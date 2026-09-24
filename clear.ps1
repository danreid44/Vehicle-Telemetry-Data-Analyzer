$ErrorActionPreference = 'Stop'

$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$csvFile = Join-Path $scriptDirectory 'data\telemetry.csv'
$dbFile = Join-Path $scriptDirectory 'db\telemetry.db'

Remove-Item -Force -ErrorAction SilentlyContinue $csvFile
Write-Output 'Cleared telemetry CSV.'

# Remove SQLite journal files as well as the main database file.
Remove-Item -Force -ErrorAction SilentlyContinue @(
    $dbFile
    "$dbFile-wal"
    "$dbFile-shm"
    "$dbFile-journal"
)
Write-Output 'Cleared telemetry database.'
