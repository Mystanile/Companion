$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonw = Join-Path $root ".venv\Scripts\pythonw.exe"
$main = Join-Path $root "main.py"

if (-not (Test-Path $pythonw)) {
    Write-Error "Run setup first: python -m venv .venv && pip install -r requirements.txt"
}

Start-Process -FilePath $pythonw -ArgumentList "`"$main`"" -WindowStyle Hidden
