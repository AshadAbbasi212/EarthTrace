# ==============================================================================
# Global Photo Geolocator - Windows Setup Script (Milestone 11)
# ==============================================================================
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1
#
# Requirements:
#   - Windows 10/11
#   - Python 3.10, 3.11, or 3.12 (64-bit)
#   - NVIDIA GPU with 4GB - 8GB+ VRAM (Recommended)
# ==============================================================================

[CmdletBinding()]
param(
    [switch]$SkipWeightDownload,
    [switch]$SkipGpuCheck
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n[+] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-WarningMsg {
    param([string]$Message)
    Write-Host "  [!] $Message" -ForegroundColor Yellow
}

function Write-Failure {
    param([string]$Message)
    Write-Host "  [ERROR] $Message" -ForegroundColor Red
}

Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "       Global Photo Geolocator - Windows Setup              " -ForegroundColor Magenta
Write-Host "       100% Keyless, Local Models, Zero API Tokens          " -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $ProjectRoot

# 1. Check Python
Write-Step "Checking Python Installation..."
$PythonCmd = Get-Command "python" -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    $PythonCmd = Get-Command "py" -ErrorAction SilentlyContinue
}

if (-not $PythonCmd) {
    Write-Failure "Python 3.10+ was not found in PATH."
    Write-Host "Please install Python 3.11 from https://www.python.org/downloads/ or via: winget install Python.Python.3.11"
    exit 1
}

$PyVerStr = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
Write-Success "Found Python $PyVerStr ($($PythonCmd.Source))"

# 2. Check NVIDIA GPU
Write-Step "Checking NVIDIA GPU & CUDA Drivers..."
$NvidiaSmi = Get-Command "nvidia-smi" -ErrorAction SilentlyContinue
if ($NvidiaSmi) {
    $GpuName = & nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | Select-Object -First 1
    Write-Success "Detected NVIDIA GPU: $GpuName"
} else {
    Write-WarningMsg "nvidia-smi not detected in PATH. If you have an NVIDIA GPU, verify drivers are installed."
}

# 3. Create Virtual Environment (.venv)
$VenvDir = Join-Path $ProjectRoot ".venv"
Write-Step "Setting up Python Virtual Environment in $VenvDir..."

if (-not (Test-Path $VenvDir)) {
    Write-Host "  Creating new virtual environment (.venv)..."
    & python -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Failure "Failed to create virtual environment."
        exit 1
    }
    Write-Success "Virtual environment created."
} else {
    Write-Success "Virtual environment already exists."
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"

# 4. Install / Upgrade Dependencies
Write-Step "Installing and Updating Dependencies..."
& $VenvPython -m pip install --upgrade pip setuptools wheel --quiet
Write-Host "  Installing geolocator in editable development mode..."
& $VenvPip install -e . --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Failure "Dependency installation failed."
    exit 1
}
Write-Success "Dependencies installed successfully."

# 5. Check GPU via check_gpu.py
if (-not $SkipGpuCheck) {
    Write-Step "Verifying GPU Memory & Sequential Model Budget..."
    $CheckGpuScript = Join-Path $ProjectRoot "scripts\check_gpu.py"
    if (Test-Path $CheckGpuScript) {
        & $VenvPython $CheckGpuScript
    }
}

# 6. Pre-cache Model Weights (Optional / Default)
if (-not $SkipWeightDownload) {
    Write-Step "Pre-downloading & Caching Model Weights for Offline Use..."
    $DlScript = Join-Path $ProjectRoot "scripts\download_weights.py"
    if (Test-Path $DlScript) {
        & $VenvPython $DlScript
    }
}

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "              Setup Completed Successfully!                 " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "`nTo start the Geolocator Web Application:" -ForegroundColor Yellow
Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\run.ps1`n" -ForegroundColor White
Write-Host "Or activate the venv directly:" -ForegroundColor Yellow
Write-Host "  .venv\Scripts\activate`n" -ForegroundColor White
