import sqlite3
import random
import time
from datetime import datetime, timezone

from simulate import RPMGenerator, PTOStateMachine, FaultGenerator
from constants import CAN_ID_RPM, CAN_ID_PTO, CAN_ID_FAULT, DB_PATH


# Ensure the database and telemetry table exist (main.py not used with this loop simulator)
def ensure_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path) # Connect to SQLite database
    cur = conn.cursor() # Create a cursor object to execute SQL commands
    cur.execute('''
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            can_id TEXT,
            data TEXT
        )
    ''') # Create and format table if it doesn't exist
    conn.commit()
    return conn

# Simulate a continuous loop generating telemetry data every 1s
def simulate_loop(interval=1.0):
    
    # Name assignment for each class
    pto_state = PTOStateMachine(
        initial_wait_range=(120, 150),    # 2-2.5 min before first engagement (vs. 20-30 min default)
        off_wait_range=(120, 180),      # 2-3 min between engagements (vs. 20-30 min default)
        on_wait_range=(120, 180),        # same as default: 2-3 min engaged
    )
    
    rpm_gen = RPMGenerator()

    fault_gen = FaultGenerator(
        initial_wait_range=(60, 90),      # 1-1.5 min before first fault (vs. 5-40 min default)
        active_duration_range=(5, 30),    # same as default: 5-30 sec active
        inactive_wait_range=(120, 180),   # 2-3 min between faults (vs. 10-30 min default)
    )

    conn = ensure_db()
    cur = conn.cursor()

    try:
        while True:
            ts = datetime.now(timezone.utc).isoformat() # ISO format and UTC timezone
            
            # Simulate PTO data first so RPM will correlate as intended
            pto_engaged = pto_state.next_state()
            pto_data, _ = pto_state.simulate_pto_hex()
            
            # Simulate RPM with PTO-aware logic
            rpm_data = rpm_gen.get_next(pto_engaged)
            
            # Simulate error/fault code data
            fault_data = fault_gen.maybe_emit_fault()

            # Insert data into the database
            # CAN IDs from standardized J1939 PGNs, also matching the simulate.py script
            cur.execute("INSERT INTO telemetry (timestamp, can_id, data) VALUES (?, ?, ?)",
                        (ts, CAN_ID_PTO, pto_data)) 
            cur.execute("INSERT INTO telemetry (timestamp, can_id, data) VALUES (?, ?, ?)",
                        (ts, CAN_ID_RPM, rpm_data)) 
            if fault_data:
                cur.execute("INSERT INTO telemetry (timestamp, can_id, data) VALUES (?, ?, ?)",
                            (ts, CAN_ID_FAULT, fault_data))

            conn.commit()

            # Limit to last 3600 entries (1 hour) to ensure adequate performance
            cur.execute('''
                DELETE FROM telemetry WHERE id NOT IN (
                    SELECT id FROM telemetry ORDER BY timestamp DESC LIMIT 3600
                )
            ''')

            conn.commit()
            time.sleep(interval)

    except KeyboardInterrupt:
        print("Stopped simulation.") # Exit loop message in the event of Ctrl+C
    finally:
        conn.close()

if __name__ == "__main__":
    simulate_loop()