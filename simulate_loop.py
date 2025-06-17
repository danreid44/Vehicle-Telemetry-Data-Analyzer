import sqlite3
import random
import time
import argparse
from datetime import datetime, timezone

# Generate realistic RPM hex data based on PTO state 
class RPMGenerator:
    def __init__(self):
        self.current_rpm = random.randint(1000, 1300) # Initial RPM between 1000 and 1300

    def get_next(self, pto_engaged):
        # Choose target based on PTO state
        target = random.randint(900, 1300) if pto_engaged else random.randint(1200, 2500)
        step = 50   # How quickly RPM can change per second

        # Smooth toward target
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
        self.timer = random.randint(300, 480) # Start with PTO off, wait 5-8 minutes
        self.last_update = time.time()

    def next_state(self):
        now = time.time()
        elapsed = now - self.last_update # Calculate elapsed time since last update
        self.last_update = now # Update last update time

        self.timer -= elapsed # Decrement timer based on elapsed time

        if self.timer <= 0: # Time to change state
            self.pto_on = not self.pto_on   # Toggle PTO state
            self.timer = random.randint(60, 180) if self.pto_on else random.randint(600, 1200) # Reset timer
        return self.pto_on

    def simulate_pto_hex(self):
        prefix = "01" if self.pto_on else "00"
        return prefix + ''.join(random.choices('0123456789ABCDEF', k=6)), self.pto_on

# Simulate a generic fault code in hex format
VALID_SPNS = [100, 190, 723, 84, 91, 108, 639, 110, 111]
RELEVANT_FMIS = {
    100: [0, 1, 4], 110: [0, 1, 3], 111: [1, 2], 190: [0, 2],
    91: [3, 4], 84: [0, 2], 723: [2, 5], 639: [2, 3, 4], 108: [0, 1]
}

# Simulate fault codes with SPN and FMI in hex format
class FaultGenerator:
    def __init__(self):
        self.active = False
        self.timer = random.randint(120, 240) # Initial fault timer (2-4 minutes)
        self.last_update = time.time()

    def simulate_fault_hex(self):
        spn = random.choice(VALID_SPNS) # SPN (Suspect Parameter Number)
        fmi = random.choice(RELEVANT_FMIS[spn]) # FMI (Failure Mode Identifier)
        return f"{spn:04X}{fmi:02X}00" # SPN(4 hex) + FMI(2 hex) + pad to 8 characters

    def maybe_emit_fault(self):
        now = time.time()
        elapsed = now - self.last_update # Calculate elapsed time since last update
        self.last_update = now # Update last update time

        if self.timer <= 0:
            if not self.active:
                self.active = True
                self.timer = random.randint(5, 30) # Active for 5-30 seconds
            else:
                self.active = False
                self.timer = random.randint(300, 420) # Reset timer for next fault (5-7 minutes)
        else:
            self.timer -= elapsed # Decrement timer based on elapsed time

        if self.active:
            return self.simulate_fault_hex() # Emit fault code
        return None

# Database setup function
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

# Simulate loop to generate and insert telemetry data
def simulate_loop(interval=1.0):
    rpm_gen = RPMGenerator()
    pto_state = PTOStateMachine()
    fault_gen = FaultGenerator()
    conn = ensure_db()
    cur = conn.cursor()

    try:
        while True:
            ts = datetime.now(timezone.utc).isoformat()

            pto_engaged = pto_state.next_state()
            pto_data, _ = pto_state.simulate_pto_hex()
            rpm_data = rpm_gen.get_next(pto_engaged)
            fault_data = fault_gen.maybe_emit_fault()

            cur.execute("INSERT INTO telemetry (timestamp, can_id, data) VALUES (?, ?, ?)",
                        (ts, '0x18FEF100', pto_data))
            cur.execute("INSERT INTO telemetry (timestamp, can_id, data) VALUES (?, ?, ?)",
                        (ts, '0x0CF00400', rpm_data))
            if fault_data:
                cur.execute("INSERT INTO telemetry (timestamp, can_id, data) VALUES (?, ?, ?)",
                            (ts, '0x0CFE6CEE', fault_data))

            conn.commit()
            time.sleep(interval) # Wait for the specified interval

    except KeyboardInterrupt:
        print("Stopped simulation.")
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-interval", type=float, default=1.0, help="Interval between data points in seconds (e.g. 0.1 for 10Hz)")
    args = parser.parse_args()

    simulate_loop(interval=args.interval)
