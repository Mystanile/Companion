$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$pip = Join-Path $PSScriptRoot ".venv\Scripts\pip.exe"

if (-not (Test-Path $python)) {
    Write-Error "Virtual env not found. Run: python -m venv .venv"
}

& $pip install pyinstaller | Out-Null

& $python -m PyInstaller `
    --noconfirm `
    --windowed `
    --name Companion `
    --add-data "config.yaml;." `
    --add-data ".env.example;." `
    --hidden-import=pygame `
    --hidden-import=keyboard `
    --hidden-import=sounddevice `
    --hidden-import=edge_tts `
    --hidden-import=groq `
    --collect-all edge_tts `
    main.py

$dist = Join-Path $PSScriptRoot "dist\Companion"
Copy-Item (Join-Path $PSScriptRoot "config.yaml") $dist -Force
Copy-Item (Join-Path $PSScriptRoot ".env.example") $dist -Force

if (-not (Test-Path (Join-Path $dist ".env"))) {
    if (Test-Path (Join-Path $PSScriptRoot ".env")) {
        Copy-Item (Join-Path $PSScriptRoot ".env") $dist -Force
    } else {
        Copy-Item (Join-Path $dist ".env.example") (Join-Path $dist ".env") -Force
    }
}

Write-Host ""
Write-Host "Built: $dist\Companion.exe"
Write-Host "Double-click Companion.exe to run (no terminal)."
Write-Host "Edit .env in that folder for your Groq API key."
