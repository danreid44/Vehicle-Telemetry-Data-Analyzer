# Shared constants for CAN IDs and file paths used across the telemetry pipeline.
 
# J1939 CAN IDs written by the simulator and read by every consumer of the data
# These IDs are chosen based on 29-bit CAN identifiers in the SAE J1939 standard
CAN_ID_RPM = '0x0CF00400'
CAN_ID_PTO = '0x18FEF100'
CAN_ID_FAULT = '0x0CFE6CEE'
 
# File paths
CSV_PATH = "data/telemetry.csv"
DB_PATH = "db/telemetry.db"
DECODER_PATH = "data/spn_fmi_decoder.csv"
