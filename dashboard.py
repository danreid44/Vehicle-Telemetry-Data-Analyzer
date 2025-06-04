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
tab0, tab1, tab2, tab3, tab4 = st.tabs(["Dashboard Summary","Engine RPM", "PTO Activation", "Fault Codes", "About"])

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

    # Download RPM Data as CSV
    st.download_button(
        label="Download RPM Data as CSV",
        data=df_rpm.to_csv(index=False),
        file_name="rpm_data.csv",
        mime="text/csv"
    )

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

    # Download PTO Data as CSV
    st.download_button(
        label="Download PTO Data as CSV",
        data=df_pto.to_csv(index=False),
        file_name="pto_data.csv",
        mime="text/csv"
    )

# Fault Codes Tab
with tab3:
    st.subheader("Fault Codes Overview")
    st.markdown("This section shows any fault codes detected in the telemetry data.")
    
    if df_fault.empty:
        st.success("No fault codes detected in the current dataset.")
    else:
        st.dataframe(df_fault)
        st.markdown(f"Total Faults: {len(df_fault)}")
        st.markdown("Fault codes are represented by SPN (Suspect Parameter Number) and FMI (Failure Mode Identifier).")

    # Download Fault Codes as CSV
    st.download_button(
        label="Download Fault Codes as CSV",
        data=df_fault.to_csv(index=False),
        file_name="fault_data.csv",
        mime="text/csv"
    )
    
# About Tab
with tab4:
    st.subheader("About This Dashboard")
    st.markdown("""
    This dashboard provides an interactive way to analyze simulated J1939 vehicle telemetry data.
    
    - **Engine RPM**: Displays engine RPM over time with key statistics.
    - **PTO Activation**: Shows PTO activation status and duration.
    - **Fault Codes**: Lists any fault codes detected in the telemetry data.
    - **SQLite database** for telemetry storage
    - **REST API access** via Postman for CRUD operations
    
    Th raw data can be downloaded as CSV files for further analysis.
                
    """)

                
# Footer
st.markdown("---")
st.caption("Developed by Dan Reid • Simulated CAN/J1939 Data • Powered by Streamlit")
