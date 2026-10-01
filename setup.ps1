<#
.SYNOPSIS
    Cloud-Native Automated Compliance & Audit System (CACA) - Universal Setup Script (Windows PowerShell)
.DESCRIPTION
    Creates isolated Python environment, installs all dependencies, initializes database,
    seeds sample data, and starts both FastAPI backend and Next.js frontend.
    Works on Windows 10/11 with PowerShell 5.1+ or PowerShell Core 7+.
#>

param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000,
    [string]$PythonCmd = "python",
    [string]$NodeCmd = "node",
    [string]$NpmCmd = "npm"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VenvDir = Join-Path $ProjectRoot ".venv"
$BackendPid = $null
$FrontendPid = $null

# Colors
$Red = [ConsoleColor]::Red
$Green = [ConsoleColor]::Green
$Yellow = [ConsoleColor]::Yellow
$Blue = [ConsoleColor]::Cyan
$Cyan = [ConsoleColor]::Cyan
$Bold = "Bold"

function Log-Info { Write-Host "[INFO] $args" -ForegroundColor $Blue }
function Log-Success { Write-Host "[✓] $args" -ForegroundColor $Green }
function Log-Warn { Write-Host "[!] $args" -ForegroundColor $Yellow }
function Log-Error { Write-Host "[✗] $args" -ForegroundColor $Red }
function Log-Step { Write-Host "`n▶ $args" -ForegroundColor $Cyan }
function Show-Banner {
    Write-Host @"
╔═══════════════════════════════════════════════════════════════════════╗
║  ☁️  Cloud-Native Automated Compliance & Audit System (CACA)          ║
║  🎓  Final Year Capstone Project  |  RegTech  |  AI + Serverless      ║
╚═══════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor $Cyan
}

function Cleanup {
    Log-Info "Shutting down services..."
    if ($BackendPid) { Stop-Process -Id $BackendPid -Force -ErrorAction SilentlyContinue }
    if ($FrontendPid) { Stop-Process -Id $FrontendPid -Force -ErrorAction SilentlyContinue }
    Get-Process -Name "uvicorn", "node" -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $PID } | Stop-Process -Force -ErrorAction SilentlyContinue
    exit 0
}

$global:cleanupRegistered = $false
Register-EngineEvent -SourceIdentifier "PowerShell.Exiting" -Action { Cleanup } -SupportEvent | Out-Null
$global:cleanupRegistered = $true

function Check-Command($cmd, $name, $minVersion = $null) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Log-Error "$name not found. Please install $name and add to PATH."
        exit 1
    }
    if ($minVersion) {
        $version = & $cmd --version 2>&1 | Select-String -Pattern '(\d+\.\d+)' | ForEach-Object { $_.Matches[0].Value }
        if (-not ([Version]$version -ge [Version]$minVersion)) {
            Log-Error "$name $version found, but $minVersion+ required"
            exit 1
        }
    }
    return $cmd
}

function Setup-Venv($pyCmd) {
    Log-Step "Creating isolated Python environment..."
    if (Test-Path $VenvDir) {
        Log-Warn "Existing .venv found, recreating..."
        Remove-Item $VenvDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    & $pyCmd -m venv $VenvDir
    Log-Success "Virtual environment ready at .venv/"
}

function Install-PythonDeps {
    Log-Step "Installing Python dependencies..."
    $pip = Join-Path $VenvDir "Scripts" "pip.exe"
    $reqFile = Join-Path $ProjectRoot "backend" "requirements.txt"
    if (-not (Test-Path $reqFile)) {
        Log-Error "Requirements file not found: $reqFile"
        exit 1
    }
    & $pip install --quiet -r $reqFile 2>&1 | Select-Object -Last 5
    Log-Success "Python packages installed"
}

function Install-NodeDeps {
    Log-Step "Installing Node.js dependencies..."
    Push-Location (Join-Path $ProjectRoot "frontend")
    if (Test-Path "package-lock.json") {
        & $NpmCmd ci --silent 2>&1 | Select-Object -Last 3
    } else {
        & $NpmCmd install --silent 2>&1 | Select-Object -Last 3
    }
    Pop-Location
    Log-Success "Node packages installed"
}

function Init-Database {
    Log-Step "Initializing database & seeding samples..."
    $py = Join-Path $VenvDir "Scripts" "python.exe"
    & $py -c "
import sys
sys.path.insert(0, 'backend')
from backend.database import engine, Base
from backend.models import AuditDocument, ComplianceFinding, AuditReport
Base.metadata.create_all(bind=engine)
print('  Database schema created')
"
    & $py -c "
import sys
sys.path.insert(0, 'backend')
from backend.main import seed_sample_documents
from backend.database import SessionLocal
db = SessionLocal()
try:
    result = seed_sample_documents(db)
    if result['seeded_files']:
        print('  Seeded: {0} sample documents'.format(len(result['seeded_files'])))
    else:
        print('  Samples already exist')
finally:
    db.close()
"
    Log-Success "Database initialized with sample compliance documents"
}

function Start-Backend {
    Log-Step "Starting FastAPI Backend (port $BackendPort)..."
    $py = Join-Path $VenvDir "Scripts" "python.exe"
    $backend = Start-Process -FilePath $py -ArgumentList "-m uvicorn backend.main:app --host 0.0.0.0 --port $BackendPort --log-level warning" -WorkingDirectory $ProjectRoot -PassThru
    $global:BackendPid = $backend.Id

    # Wait for backend
    for ($i=1; $i -le 30; $i++) {
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:$BackendPort/" -TimeoutSec 2 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) { Log-Success "Backend ready at http://localhost:$BackendPort"; Log-Success "API Documentation: http://localhost:$BackendPort/docs"; return }
        } catch { Start-Sleep -Milliseconds 500 }
    }
    Log-Error "Backend failed to start within 30s"
    exit 1
}

function Start-Frontend {
    Log-Step "Starting Next.js Frontend (port $FrontendPort)..."
    $frontend = Start-Process -FilePath $NpmCmd -ArgumentList "run dev" -WorkingDirectory (Join-Path $ProjectRoot "frontend") -PassThru
    $global:FrontendPid = $frontend.Id

    for ($i=1; $i -le 20; $i++) {
        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:$FrontendPort/" -TimeoutSec 2 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) { Log-Success "Frontend ready at http://localhost:$FrontendPort"; return }
        } catch { Start-Sleep -Seconds 1 }
    }
    Log-Warn "Frontend may still be compiling... check http://localhost:$FrontendPort"
}

# =============================================================================
# MAIN
# =============================================================================
Show-Banner
Log-Info "Project: CACA - Compliance Audit System"
Log-Info "Root: $ProjectRoot"

# Prerequisites
Log-Step "Checking prerequisites..."
$PyCmd = Check-Command $PythonCmd "Python" "3.10"
$NodeCmd = Check-Command $NodeCmd "Node.js" "18"
$NpmCmd = Check-Command $NpmCmd "npm"
Log-Success "Python: $(& $PyCmd --version)"
Log-Success "Node: $(& $NodeCmd --version)"
Log-Success "npm: $(& $NpmCmd --version)"

# Setup
Setup-Venv $PyCmd
Install-PythonDeps
Install-NodeDeps
Init-Database

# Launch
Start-Backend
Start-Frontend

# Display access info
Write-Host "`n================================================================" -ForegroundColor $Green
Write-Host "  🚀  PLATFORM RUNNING  🚀" -ForegroundColor $Green
Write-Host "================================================================" -ForegroundColor $Green
Write-Host "  Dashboard:      http://localhost:$FrontendPort" -ForegroundColor $Cyan
Write-Host "  API Docs:       http://localhost:$BackendPort/docs" -ForegroundColor $Cyan
Write-Host "  API Base:       http://localhost:$BackendPort/api" -ForegroundColor $Cyan
Write-Host "  Seed Samples:   POST http://localhost:$BackendPort/api/seed-samples" -ForegroundColor $Cyan
Write-Host "================================================================" -ForegroundColor $Green
Write-Host "`nPress Ctrl+C to stop all services`n" -ForegroundColor $Yellow

# Wait
Wait-Process -Id $BackendPid, $FrontendPid -ErrorAction SilentlyContinue
