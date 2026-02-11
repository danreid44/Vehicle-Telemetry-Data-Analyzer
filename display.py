import matplotlib.pyplot as plt
import os
from analyze import get_rpm_data # Import rpm function from analyze.py
from analyze import get_pto_data # Import pto function from analyze.py

# Ensure the display folder exists
def ensure_display_folder():
    os.makedirs("display", exist_ok=True)

# Plot RPM data
def plot_rpm():
    ensure_display_folder()
    df = get_rpm_data('db/telemetry.db')
    plt.plot(df['timestamp'], df['rpm'])
    plt.xlabel('Timestamp')
    plt.ylabel('RPM')
    plt.title('Engine RPM Over Time')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("display/rpm_plot.png")
    plt.show()

# Plot PTO data
def plot_pto():
    ensure_display_folder()
    df = get_pto_data('db/telemetry.db')
    plt.figure()
    plt.plot(df['timestamp'], df['pto_on'].astype(int), label="PTO")
    plt.xlabel('Timestamp')
    plt.ylabel('PTO Activation (1 = ON, 0 = OFF)')
    plt.title('Engine PTO Activation Over Time')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("display/pto_plot.png")
    plt.show()

if __name__ == "__main__":
    plot_rpm()
    plot_pto()
