import csv
import random
from datetime import datetime, timedelta

def simulate_rpm_hex(pto_engaged):
    """Generate RPM hex data based on PTO state."""
    if pto_engaged:
        rpm = random.randint(900, 1300)  # Lower RPM when PTO is active
    else:
        rpm = random.randint(1200, 2500)  # Normal operation range
    scaled = int(rpm * 4)  # Match the hex_to_rpm scaling (÷4)
    return f"{scaled:04X}" + "0000"  # Pad to 8 chars

def simulate_pto_hex(cycle_step):
    """Simulate PTO engagement pattern every 20 seconds."""
    engaged = 10 <= cycle_step % 20 <= 14
    prefix = "01" if engaged else "00"
    return prefix + ''.join(random.choices('0123456789ABCDEF', k=6)), engaged

def simulate_generic_hex():
    """Random generic 8-character hex string."""
    return ''.join(random.choices('0123456789ABCDEF', k=8))

def generate_data(file="data/telemetry.csv", rows=1000):
    can_ids = ['0x0CF00400', '0x18FEF100', '0x0CFE6CEE']
    timestamp = datetime.utcnow()

    with open(file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'can_id', 'data'])

        for i in range(rows):
            ts = timestamp.isoformat() + 'Z'
            
            # Simulate PTO data first so we can correlate RPM
            pto_data, pto_engaged = simulate_pto_hex(i)
            writer.writerow([ts, '0x18FEF100', pto_data])

            # Simulate RPM with PTO-aware logic
            rpm_data = simulate_rpm_hex(pto_engaged)
            writer.writerow([ts, '0x0CF00400', rpm_data])

            # Simulate generic error/fault code data
            generic_data = simulate_generic_hex()
            writer.writerow([ts, '0x0CFE6CEE', generic_data])

            timestamp += timedelta(seconds=1)

if __name__ == "__main__":
    generate_data()
