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

# 2. Prepare Sidecar (--onedir mode)
Write-Host "Preparing Sidecar..." -ForegroundColor Cyan
$BinDir = "src-tauri/binaries"
if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir | Out-Null
}

# Target triple for Windows (x86_64-pc-windows-msvc)
$Target = "x86_64-pc-windows-msvc"

# --onedir mode: PyInstaller generates a directory with exe and dependencies
$SourceDir = "backend/dist/photonflow-server"

if (Test-Path $SourceDir) {
    # Clean old binaries directory content
    Get-ChildItem -Path $BinDir -Recurse | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    
    # Copy all files from onedir output to binaries folder
    # This includes the exe and all its dependencies (DLLs, etc.)
    Copy-Item -Path "$SourceDir\*" -Destination $BinDir -Recurse -Force
    
    # Rename the exe to match Tauri's externalBin naming convention
    $SourceExe = "$BinDir/photonflow-server.exe"
    $DestExe = "$BinDir/server-$Target.exe"
    if (Test-Path $SourceExe) {
        Move-Item -Path $SourceExe -Destination $DestExe -Force
        Write-Host "Sidecar prepared at $DestExe (with dependencies)" -ForegroundColor Green
    } else {
        Write-Error "photonflow-server.exe not found in $SourceDir"
    }
} else {
    if (-not $SkipBackend) {
        Write-Error "Source directory not found at $SourceDir. PyInstaller --onedir should create this."
    } else {
        Write-Warning "Backend directory not found. Ensure it was built previously."
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

# Check for local tauri
if (Test-Path "frontend/node_modules/.bin/tauri.cmd") {
    & .\frontend\node_modules\.bin\tauri.cmd build --bundles msi
} elseif (Get-Command cargo-tauri -ErrorAction SilentlyContinue) {
    cargo-tauri build --bundles msi
} else {
    cargo tauri build --bundles msi
}

Write-Host "Build Complete!" -ForegroundColor Green
