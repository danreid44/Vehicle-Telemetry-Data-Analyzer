from flask import Flask, request, jsonify
import sqlite3
import pandas as pd
from datetime import datetime

app = Flask(__name__) # Flask app instance
DB_PATH = "db/telemetry.db" # Path to SQLite database file

# Database connection function
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Route to get RPM telemetry data
@app.route("/api/rpm", methods=["GET"])
def get_rpm_data():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT id, timestamp, data FROM telemetry WHERE can_id='0x0CF00400'", conn) # Fetch RPM data
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['rpm'] = df['data'].apply(lambda d: int(d[:4], 16) / 4) # Convert hex data to RPM
    return jsonify(df.to_dict(orient="records"))

# Route to get PTO telemetry data
@app.route("/api/pto", methods=["GET"])
def get_pto_data():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT id, timestamp, data FROM telemetry WHERE can_id='0x18FEF100'", conn) # Fetch PTO data
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['pto_on'] = df['data'].apply(lambda d: d[:2] == "01") # Convert hex data to PTO status
    return jsonify(df.to_dict(orient="records"))

# Route to get fault telemetry data
@app.route("/api/faults", methods=["GET"])
def get_fault_data():
    def decode_fault(hex_str):
        try:
            spn = int(hex_str[:4], 16)
            fmi = int(hex_str[4:6], 16)
            return spn, fmi
        except:
            return None, None

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT timestamp, data FROM telemetry WHERE can_id='0x0CFE6CEE'", conn)
    conn.close()

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df[['spn', 'fmi']] = df['data'].apply(lambda d: pd.Series(decode_fault(d)))
    df = df.dropna()

    return jsonify(df[['timestamp', 'spn', 'fmi']].to_dict(orient="records"))

# Route to post new telemetry data
@app.route("/api/telemetry", methods=["POST"])
def add_telemetry():
    data = request.get_json()
    timestamp = data.get("timestamp", datetime.utcnow().isoformat() + "Z")
    can_id = data.get("can_id")
    hex_data = data.get("data")

    if not all([timestamp, can_id, hex_data]):
        return jsonify({"error": "timestamp, can_id, and data are required"}), 400

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

    for field in ["timestamp", "can_id", "data"]:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])

    if not fields:
        return jsonify({"error": "No valid fields to update"}), 400

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
