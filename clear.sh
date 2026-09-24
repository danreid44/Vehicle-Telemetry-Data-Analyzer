#!/bin/bash

set -euo pipefail

# Bash script to clear telemetry CSV and database 
# Delete telemetry CSV in data directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CSV_FILE="$SCRIPT_DIR/data/telemetry.csv"
DB_FILE="$SCRIPT_DIR/db/telemetry.db"

if rm -f "$CSV_FILE"; then
    echo "Cleared telemetry CSV."
fi

# Remove SQLite journal files as well as the main database file.
if rm -f "$DB_FILE" "$DB_FILE-wal" "$DB_FILE-shm" "$DB_FILE-journal"; then
    echo "Cleared telemetry database."
fi

