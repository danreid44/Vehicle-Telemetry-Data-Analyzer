import sqlite3
import random
import time
import argparse
from datetime import datetime, timezone

# Generate realistic RPM hex data based on PTO state 
class RPMGenerator:
    def __init__(self):
        self.current_rpm = random.uniform(1000, 1300) # Initial RPM between 1000 and 1300

    def get_next(self, pto_engaged, elapsed):
        # Choose target based on PTO state
        target = random.uniform(900, 1300) if pto_engaged else random.uniform(1200, 2500)
        step = 50  # How quickly RPM can change per second

        # Smooth toward target
        if abs(self.current_rpm - target) > step:
            self.current_rpm += step if target > self.current_rpm else -step
        else:
            self.current_rpm = target # Snap to target if within step

        scaled = int(self.current_rpm * 4) # Match the hex_to_rpm scaling (÷4)
        return f"{scaled:04X}" + "0000" # 4-digit hex + 4 zeroes


# PTO state machine for realistic engagement patterns
class PTOStateMachine:
    def __init__(self):
        self.pto_on = False # Initial state
        self.timer = random.uniform(120, 180) # Start with PTO off, wait 2-3 minutes as float
        self.cached_hex = self._generate_hex()

    def _generate_hex(self):
        prefix = "01" if self.pto_on else "00"
        return prefix + ''.join(random.choices('0123456789ABCDEF', k=6))

    def next_state(self, elapsed):
        self.timer -= elapsed # Decrement timer based on elapsed time
        if self.timer <= 0: # Time to change state
            self.pto_on = not self.pto_on   # Toggle PTO state
            self.timer = random.uniform(60, 180) if self.pto_on else random.uniform(300, 420) # Reset timer to 1-3 minutes if PTO on, 5-7 minutes if PTO off
            self.cached_hex = self._generate_hex()  # Only update when state toggles
        return self.pto_on

    def simulate_pto_hex(self):
        return self.cached_hex, self.pto_on

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
        self.timer = random.uniform(60, 90) # Initial fault timer (1-1.5 minutes) as float
        self.emitted_this_cycle = False

    def simulate_fault_hex(self):
        spn = random.choice(VALID_SPNS) # SPN (Suspect Parameter Number)
        fmi = random.choice(RELEVANT_FMIS[spn]) # FMI (Failure Mode Identifier)
        return f"{spn:04X}{fmi:02X}00" # SPN(4 hex) + FMI(2 hex) + pad to 8 characters

    def maybe_emit_fault(self, elapsed):
        self.timer -= elapsed
        if self.timer <= 0:
            if not self.active:
                self.active = True
                self.timer = random.uniform(5, 30) # Active for 5-30 seconds
                self.emitted_this_cycle = False
            else:
                self.active = False
                self.timer = random.uniform(300, 420) # Reset timer for next fault (5-7 minutes)
        if self.active and not self.emitted_this_cycle:
            self.emitted_this_cycle = True
            return self.simulate_fault_hex()
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
        prev_time = time.time()
        while True:
            now = time.time()
            elapsed = now - prev_time
            prev_time = now

            ts = datetime.now(timezone.utc).isoformat()

            pto_engaged = pto_state.next_state(elapsed) # Get current PTO state
            pto_data, _ = pto_state.simulate_pto_hex() # Get PTO hex data and state
            rpm_data = rpm_gen.get_next(pto_engaged, elapsed) # Get next RPM data based on PTO state
            fault_data = fault_gen.maybe_emit_fault(elapsed) # Check for fault codes

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
    # Add argument for interval between data points
    parser.add_argument("-interval", type=float, default=1.0, help="Interval between data points in seconds (e.g. 0.1 for 10Hz)")
    args = parser.parse_args()

    simulate_loop(interval=args.interval) # Run the simulation loop with specified interval
