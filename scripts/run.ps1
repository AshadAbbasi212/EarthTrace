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
    $connections = Get-NetTCPConnection -LocalPort $CheckPort -ErrorAction SilentlyContinue
    if ($null -ne $connections -and $connections.Count -gt 0) {
        return $true
    }
    return $false
}

$RequestedPort = $Port

if ($KillExisting) {
    $existingConns = Get-NetTCPConnection -LocalPort $RequestedPort -ErrorAction SilentlyContinue
    if ($existingConns) {
        $procIds = $existingConns.OwningProcess | Where-Object { $_ -gt 0 } | Select-Object -Unique
        foreach ($pidToKill in $procIds) {
            Write-Host "[CLEANUP] Stopping existing process (PID $pidToKill) on port $RequestedPort..." -ForegroundColor Yellow
            Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Milliseconds 800
    }
}

if (Test-PortOccupied -CheckPort $Port) {
    Write-Host "[NOTICE] Address http://${HostAddress}:${Port} is already in use or locked by Windows TCP." -ForegroundColor Yellow
    $OriginalPort = $Port
    while (Test-PortOccupied -CheckPort $Port) {
        $Port++
    }
    Write-Host "[AUTO-ASSIGN] Automatically selected available address: http://${HostAddress}:${Port}`n" -ForegroundColor Cyan
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "             GLOBAL PHOTO GEOLOCATOR (100% Local)           " -ForegroundColor Cyan
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

& $VenvPython $UvicornArgs
