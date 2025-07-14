import sqlite3 
import pandas as pd

# Function to fetch RPM data from SQLite database
# Assume: first 4 hex chars as RPM
def get_rpm_data(db_file): 
    def hex_to_rpm(data):
        return int(data[:4], 16) / 4  # Simulated formula

    conn = sqlite3.connect(db_file) # Connect to SQLite database
    df = pd.read_sql_query("SELECT timestamp, data FROM telemetry WHERE can_id='0x0CF00400'", conn) # Fetch data from telemetry table
    conn.close() # Close connection

    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, format='mixed') # Convert timestamp to datetime
    df['rpm'] = df['data'].apply(hex_to_rpm) # Convert hex data to RPM
    return df
# Function to calculate RPM statistics from the fetched data
def get_rpm_stats(db_file):
    df = get_rpm_data(db_file)
    return {
        "min_rpm": round(df['rpm'].min(), 2),
        "max_rpm": round(df['rpm'].max(), 2),
        "avg_rpm": round(df['rpm'].mean(), 2),
    }


# Function to fetch PTO data from SQLite database
# Assume: first byte represents PTO status: 00 = Off, 01 = On
def get_pto_data(db_file):
    def is_pto_on(data):
        return data[:2] == "01"  # check if first byte == 0x01

    conn = sqlite3.connect(db_file) # Connect to SQLite database
    df = pd.read_sql_query("SELECT timestamp, data FROM telemetry WHERE can_id='0x18FEF100'", conn) # Fetch PTO data
    conn.close()

    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, format='mixed') # Convert timestamp to datetime
    df['pto_on'] = df['data'].apply(is_pto_on) # Convert hex data to PTO status
    return df
# Function to calculate PTO statistics from the fetched data
def get_pto_stats(db_file):
    df = get_pto_data(db_file)
    # Calculate PTO usage frequency
    df['engaged_shift'] = df['pto_on'].shift(1, fill_value=False)
    df['transition'] = df['pto_on'] & (~df['engaged_shift'])
    usage_count = df['transition'].sum()

    # Calculate total engaged time (1 entry per second)
    engaged_duration_sec = df['pto_on'].sum()

    return {
        "pto_usage_count": int(usage_count),
        "pto_duration_sec": int(engaged_duration_sec),
        "pto_duration_min": round(engaged_duration_sec / 60, 2)
    }

# Function to decode fault codes from hex string
# Assume: first 4 hex chars as SPN, next 2 hex chars as FMI
def decode_fault(hex_str):
        try:
            if not isinstance(hex_str, str) or len(hex_str) < 6: # Validate input
                return None, None
            spn = int(hex_str[:4], 16) # Convert first 4 hex chars to SPN
            fmi = int(hex_str[4:6], 16) # Convert next 2 hex chars to FMI
            return spn, fmi
        except:
            return None, None

# Function to classify severity based on FMI
def classify_severity(fmi):
        if fmi in [0, 1]:
            return "Critical"
        elif fmi in [2, 3, 4]:
            return "Warning"
        else:
            return "Info"
        

# Function to get fault codes from SQLite database
def get_fault_data(db_file, decoder_path="data/spn_fmi_decoder.csv"):
    conn = sqlite3.connect(db_file)
    df = pd.read_sql_query("SELECT timestamp, data FROM telemetry WHERE can_id='0x0CFE6CEE'", conn) # Fetch fault data
    conn.close()

    df['timestamp'] = pd.to_datetime(df['timestamp']) # Convert timestamp to datetime

    if df.empty or 'data' not in df.columns:
        return pd.DataFrame(columns=["timestamp", "spn", "fmi", "description", "severity"])

    # Filter out invalid data
    df = df[df['data'].apply(lambda x: isinstance(x, str) and len(x) >= 6)] 

    # Split data into SPN and FMI columns
    df[['spn', 'fmi']] = df['data'].apply(lambda d: pd.Series(decode_fault(d))) 
    df.dropna(subset=['spn', 'fmi'], inplace=True)

    # Load decoder CSV
    decoder = pd.read_csv(decoder_path)
    df = df.merge(decoder, on=["spn", "fmi"], how="left")
    df['description'] = df['description'].fillna("Unknown SPN/FMI")
    df['severity'] = df['fmi'].apply(classify_severity)
    
    return df

def get_mtbf(df):
    if df.empty or 'timestamp' not in df.columns:
        return None  # No data to analyze
    
    df_sorted = df.sort_values("timestamp").reset_index(drop=True)  # Sort by timestamp
    timestamps = df_sorted['timestamp'].tolist()

    if len(timestamps) < 2:
        return None  # Not enough data

    deltas = [
        (timestamps[i] - timestamps[i-1]).total_seconds()
        for i in range(1, len(timestamps))
    ]

    mtbf = sum(deltas) / len(deltas)  # Avg seconds between faults
    return mtbf


# Function to get top N fault codes
def get_fault_frequency(df_fault, top_n=10):
    def wrap_text(text, width=30):
        # Insert line break at nearest space before width
        import textwrap
        return "\n".join(textwrap.wrap(text, width=width))

    df_fault["wrapped_description"] = df_fault["description"].apply(lambda d: wrap_text(d, width=25))

    # Group by description and severity, count occurrences, and sort
    freq = (df_fault
            .groupby(["wrapped_description", "severity"])
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
            .head(top_n)
    )
    return freq.reset_index().rename(columns={0: "count"})

# Function to calculate fault statistics from the fetched data
def get_fault_stats(df_fault):
    if df_fault.empty:
        return {
            "most_recent": None,
            "last_fault_time": None,
            "critical_count": 0,
            "severity_counts": {}
        }

    total_faults = len(df_fault)
    last_fault = df_fault.sort_values("timestamp", ascending=False).iloc[0]
    critical_count = df_fault[df_fault["severity"] == "Critical"].shape[0]
    warning_count = df_fault[df_fault["severity"] == "Warning"].shape[0]
    info_count = df_fault[df_fault["severity"] == "Info"].shape[0]
    severity_counts = df_fault["severity"].value_counts().to_dict()

    return {
        "total_faults": total_faults,
        "most_recent": last_fault,
        "last_fault_time": last_fault["timestamp"],
        "critical_count": critical_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "severity_counts": severity_counts
    }

# Function to detect RPM anomalies based on rules
def detect_rpm_anomalies(df):
    anomalies = []  # List to store detected anomalies

    for i in range(1, len(df)):
        rpm_now = df.iloc[i]['rpm']
        rpm_prev = df.iloc[i-2]['rpm']
        pto_on = df.iloc[i]['pto_on']

        # Rule: RPM > 2000 while PTO is engaged
        if pto_on and rpm_now > 2000:
            anomalies.append((df.iloc[i]['timestamp'], "High RPM during PTO"))

        # Rule: Sudden RPM jump (eg. > 110 RPM change in 2 seconds)
        if abs(rpm_now - rpm_prev) > 110:
            anomalies.append((df.iloc[i]['timestamp'], "Sudden RPM change"))

    return anomalies
