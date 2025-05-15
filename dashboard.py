import streamlit as st # Importing necessary libraries
import sqlite3
import pandas as pd
from analyze import fetch_rpm_data, fetch_pto_events # Importing functions from analyze.py

# Streamlit page settings
st.set_page_config(
    page_title="Vehicle Telemetry Dashboard",
    layout="wide"
)

st.title("Vehicle Telemetry Dashboard")
st.markdown("Analyze simulated J1939 vehicle data: engine RPM, PTO activation, and more.")

# Load data
DB_PATH = "db/telemetry.db"
df_rpm = fetch_rpm_data(DB_PATH)
df_pto = fetch_pto_events(DB_PATH)

# Tabbed layout
tab1, tab2 = st.tabs(["📈 Engine RPM", "🔧 PTO Activation"])

# Engine RPM Tab
with tab1:
    st.subheader("Engine RPM Over Time")
    st.line_chart(df_rpm.set_index("timestamp")["rpm"])
    
    with st.expander("Show Raw RPM Data"):
        st.dataframe(df_rpm)

# PTO Activation Tab
with tab2:
    st.subheader("PTO Activation Timeline")
    st.line_chart(df_pto.set_index("timestamp")["pto_on"].astype(int))
    
    with st.expander("Show Raw PTO Data"):
        st.dataframe(df_pto)

# Footer
st.markdown("---")
st.caption("Developed by Dan Reid • Simulated CAN/J1939 Telemetry • Powered by Streamlit")
