import sqlite3
import random
import time
from datetime import datetime, timezone

# Generate realistic RPM hex data based on PTO state 
class RPMGenerator:
    def __init__(self):
        self.current_rpm = random.uniform(1000, 1300) # Initial RPM between 1000 and 1300

    def get_next(self, pto_engaged):
        # Choose target based on PTO state
        target = random.uniform(900, 1300) if pto_engaged else random.uniform(1200, 3200)
        step = random.randint(25, 60)  # How quickly RPM can change per second

        if abs(self.current_rpm - target) > step:
            self.current_rpm += step if target > self.current_rpm else -step
        else:
            self.current_rpm = target

        scaled = int(self.current_rpm * 4) # Match the hex_to_rpm scaling (÷4)
        return f"{scaled:04X}" + "0000" # 4-digit hex + 4 zeroes

# PTO state machine for realistic engagement patterns
class PTOStateMachine:
    def __init__(self):
        self.pto_on = False # Initial state
        self.timer = random.randint(120, 150)  # Start with PTO off, wait 2-2.5 minutes

    def next_state(self):
        if self.timer <= 0: # Time to change state
            self.pto_on = not self.pto_on # Toggle PTO state
            self.timer = random.randint(60, 180) if self.pto_on else random.randint(120, 180) # Reset timer
        self.timer -= 1 # Decrement timer
        return self.pto_on

    def simulate_pto_hex(self):
        prefix = "01" if self.pto_on else "00" # PTO engaged state format
        return prefix + ''.join(random.choices('0123456789ABCDEF', k=6)), self.pto_on # Pad to 8 characters

# Simulate a generic fault code in hex format
VALID_SPNS = [100, 190, 723, 84, 91, 108, 639, 110, 111]
RELEVANT_FMIS = {
    100: [0, 1, 4],
    110: [0, 1, 3],
    111: [1, 2],
    190: [0, 2],
    91:  [3, 4],
    84:  [0, 2],
    723: [2, 5],
    639: [2, 3, 4],
    108: [0, 1]}

# Simulate fault codes with SPN and FMI in hex format
class FaultGenerator:
    def __init__(self):
        self.active = False
        self.timer = random.randint(60, 90)  # Initial fault timer (1-1.5 minutes)

    def simulate_fault_hex(self):
        spn = random.choice(VALID_SPNS)  # SPN (Suspect Parameter Number)
        fmi = random.choice(RELEVANT_FMIS[spn])    # FMI (Failure Mode Identifier)
        return f"{spn:04X}{fmi:02X}00"   # SPN(4 hex) + FMI(2 hex) + pad to 8 characters

    def maybe_emit_fault(self):
        if self.timer <= 0:
            if not self.active:
                self.active = True
                self.timer = random.randint(5, 30)  # Emit fault for 5-30 seconds
            else:
                self.active = False
                self.timer = random.randint(120, 180)  # Reset timer for next fault in 2-3 minutes
        else:
            self.timer -= 1 # Decrement timer

        if self.active:
            return self.simulate_fault_hex() # Emit fault code
        return None

# Ensure the database and telemetry table exist
def ensure_db(db_path="db/telemetry.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            can_id TEXT,
            data TEXT
        )
    ''')
    conn.commit()
    return conn

# Simulate a continuous loop generating telemetry data
def simulate_loop(interval=1.0):
    rpm_gen = RPMGenerator()
    pto_state = PTOStateMachine()
    fault_gen = FaultGenerator()
    conn = ensure_db()
    cur = conn.cursor()

    try:
        while True:
            ts = datetime.now(timezone.utc).isoformat() # ISO format and UTC timezone
            # Simulate PTO data first so RPM will correlate
            pto_engaged = pto_state.next_state()
            pto_data, _ = pto_state.simulate_pto_hex()
            
            # Simulate RPM with PTO-aware logic
            rpm_data = rpm_gen.get_next(pto_engaged)
            
            # Simulate generic error/fault code data
            fault_data = fault_gen.maybe_emit_fault()

            # Insert data into the database
            cur.execute("INSERT INTO telemetry (timestamp, can_id, data) VALUES (?, ?, ?)",
                        (ts, '0x18FEF100', pto_data))
            cur.execute("INSERT INTO telemetry (timestamp, can_id, data) VALUES (?, ?, ?)",
                        (ts, '0x0CF00400', rpm_data))
            if fault_data:
                cur.execute("INSERT INTO telemetry (timestamp, can_id, data) VALUES (?, ?, ?)",
                            (ts, '0x0CFE6CEE', fault_data))

            conn.commit()

            # Limit to last 3600 entries (1 hour) for performance
            cur.execute('''
                DELETE FROM telemetry WHERE id NOT IN (
                    SELECT id FROM telemetry ORDER BY timestamp DESC LIMIT 3600
                )
            ''')

            conn.commit()
            time.sleep(interval)

    except KeyboardInterrupt:
        print("Stopped simulation.")
    finally:
        conn.close()


if __name__ == "__main__":
    simulate_loop()