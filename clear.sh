#!/bin/bash

# Bash script to clear telemetry CSV and database 
# Execute file: ./clear.sh

# Delete telemetry CSV in data directory
if [ -e data/telemetry.csv ]; then
    rm data/telemetry.csv
    echo "Cleared telemetry CSV."
else
    echo "Error: data/telemetry.csv does not exist."
fi

# Delete telemetry database in SQLite
if [ -e db/telemetry.db ]; then
    rm db/telemetry.db
    echo "Cleared telemetry database."
else
    echo "Error: db/telemetry.db does not exist."
fi

