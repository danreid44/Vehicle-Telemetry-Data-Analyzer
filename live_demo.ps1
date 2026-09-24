$ErrorActionPreference = 'Stop'

$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = Join-Path $scriptDirectory 'venv\Scripts\python.exe'
$streamlitPath = Join-Path $scriptDirectory 'venv\Scripts\streamlit.exe'

if (-not (Test-Path $pythonPath)) {
    $pythonPath = 'python'
}

if (-not (Test-Path $streamlitPath)) {
    $streamlitPath = 'streamlit'
}

$simulator = Start-Process `
    -FilePath $pythonPath `
    -ArgumentList 'simulate_loop.py' `
    -WorkingDirectory $scriptDirectory `
    -PassThru

try {
    & $streamlitPath run dashboard.py
}
finally {
    if (-not $simulator.HasExited) {
        Stop-Process -Id $simulator.Id -Force
    }
}
