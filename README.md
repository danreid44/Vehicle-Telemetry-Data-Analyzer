# Vehicle Telemetry Data Analyzer

This is a Python-based tool for simulating, storing, analyzing, and displaying vehicle telemetry data such as engine RPM, PTO activity, and fault codes. This is designed to replicate the primary functions of commerical fleet diagnostics platforms commonly used in the industry.

# Key Features
- Simulated CAN/J1939 messages
- SQLite data storage
- Data trend analysis with Pandas
- Data displayed using Matplotlib and Streamlit


# How to Run the Project:

# 1. Clone the Repo
git clone https://github.com/yourusername/vehicle-telemetry-analyzer.git
cd vehicle-telemetry-analyzer

# 2. Create & Activate Virtual Environment
python3 -m venv venv
source venv/bin/activate # On Windows: .\venv\Scripts\activate

# 3. Install Required Packages
pip install -r requirements.txt

# 4. Generate Simulated Telemetry Data
python simulate_data.py

# 5. Load Data into SQLite Database
python main.py

# 6. Display Engine RPM Over Time
python display.py

# 7. Run the Dashboard
streamlit run dashboard.py
