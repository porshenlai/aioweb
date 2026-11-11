$ErrorActionPreference = "Stop"

$ROOT = $PSScriptRoot
$VENV = Join-Path $ROOT "venv"
$PY = Join-Path $VENV "Scripts\python.exe"
$THPY = "D:\apps\thonny\python.exe"

# Note: The original logic falls back to creation only if $THPY is missing.
# If you intended to create the venv when $THPY exists, change '!Test-Path $THPY' to 'Test-Path $THPY'.
if (-not (Test-Path -Path $PY -PathType Leaf)) {
    if (Test-Path -Path $THPY -PathType Leaf) {
        Write-Host "Install from thonny"
        & $THPY -m venv $VENV
        & $PY -m pip install --upgrade pip aiohttp aiohttp_cors aiofiles
    }
}

if (-not (Test-Path -Path $PY -PathType Leaf)) {
    Write-Host "$PY not found"
    exit 1
}

$APP = Join-Path $ROOT "app\aioweb.py"
& $PY $APP @args
