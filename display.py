import matplotlib.pyplot as plt
from analyze import get_rpm_data # Import function from analyze.py

# Function to plot RPM data
def plot_rpm():
    df = get_rpm_data('db/telemetry.db')
    plt.plot(df['timestamp'], df['rpm'])
    plt.xlabel('Timestamp')
    plt.ylabel('RPM')
    plt.title('Engine RPM Over Time')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("display/rpm_plot.png")
    plt.show()

if __name__ == "__main__":
    plot_rpm()
