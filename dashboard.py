import streamlit as st
import sqlite3
import pandas as pd
from analyze import (
    get_rpm_data,
    get_rpm_stats,
    get_pto_data,
    get_pto_stats,
    get_fault_data
) # Importing functions from analyze.py

# Load data
DB_PATH = "db/telemetry.db"
df_rpm = get_rpm_data(DB_PATH)
df_pto = get_pto_data(DB_PATH)
rpm_stats = get_rpm_stats(DB_PATH)
pto_stats = get_pto_stats(DB_PATH)
df_fault = get_fault_data(DB_PATH)


# Streamlit page settings
st.set_page_config(
    page_title="Vehicle Telemetry Dashboard",
    layout="wide"
)
st.title("Vehicle Telemetry Dashboard")
st.markdown("Analyze simulated J1939 vehicle data: engine RPM, PTO activation, and more.")

# Tabbed layout
tab0, tab1, tab2, tab3 = st.tabs(["Dashboard Summary","Engine RPM", "PTO Activation", "Fault Codes"])

# Dashboard Summary Tab
with tab0:
    st.subheader("Dashboard Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("RPM Statistics")
        st.metric("Min RPM", f"{rpm_stats['min_rpm']} RPM")
        st.metric("Max RPM", f"{rpm_stats['max_rpm']} RPM")
        st.metric("Avg RPM", f"{rpm_stats['avg_rpm']} RPM")

    with col2:
        st.markdown("PTO Activity")
        st.metric("Total PTO Duration", f"{pto_stats['pto_duration_min']} min")
        st.metric("PTO Activation Count", f"{pto_stats['pto_usage_count']} times")

    with col3:
        st.markdown("Fault Codes")
        if df_fault.empty:
            st.success("No fault codes detected.")
        else:
            st.metric("Total Faults", f"{len(df_fault)}")

    st.markdown("---")
    st.caption("This summary shows key metrics from the latest simulated data in the telemetry database.")

# Engine RPM Tab
with tab1:
    st.subheader("Engine RPM Over Time")
    st.line_chart(df_rpm.set_index("timestamp")["rpm"])
    
    st.markdown(f"""
    **RPM Stats**
    - Min: {rpm_stats['min_rpm']} RPM
    - Max: {rpm_stats['max_rpm']} RPM
    - Avg: {rpm_stats['avg_rpm']} RPM
    """)

    with st.expander("Show Raw RPM Data"):
        st.dataframe(df_rpm)

# PTO Activation Tab
with tab2:
    st.subheader("PTO Activation Timeline")
    st.line_chart(df_pto.set_index("timestamp")["pto_on"].astype(int))
    
    st.markdown(f"""
    **PTO Stats**
    - Total Duration: {pto_stats['pto_duration_min']} minutes
    - Usage Frequency: {pto_stats['pto_usage_count']} activations
    """)

    with st.expander("Show Raw PTO Data"):
        st.dataframe(df_pto)

with tab3:
    st.subheader("Fault Codes Overview")
    st.markdown("This section shows any fault codes detected in the telemetry data.")
    
    if df_fault.empty:
        st.success("No fault codes detected in the current dataset.")
    else:
        st.dataframe(df_fault)
        st.markdown(f"Total Faults: {len(df_fault)}")
        st.markdown("Fault codes are represented by SPN (Suspect Parameter Number) and FMI (Failure Mode Identifier).")
        
# Footer
st.markdown("---")
st.caption("Developed by Dan Reid • Simulated CAN/J1939 Data • Powered by Streamlit")
