#!/bin/bash

# Bash script to run the live demo for the telemetry dashboard.
python simulate_loop.py &  # Generate new telemetry.csv
streamlit run dashboard.py  # Run the Streamlit dashboard