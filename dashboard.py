import streamlit as st

# Streamlit page settings
st.set_page_config(
    page_title="Vehicle Telemetry Dashboard",
    layout="wide"
)

import altair as alt
import time
from analyze import (
    get_rpm_data,
    get_rpm_stats,
    get_pto_data,
    get_pto_stats,
    get_fault_data,
    get_fault_frequency,
    get_fault_stats,
    get_mtbf
) # Importing functions from analyze.py

# Import Auto Refresh
from streamlit_autorefresh import st_autorefresh

# Refresh the dashboard every 5 seconds
live_refresh = st.sidebar.checkbox("Live Refresh (every 5s)", value=True)

if live_refresh:
    st_autorefresh(interval=5000, key="dashboard_refresh")


# Load data
DB_PATH = "db/telemetry.db"
df_rpm = get_rpm_data(DB_PATH)
df_pto = get_pto_data(DB_PATH)
rpm_stats = get_rpm_stats(DB_PATH)
pto_stats = get_pto_stats(DB_PATH)
df_fault = get_fault_data(DB_PATH)
fault_freq = get_fault_frequency(df_fault)
fault_stats = get_fault_stats(df_fault)
mtbf = get_mtbf(df_fault)


# Function to highlight severity in fault codes
def highlight_severity(val):
    color = {
        "Critical": "red",
        "Warning": "orange",
        "Info": "green",
    }.get(val, "black")  # Fallback color
    return f"color: {color}; font-weight: bold;"


st.title("Vehicle Telemetry Dashboard")
st.markdown("Analyze simulated J1939 vehicle data: engine RPM, PTO activation, fault codes, and more.")

# Tabbed layout
tab0, tab1, tab2, tab3, tab4 = st.tabs(["Dashboard Summary","Engine RPM", "PTO Activation", "Fault Codes", "About"])

# Dashboard Summary Tab
with tab0:
    st.subheader("System Summary")
    refresh_status = "Active" if live_refresh else "Paused"
    st.caption(f"Live Refresh: {refresh_status} — Last updated {time.strftime('%H:%M:%S')}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**RPM Statistics**")
        st.metric("Min RPM", f"{rpm_stats['min_rpm']} RPM")
        st.metric("Max RPM", f"{rpm_stats['max_rpm']} RPM")
        st.metric("Avg RPM", f"{rpm_stats['avg_rpm']} RPM")

    with col2:
        st.markdown("**PTO Activity**")
        st.metric("Total PTO Duration", f"{pto_stats['pto_duration_min']} min")
        st.metric("PTO Activation Count", f"{pto_stats['pto_usage_count']} times")

    with col3:
        st.markdown("**Fault Codes**")
        if df_fault.empty:
            st.success("No fault codes detected.")
        else:
            st.metric("Total Faults", f"{fault_stats['total_faults']}")
            st.metric("Critical Faults", f"{fault_stats['critical_count']}")
            if mtbf:
                st.metric("Mean Time Between Faults", f"{mtbf:.1f} sec")
            else:
                st.write("Not enough data to calculate MTBF.")

    st.markdown("---")
    st.markdown("""
    This summary shows key metrics from the latest simulated data in the telemetry database. 
    Please explore the tabs for detailed analysis on each of these parameters.
    
    """)
    
# Engine RPM Tab
with tab1:
    st.subheader("Engine RPM Over Time")
    st.line_chart(df_rpm.set_index("timestamp")["rpm"])
    
    st.subheader("RPM Statistics")
    st.markdown(f"""
    - Min: {rpm_stats['min_rpm']} RPM
    - Max: {rpm_stats['max_rpm']} RPM
    - Avg: {rpm_stats['avg_rpm']} RPM
    """)

    with st.expander("**Show Raw RPM Data**"):
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
    
    st.subheader("PTO Activity Statistics")
    st.markdown(f"""
    - Total Duration: {pto_stats['pto_duration_min']} minutes
    - Usage Frequency: {pto_stats['pto_usage_count']} activations
    """)

    with st.expander("**Show Raw PTO Data**"):
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
    
    # Create Altair bar chart
    chart = alt.Chart(fault_freq).mark_bar().encode(
        x=alt.X("wrapped_description:N", sort="-y", title="Fault Description"),
        y=alt.Y("count:Q", title="Count"),
        color=alt.Color("severity:N", scale=alt.Scale(domain=["Critical", "Warning", "Info"], range=["red", "orange", "green"])),
        tooltip=["wrapped_description", "count", "severity"]
    ).properties(
        width="container",
        height=400,
        title="Top Faults by Frequency"
    ).configure_axisX(
        labelAngle=0,  # Horizontal labels
        labelLimit=0 # 
    )
    st.altair_chart(chart, use_container_width=True)

    # Display fault code statistics
    st.subheader("Fault Code Statistics")
    col1, col2 = st.columns(2)
    most_recent = fault_stats["most_recent"]
    if most_recent is None or df_fault.empty:
        st.success("No fault codes detected in the current dataset.")
    else:
        with col1:
            st.markdown(f"""
            - Total Faults: {fault_stats['total_faults']}
            - Critical Faults: {fault_stats['critical_count']}
            - Warning Faults: {fault_stats['warning_count']}
            - Info Faults: {fault_stats['info_count']}
            - Mean Time Between Faults: {mtbf:.1f} sec
            """)
        with col2:
            st.write(f"• Most Recent Fault: {most_recent['wrapped_description']}")
            st.write(f"• Time: {fault_stats['last_fault_time']}")
            st.write(f"• Severity: {most_recent['severity']}")

    # Display fault code data with severity highlighting
    st.subheader("Fault Code Data")
    if df_fault.empty:
        st.success("No fault codes detected in the current dataset.")
    else:
        styled_df = df_fault[["timestamp", "spn", "fmi", "description", "severity"]].style.map(
            highlight_severity, subset=["severity"]
        )
        st.dataframe(styled_df, use_container_width=True)
    
    # Download Fault Codes as CSV
    st.download_button(
        label="Download Fault Codes as CSV",
        data=df_fault.to_csv(index=False),
        file_name="fault_data.csv",
        mime="text/csv"
    )
    
    # List number of faults and overview of fault codes
    st.markdown("Fault codes are represented by SPN (Suspect Parameter Number) and FMI (Failure Mode Identifier).")

# About Tab
with tab4:
    st.subheader("About This Dashboard")
    st.markdown("""
    This dashboard provides an interactive way to analyze simulated J1939 vehicle telemetry data.
    
    - **Engine RPM**: Displays engine RPM over time with key statistics.
    - **PTO Activation**: Shows PTO activation timeline and stats.
    - **Fault Codes**: Shows detected fault codes with severity levels and frequency.
    - **SQLite database** for telemetry storage
    - **REST API access** via Postman for CRUD operations
    
    The raw data can be downloaded as CSV files for further analysis.
                
    """)

                
# Footer
st.markdown("---")
st.caption("Developed by Dan Reid • Simulated CAN/J1939 Data • Powered by Streamlit")
