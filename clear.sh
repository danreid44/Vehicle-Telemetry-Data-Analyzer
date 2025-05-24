#!/bin/bash

# Delete telemetry CSV
rm -f data/telemetry.csv

# Delete telemetry database
rm -f db/telemetry.db

echo "Cleared telemetry CSV and database."
