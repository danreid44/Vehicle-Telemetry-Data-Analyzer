# Vehicle Telemetry Data Analyzer

This is a Python-based tool for simulating, storing, analyzing, and displaying vehicle telemetry data such as engine RPM, PTO activity, and fault codes. This is designed to replicate the primary functions of commerical fleet diagnostics platforms commonly used in the industry. A postman collection is provided to perform CRUD operations on the SQLite database.

## Key Features ##
- Simulated CAN/J1939 messages
- SQLite data storage
- Data trend analysis with Pandas
- Data displayed using Streamlit and Matplotlib
- Backend API routes to perform CRUD operations


# How to Run the Project:

## 1. Clone the Repo ##
```bash
git clone https://github.com/yourusername/vehicle-telemetry-analyzer.git
cd vehicle-telemetry-analyzer
```

## 2. Create & Activate Virtual Environment ##
```bash
python3 -m venv venv
source venv/bin/activate # On Windows: .\venv\Scripts\activate
```

## 3. Simulate, Store, and Display Data ##
```bash
pip install -r requirements.txt # Install required packages

python simulate.py # Generate Simulated Telemetry Data

python main.py # Load Data into SQLite Database

python display.py # Display Engine RPM Over Time

streamlit run dashboard.py # Run the Dashboard

python api.py # Launch API routes and Flask app on http://127.0.0.1:5000
```


## API Endpoints ##

| Method        | Route                | Description             |
| ------------- | -------------------- | ----------------------- |
| GET           | '/api/rpm'           | Get RPM telemetry data  |
| GET           | '/api/pto'           | Get PTO telemetry data  |
| POST          | '/api/telemetry'     | Add new telemetry data  |
| PATCH         | '/api/telemetry/:id' | Patch telemetry data    |
| DELETE        | '/api/telemetry/:id' | Delete telemetry data   |
