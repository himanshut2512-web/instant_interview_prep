# Start backend (FastAPI on :8000) and frontend (Vite on :5173) for development on Windows.
# Usage (PowerShell):  .\scripts\dev.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path "$Root\backend\.venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv "$Root\backend\.venv"
    & "$Root\backend\.venv\Scripts\pip.exe" install -q -r "$Root\backend\requirements.txt"
}
if (-not (Test-Path "$Root\backend\.env")) {
    Copy-Item "$Root\backend\.env.example" "$Root\backend\.env"
    Write-Host "Created backend\.env - add ANTHROPIC_API_KEY there for AI mode (demo mode works without it)."
}
if (-not (Test-Path "$Root\frontend\node_modules")) {
    Write-Host "Installing frontend dependencies..."
    Push-Location "$Root\frontend"; npm install --no-fund --no-audit; Pop-Location
}

$backend = Start-Process -PassThru -NoNewWindow -WorkingDirectory "$Root\backend" `
    -FilePath "$Root\backend\.venv\Scripts\uvicorn.exe" -ArgumentList "app.main:app", "--reload", "--port", "8000"
Write-Host "Backend: http://localhost:8000   Frontend: http://localhost:5173"
try {
    Push-Location "$Root\frontend"
    npm run dev
}
finally {
    Pop-Location
    Stop-Process -Id $backend.Id -ErrorAction SilentlyContinue
}
