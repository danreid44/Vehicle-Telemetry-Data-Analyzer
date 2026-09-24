import csv
import random
from datetime import datetime, timezone, timedelta
from constants import CAN_ID_RPM, CAN_ID_PTO, CAN_ID_FAULT, CSV_PATH

# Generate realistic RPM hex data based on PTO state 
class RPMGenerator:
    def __init__(self):
        self.current_rpm = random.randint(1000, 1300) # Initial RPM between 1000 and 1300 for realistic cold start

    def get_next(self, pto_engaged):
        # Choose target based on PTO state
        target = random.randint(900, 1300) if pto_engaged else random.randint(1200, 3200) # Adjust RPM range based on PTO state
        step = random.randint(25, 60)  # How quickly RPM can change per second

        # Smooth RPM change towards target range
        if abs(self.current_rpm - target) > step:
            self.current_rpm += step if target > self.current_rpm else -step
        else:
            self.current_rpm = target

        scaled = int(self.current_rpm * 8) # Match the hex_to_rpm scaling (÷8)
        return f"{scaled:04X}" + "0000" # 4-digit hex + 4 zeroes 

# PTO state machine for realistic engagement patterns
# Timer windows are parameterized (in seconds) so callers like simulate_loop.py
# can shorten them for a faster live demo without duplicating this class.
class PTOStateMachine:
    def __init__(self, initial_wait_range=(1200, 1800), off_wait_range=(1200, 1800), on_wait_range=(60, 180)):
        self.timer = random.randint(*initial_wait_range) # Wait before the first state change
        self.off_wait_range = off_wait_range  # Start with PTO off, wait specified time before first engaging
        self.on_wait_range = on_wait_range  # Keep PTO engaged for the specified time
        
    def next_state(self):
        if self.timer <= 0: # Time to change state
            self.pto_on = not self.pto_on # Toggle PTO state
            self.timer = random.randint(*self.on_wait_range) if self.pto_on else random.randint(*self.off_wait_range) # Reset timer
        self.timer -= 1 # Decrement timer
        return self.pto_on

    def simulate_pto_hex(self):
        prefix = "01" if self.pto_on else "00" # PTO engaged vs. not engaged format
        return prefix + ''.join(random.choices('0123456789ABCDEF', k=6)), self.pto_on # Pad to 8 chars

# Simulate a generic fault code in hex format based on SAE J1939 specification
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
# Timer windows are parameterized (in seconds) so callers like simulate_loop.py
# can shorten them for a faster live demo without duplicating this class.
class FaultGenerator:
    def __init__(self, initial_wait_range=(300, 2400), active_duration_range=(5, 30), inactive_wait_range=(600, 1800)):
        self.active = False
        self.timer = random.randint(*initial_wait_range) # Initial fault timer
        self.active_duration_range = active_duration_range # How long an emitted fault stays active
        self.inactive_wait_range = inactive_wait_range # How long to wait before the next fault


    def simulate_fault_hex(self):
        spn = random.choice(VALID_SPNS)  # SPN (Suspect Parameter Number)
        fmi = random.choice(RELEVANT_FMIS[spn])    # FMI (Failure Mode Identifier)
        return f"{spn:04X}{fmi:02X}00"   # SPN(4 hex) + FMI(2 hex) + pad to 8 chars

    def maybe_emit_fault(self):
        if self.timer <= 0:
            if not self.active:
                self.active = True
                self.timer = random.randint(*self.active_duration_range)  # Emit fault for specified time period
            else:
                self.active = False
                self.timer =  random.randint(*self.inactive_wait_range)   # Reset timer for next fault
        else:
            self.timer -= 1 # Decrement timer

        if self.active:
            return self.simulate_fault_hex() # Emit fault code
        return None

# Generate 3600 rows (equivalent 1 hour) of telemetry data
def generate_data(file=CSV_PATH, rows=3600):
    timestamp = datetime.now(timezone.utc) # Start from current UTC time
    
    # Name assignment for each class
    pto_state = PTOStateMachine()
    rpm_gen = RPMGenerator()
    fault_gen = FaultGenerator()

    with open(file, 'w', newline='') as f:
        writer = csv.writer(f) # Open file in write mode
        writer.writerow(['timestamp', 'can_id', 'data']) # Header row

        for i in range(rows):
            ts = timestamp.isoformat() # ISO format and UTC timezone
            
            # Simulate PTO data first so RPM will correlate as intended
            pto_engaged = pto_state.next_state()
            pto_data, _ = pto_state.simulate_pto_hex()
            writer.writerow([ts, CAN_ID_PTO, pto_data])

            # Simulate RPM with PTO-aware logic
            rpm_data = rpm_gen.get_next(pto_engaged)
            writer.writerow([ts, CAN_ID_RPM, rpm_data])

            # Simulate error/fault code data
            fault_data = fault_gen.maybe_emit_fault()
            if fault_data:
                writer.writerow([ts, CAN_ID_FAULT, fault_data])

            timestamp += timedelta(seconds=1) # Increment timestamp by 1 second

if __name__ == "__main__":
    generate_data()
