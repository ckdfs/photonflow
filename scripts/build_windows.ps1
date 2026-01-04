# Windows Build Script for PhotonFlow
# Run this in PowerShell: .\scripts\build_windows.ps1

param (
    [switch]$SkipBackend,
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"

# 1. Build Backend
if (-not $SkipBackend) {
    Write-Host "Building Backend..." -ForegroundColor Cyan
    Set-Location backend
    
    # Check if we are already in the photonflow environment
    if ($env:CONDA_DEFAULT_ENV -eq "photonflow") {
        Write-Host "Already in 'photonflow' environment. Running PyInstaller directly..."
        pyinstaller photonflow.spec --log-level=INFO --noconfirm
    }
    # Check for conda command if not in env
    elseif (Get-Command conda -ErrorAction SilentlyContinue) {
        Write-Host "Using Conda environment 'photonflow' via conda run..."
        # Use --no-capture-output to stream logs
        conda run -n photonflow --no-capture-output pyinstaller photonflow.spec --log-level=INFO --noconfirm
    } else {
        Write-Host "Using current Python environment..."
        pyinstaller photonflow.spec --log-level=INFO --noconfirm
    }
    
    if (-not (Test-Path "dist/photonflow-server.exe")) {
        Write-Error "Backend build failed: dist/photonflow-server.exe not found."
    }
    Set-Location ..
} else {
    Write-Host "Skipping Backend Build..." -ForegroundColor Yellow
}

# 2. Prepare Sidecar
Write-Host "Preparing Sidecar..." -ForegroundColor Cyan
$BinDir = "src-tauri/binaries"
if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir | Out-Null
}

# Target triple for Windows (x86_64-pc-windows-msvc)
$Target = "x86_64-pc-windows-msvc"
$SourceExe = "backend/dist/photonflow-server.exe"
$DestExe = "$BinDir/server-$Target.exe"

if (Test-Path $SourceExe) {
    Copy-Item -Path $SourceExe -Destination $DestExe -Force
    Write-Host "Sidecar copied to $DestExe" -ForegroundColor Green
} else {
    if (-not $SkipBackend) {
        Write-Error "Source executable not found at $SourceExe"
    } else {
        Write-Warning "Backend binary not found. Ensure it was built previously."
    }
}

# 3. Build Frontend
if (-not $SkipFrontend) {
    Write-Host "Building Frontend..." -ForegroundColor Cyan
    Set-Location frontend
    npm install
    npm run build
    Set-Location ..
} else {
    Write-Host "Skipping Frontend Build..." -ForegroundColor Yellow
}

# 4. Build Tauri App
Write-Host "Building Tauri App..." -ForegroundColor Cyan

# Ensure targets are correct for Windows in tauri.conf.json
# We can't easily edit JSON with regex safely, but we assume the user handles it or defaults are ok.
# If targets was set to ["deb"] on Linux, it might fail on Windows or produce nothing.
# Ideally, tauri.conf.json should use "targets": "all" or platform specific overrides if supported (v2 supports it).

# Check for local tauri
if (Test-Path "frontend/node_modules/.bin/tauri.cmd") {
    & .\frontend\node_modules\.bin\tauri.cmd build
} elseif (Get-Command cargo-tauri -ErrorAction SilentlyContinue) {
    cargo-tauri build
} else {
    cargo tauri build
}

Write-Host "Build Complete!" -ForegroundColor Green
