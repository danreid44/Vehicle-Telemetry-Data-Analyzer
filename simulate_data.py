# This script generates a CSV file with simulated telemetry data.
# The data includes timestamps, CAN IDs, and random data strings.

import csv
import random # for random data generation
from datetime import datetime, timedelta # for timestamp generation

# Function to generate random telemetry data
def generate_data(file="data/telemetry.csv", rows=1000): # Default to 1000 rows
    can_ids = ['0x0CF00400', '0x18FEF100', '0x0CFE6CEE']  # RPM, PTO, error code
    timestamp = datetime.utcnow()

    with open(file, 'w', newline='') as f:
        writer = csv.writer(f) # Open file in write mode
        writer.writerow(['timestamp', 'can_id', 'data']) # Write header row
        for _ in range(rows): # Loop to generate specified number of rows
            ts = timestamp.isoformat() + 'Z'
            can_id = random.choice(can_ids) # Randomly select a CAN ID
            data = ''.join(random.choices('0123456789ABCDEF', k=8)) # Random hex string of length 8
            writer.writerow([ts, can_id, data]) # Write row to CSV
            timestamp += timedelta(seconds=1) # Increment timestamp by 1 second

if __name__ == "__main__":
    generate_data()
    # Call the function to generate data