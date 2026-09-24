from flask import Flask, request, jsonify
import sqlite3
import pandas as pd
from datetime import datetime

from analyze import decode_fault, hex_to_rpm, is_pto_on
from constants import CAN_ID_RPM, CAN_ID_PTO, CAN_ID_FAULT, DB_PATH

app = Flask(__name__) # Flask app instance

# Root API route
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Vehicle Telemetry Data Analyzer API",
        "endpoints": {
            "GET /api/rpm": "Get RPM telemetry data",
            "GET /api/pto": "Get PTO telemetry data",
            "GET /api/faults": "Get fault data",
            "POST /api/telemetry": "Add new telemetry data",
            "PATCH /api/telemetry/<id>": "Update telemetry data",
            "DELETE /api/telemetry/<id>": "Delete telemetry data"
        }
    }), 200

# Database connection function
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Route to get RPM telemetry data
@app.route("/api/rpm", methods=["GET"])
def get_rpm_data():
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT id, timestamp, data FROM telemetry WHERE can_id='{CAN_ID_RPM}'", conn) # Fetch RPM data based on CAN ID
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['rpm'] = df['data'].apply(hex_to_rpm) # Convert hex data to RPM, hex_to_rpm imported from analyze.py
    return jsonify(df.to_dict(orient="records"))

# Route to get PTO telemetry data
@app.route("/api/pto", methods=["GET"])
def get_pto_data():
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT id, timestamp, data FROM telemetry WHERE can_id='{CAN_ID_PTO}'", conn) # Fetch PTO data based on CAN ID
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['pto_on'] = df['data'].apply(is_pto_on) # Convert hex data to PTO status, is_pto_on imported from analyze.py
    return jsonify(df.to_dict(orient="records"))

# Route to get fault telemetry data
@app.route("/api/faults", methods=["GET"])
def get_fault_data():

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(f"SELECT timestamp, data FROM telemetry WHERE can_id='{CAN_ID_FAULT}'", conn) # Fetch fault data based on CAN ID
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df[['spn', 'fmi']] = df['data'].apply(lambda d: pd.Series(decode_fault(d))) # decode_fault imported from analyze.py
    df = df.dropna()
    return jsonify(df[['timestamp', 'spn', 'fmi']].to_dict(orient="records"))

# Route to post new telemetry data
@app.route("/api/telemetry", methods=["POST"])
def add_telemetry():
    data = request.get_json() # Require timestamp, CAN ID, and 32 bit hex data to post new record
    timestamp = data.get("timestamp", datetime.now().isoformat() + "Z")
    can_id = data.get("can_id")
    hex_data = data.get("data")

    if not all([timestamp, can_id, hex_data]):
        return jsonify({"error": "timestamp, can_id, and data are required"}), 400 # Error return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO telemetry (timestamp, can_id, data) VALUES (?, ?, ?)",
        (timestamp, can_id, hex_data) # Insert telemetry data into the database
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({"message": "Telemetry record added", "id": new_id}), 201

# Route to patch telemetry data
@app.route("/api/telemetry/<int:record_id>", methods=["PATCH"])
def update_telemetry(record_id):
    data = request.get_json()
    fields = []
    values = []

    # Append data in desired field
    for field in ["timestamp", "can_id", "data"]:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])

    if not fields:
        return jsonify({"error": "No valid fields to update"}), 400 # Error return

    values.append(record_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE telemetry SET {', '.join(fields)} WHERE id = ?", values) # Update telemetry data in the database
    conn.commit()
    conn.close()
    
    return jsonify({"message": f"Telemetry record {record_id} updated"}), 200


# Route to delete telemetry data
@app.route("/api/telemetry/<int:record_id>", methods=["DELETE"])
def delete_telemetry(record_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM telemetry WHERE id = ?", (record_id,)) # Delete telemetry data from the database
    conn.commit()
    conn.close()

    return jsonify({"message": f"Telemetry record {record_id} deleted"}), 200

if __name__ == "__main__":
    app.run(debug=True)
