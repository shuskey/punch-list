#!/usr/bin/env pwsh
# Launch the Punch List web UI (Flask on http://localhost:5000).

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$python = (Get-Command python -ErrorAction SilentlyContinue)?.Source
if (-not $python) { $python = (Get-Command py -ErrorAction Stop).Source }

& $python -c "import flask" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing dependencies..."
    & $python -m pip install -r requirements.txt
}

& $python app.py
