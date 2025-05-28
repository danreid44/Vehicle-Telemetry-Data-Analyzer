import sqlite3
import csv

# Function to load telemetry data from CSV to SQLite database
def load_to_db(csv_file, db_file):
    conn = sqlite3.connect(db_file) # Connect to SQLite database
    cur = conn.cursor() # Create a cursor object to execute SQL commands

    cur.execute('''
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            can_id TEXT,
            data TEXT
        )
    ''') # Create and format table if it doesn't exist

    with open(csv_file, newline='') as f: # Open CSV file
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute("INSERT INTO telemetry (timestamp, can_id, data) VALUES (?, ?, ?)",
                        (row['timestamp'], row['can_id'], row['data'])) # Insert data into table

    conn.commit()
    conn.close() # Commit changes and close connection

if __name__ == "__main__":
    load_to_db('data/telemetry.csv', 'db/telemetry.db') 
