import csv
import random
from datetime import datetime, timezone, timedelta

# Generate realistic RPM hex data based on PTO state 
class RPMGenerator:
    def __init__(self):
        self.current_rpm = random.randint(1000, 1300) # Initial RPM between 1000 and 1300

    def get_next(self, pto_engaged):
        # Choose target based on PTO state
        target = random.randint(900, 1300) if pto_engaged else random.randint(1200, 2500)
        step = 50  # How quickly RPM can change per second

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
        self.timer = random.randint(1200, 1800)  # Start with PTO off, wait 20-30 minutes

    def next_state(self):
        if self.timer <= 0: # Time to change state
            self.pto_on = not self.pto_on # Toggle PTO state
            self.timer = random.randint(60, 180) if self.pto_on else random.randint(1200, 1800) # Reset timer
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


class FaultGenerator:
    def simulate_fault_hex(self):
        spn = random.choice(VALID_SPNS)  # SPN (Suspect Parameter Number)
        fmi = random.choice(RELEVANT_FMIS[spn])    # FMI (Failure Mode Identifier)
        return f"{spn:04X}{fmi:02X}00"   # SPN(4 hex) + FMI(2 hex) + pad to 8 characters
    
    def __init__(self):
        self.active = False
        self.timer = random.randint(300, 2400)  # Initial fault timer (5-40 minutes)

    def maybe_emit_fault(self):
        if self.timer <= 0:
            if not self.active:
                self.active = True
                self.timer = random.randint(5, 30)  # Emit fault for 5-30 seconds
            else:
                self.active = False
                self.timer = random.randint(600, 1800)  # Reset timer for next fault in 10-30 minutes
        else:
            self.timer -= 1

        if self.active:
            return self.simulate_fault_hex()
        return None

# Generate 3600 rows of telemetry data, equivalent to 1 hour
def generate_data(file="data/telemetry.csv", rows=3600):
    can_ids = ['0x0CF00400', '0x18FEF100', '0x0CFE6CEE'] # Example CAN IDs
    timestamp = datetime.now(timezone.utc) # Start from current UTC time with explicit timezone awareness
    pto_state = PTOStateMachine()
    rpm_gen = RPMGenerator()
    fault_gen = FaultGenerator()

    with open(file, 'w', newline='') as f:
        writer = csv.writer(f) # Open file in write mode
        writer.writerow(['timestamp', 'can_id', 'data']) # Header row

        for i in range(rows):
            ts = timestamp.isoformat() # ISO format and UTC timezone
            
            # Simulate PTO data first so RPM will correlate 
            pto_engaged = pto_state.next_state()
            pto_data, _ = pto_state.simulate_pto_hex()
            writer.writerow([ts, '0x18FEF100', pto_data])

            # Simulate RPM with PTO-aware logic
            rpm_data = rpm_gen.get_next(pto_engaged)
            writer.writerow([ts, '0x0CF00400', rpm_data])

            # Simulate generic error/fault code data
            fault_data = fault_gen.maybe_emit_fault()
            if fault_data:
                writer.writerow([ts, '0x0CFE6CEE', fault_data])

            timestamp += timedelta(seconds=1) # Increment timestamp by 1 second

if __name__ == "__main__":
    generate_data()
