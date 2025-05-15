import sqlite3 # Import SQLite library
import pandas as pd # Import Pandas library

# Function to fetch RPM data from SQLite database
# Assume: first 4 hex chars as RPM
def fetch_rpm_data(db_file): 
    def hex_to_rpm(data):
        return int(data[:4], 16) / 4  # Simulated formula

    conn = sqlite3.connect(db_file) # Connect to SQLite database
    df = pd.read_sql_query("SELECT timestamp, data FROM telemetry WHERE can_id='0x0CF00400'", conn) # Fetch data from telemetry table
    conn.close() # Close connection

    df['timestamp'] = pd.to_datetime(df['timestamp']) # Convert timestamp to datetime
    df['rpm'] = df['data'].apply(hex_to_rpm) # Convert hex data to RPM

    return df # Return DataFrame with timestamp and RPM data

# Function to fetch PTO data from SQLite database
# Assume: first byte represents PTO status: 00 = Off, 01 = On
def fetch_pto_events(db_file):
    def is_pto_on(data):
        return data[:2] == "01"  # check if first byte == 0x01

    conn = sqlite3.connect(db_file) # Connect to SQLite database
    df = pd.read_sql_query("SELECT timestamp, data FROM telemetry WHERE can_id='0x18FEF100'", conn) # Fetch PTO data
    conn.close()

    df['timestamp'] = pd.to_datetime(df['timestamp']) # Convert timestamp to datetime
    df['pto_on'] = df['data'].apply(is_pto_on) # Convert hex data to PTO status
    return df