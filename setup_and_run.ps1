<#
.SYNOPSIS
    Cloud-Native Automated Compliance & Audit System - Zero-Setup Launch Script (Windows PowerShell)
.DESCRIPTION
    Creates isolated Python environment, installs all dependencies, initializes database,
    seeds sample data, and starts both FastAPI backend and Next.js frontend.
#>

param(
    [string]$PythonCmd = "python",
    [string]$NodeCmd = "node",
    [string]$NpmCmd = "npm"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VenvDir = Join-Path $ProjectRoot ".venv"

function Log-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Log-Success { Write-Host "[SUCCESS] $args" -ForegroundColor Green }
function Log-Warn { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Log-Error { Write-Host "[ERROR] $args" -ForegroundColor Red }
function Log-Step { Write-Host "`n▶ $args" -ForegroundColor Magenta }

$backendPid = $null
$frontendPid = $null

function Cleanup {
    Log-Info "Shutting down..."
    if ($backendPid) { Stop-Process -Id $backendPid -Force -ErrorAction SilentlyContinue }
    if ($frontendPid) { Stop-Process -Id $frontendPid -Force -ErrorAction SilentlyContinue }
    exit 0
}

Register-EngineEvent -SourceIdentifier "PowerShell.Exiting" -Action { Cleanup } | Out-Null

# Check prerequisites
Log-Step "Checking prerequisites..."
foreach ($cmd in @($PythonCmd, $NodeCmd, $NpmCmd)) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Log-Error "$cmd not found. Please install $cmd and try again."
        exit 1
    }
}

$pyVer = & $PythonCmd --version 2>&1
$nodeVer = & $NodeCmd --version 2>&1
Log-Success "Python $pyVer | Node $nodeVer"

# Create venv
Log-Step "Creating isolated Python environment..."
if (Test-Path $VenvDir) {
    Log-Warn "Existing .venv found, removing..."
    Remove-Item $VenvDir -Recurse -Force
}
& $PythonCmd -m venv $VenvDir
$pip = Join-Path $VenvDir "Scripts" "pip.exe"
& $pip install --quiet --upgrade pip setuptools wheel

# Install Python deps
Log-Step "Installing Python dependencies..."
& $pip install --quiet -r (Join-Path $ProjectRoot "backend" "requirements.txt")
& $pip install --quiet -r (Join-Path $ProjectRoot "requirements-dev.txt") 2>$null
Log-Success "Python packages installed"

# Install Node deps
Log-Step "Installing Node.js dependencies..."
Push-Location (Join-Path $ProjectRoot "frontend")
& $NpmCmd ci --silent 2>$null || & $NpmCmd install --silent
Pop-Location
Log-Success "Node packages installed"

# Initialize DB & seed
Log-Step "Initializing database & seeding samples..."
$py = Join-Path $VenvDir "Scripts" "python.exe"
& $py -c "
import sys
sys.path.insert(0, 'backend')
from backend.database import engine, Base
from backend.models import AuditDocument, ComplianceFinding, AuditReport
Base.metadata.create_all(bind=engine)
print('Database schema created')
"
& $py -c "
import sys
sys.path.insert(0, 'backend')
from backend.main import seed_sample_documents
from backend.database import SessionLocal
db = SessionLocal()
try:
    result = seed_sample_documents(db)
    print(f'Seeded: {result[\"seeded_files\"]}')
finally:
    db.close()
"

# Start Backend
Log-Step "Starting FastAPI Backend (port 8000)..."
$backend = Start-Process -FilePath $py -ArgumentList "-m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level warning" -WorkingDirectory $ProjectRoot -PassThru
$backendPid = $backend.Id

# Wait for backend
for ($i=1; $i -le 30; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8000/" -TimeoutSec 2 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) { Log-Success "Backend ready at http://localhost:8000"; break }
    } catch { Start-Sleep -Milliseconds 500 }
}

# Start Frontend
Log-Step "Starting Next.js Frontend (port 3000)..."
$frontend = Start-Process -FilePath $NpmCmd -ArgumentList "run dev" -WorkingDirectory (Join-Path $ProjectRoot "frontend") -PassThru
$frontendPid = $frontend.Id

Start-Sleep -Seconds 3
Log-Success "Frontend ready at http://localhost:3000"

Write-Host "`n================================================================" -ForegroundColor Green
Write-Host "  Platform Running!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host "  Dashboard:  http://localhost:3000" -ForegroundColor Cyan
Write-Host "  API Docs:   http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  API Base:   http://localhost:8000/api" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Green
Write-Host "`nPress Ctrl+C to stop all services`n" -ForegroundColor Yellow

Wait-Process -Id $backendPid, $frontendPid -ErrorAction SilentlyContinue
