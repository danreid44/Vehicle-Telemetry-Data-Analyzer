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


# Function to get fault codes from SQLite database
# Assume: first 4 hex chars as SPN, next 2 hex chars as FMI
def get_fault_data(db_file, decoder_path="data/spn_fmi_decoder.csv"):
    def decode_fault(hex_str):
        try:
            spn = int(hex_str[:4], 16) # Convert first 4 hex chars to SPN
            fmi = int(hex_str[4:6], 16) # Convert next 2 hex chars to FMI
            return spn, fmi
        except:
            return None, None

    conn = sqlite3.connect(db_file)
    df = pd.read_sql_query("SELECT timestamp, data FROM telemetry WHERE can_id='0x0CFE6CEE'", conn) # Fetch fault data
    conn.close()

    df['timestamp'] = pd.to_datetime(df['timestamp']) # Convert timestamp to datetime
    df[['spn', 'fmi']] = df['data'].apply(lambda d: pd.Series(decode_fault(d))) # Split data into SPN and FMI columns
    df.dropna(inplace=True)

     # Load decoder CSV
    decoder = pd.read_csv(decoder_path)
    df = df.merge(decoder, on=["spn", "fmi"], how="left")
    df['description'] = df['description'].fillna("Unknown SPN/FMI")

    return df