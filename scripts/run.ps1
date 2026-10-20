# ==============================================================================
# Global Photo Geolocator - Launch Script (Milestone 11)
# ==============================================================================
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\run.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\run.ps1 -Port 8080
#   powershell -ExecutionPolicy Bypass -File scripts\run.ps1 -HostAddress 0.0.0.0 -Port 8050
#   powershell -ExecutionPolicy Bypass -File scripts\run.ps1 -KillExisting
# ==============================================================================

[CmdletBinding()]
param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8080,
    [switch]$Reload,
    [switch]$OpenBrowser,
    [switch]$KillExisting
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $ProjectRoot

$VenvDir = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "`n[ERROR] Virtual environment not found at $VenvDir." -ForegroundColor Red
    Write-Host "Please run the setup script first:" -ForegroundColor Yellow
    Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1`n" -ForegroundColor White
    exit 1
}

# ------------------------------------------------------------------------------
# Port Collision & Address Resolution
# ------------------------------------------------------------------------------
function Test-PortOccupied([int]$CheckPort) {
    $connections = Get-NetTCPConnection -LocalPort $CheckPort -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }
    if ($null -ne $connections -and $connections.Count -gt 0) {
        return $true
    }
    return $false
}

$RequestedPort = $Port

# Automatically clean up any previous Python/Uvicorn server instances listening on the requested port
$existingListening = Get-NetTCPConnection -LocalPort $RequestedPort -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' -and $_.OwningProcess -gt 0 }
if ($existingListening) {
    $procIds = $existingListening.OwningProcess | Select-Object -Unique
    foreach ($pidToKill in $procIds) {
        $proc = Get-Process -Id $pidToKill -ErrorAction SilentlyContinue
        if ($proc -and ($proc.ProcessName -match "python" -or $KillExisting)) {
            Write-Host "[CLEANUP] Stopping previous server instance (PID ${pidToKill} - $($proc.ProcessName)) on port $RequestedPort..." -ForegroundColor Yellow
            Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 600
        }
    }
}

if (Test-PortOccupied -CheckPort $Port) {
    Write-Host "[NOTICE] Address http://${HostAddress}:${Port} is actively in use by an external service." -ForegroundColor Yellow
    $OriginalPort = $Port
    while (Test-PortOccupied -CheckPort $Port) {
        $Port++
    }
    Write-Host "[AUTO-ASSIGN] Automatically selected available address: http://${HostAddress}:${Port}`n" -ForegroundColor Cyan
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "             EARTHTRACE — GLOBAL PHOTO GEOLOCATOR           " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Architecture: Keyless Multi-Hypothesis Pipeline           " -ForegroundColor White
Write-Host "  Evidence:     OSM Geometry | DEM Skyline | Sat | Street   " -ForegroundColor White
Write-Host "  VRAM Budget:  Single-resident ModelManager (4-8 GB GPU)  " -ForegroundColor White
Write-Host "  API Keys:     ZERO (No external tokens or paid services)  " -ForegroundColor White
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "  [RESPONSIBLE USE NOTICE]" -ForegroundColor Yellow
Write-Host "  Intended for defensive research, verification, historical " -ForegroundColor DarkYellow
Write-Host "  geosearch, and disaster mapping. Do not use to stalk, dox," -ForegroundColor DarkYellow
Write-Host "  harass, or compromise private persons or residences.      " -ForegroundColor DarkYellow
Write-Host "============================================================" -ForegroundColor Cyan

$AppUrl = "http://${HostAddress}:${Port}"
Write-Host "`nServer URL: " -NoNewline -ForegroundColor Green
Write-Host "$AppUrl" -ForegroundColor White
Write-Host "Press Ctrl+C to gracefully stop the application.`n" -ForegroundColor DarkGray

if ($OpenBrowser) {
    Start-Process $AppUrl
}

$UvicornArgs = @(
    "-m", "uvicorn",
    "geolocator.app.api:app",
    "--host", $HostAddress,
    "--port", $Port.ToString()
)

if ($Reload) {
    $UvicornArgs += "--reload"
}

try {
    & $VenvPython $UvicornArgs
}
catch {
    # Ignore terminal interrupt exceptions
}

# If process exited cleanly or was gracefully terminated via Ctrl+C (SIGINT exit codes: 0, 1, 130, 0xC000013A), reset exit code
if ($LASTEXITCODE -in @(0, 1, 130, 3221225786, -1073741510)) {
    $global:LASTEXITCODE = 0
    exit 0
}
