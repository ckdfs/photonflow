# Windows Build Script for PhotonFlow
# Run this in PowerShell: .\scripts\build_windows.ps1
#
# Useful options:
# - Skip backend build:  .\scripts\build_windows.ps1 -SkipBackend
# - Skip frontend build: .\scripts\build_windows.ps1 -SkipFrontend
# - Build app .exe only (no MSI): .\scripts\build_windows.ps1 -NoMsi

param (
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    # When set, build the Tauri .exe but skip generating MSI installer.
    [switch]$NoMsi
)

$ErrorActionPreference = "Stop"

function Assert-LastExitCode {
    param(
        [Parameter(Mandatory = $true)][string]$Context
    )
    if ($LASTEXITCODE -ne 0) {
        throw "$Context failed with exit code $LASTEXITCODE."
    }
}

function Ensure-WindowsResourceTooling {
    # Tauri's build script uses tauri-winres -> embed-resource, which requires either:
    # - Microsoft rc.exe (Windows SDK) or
    # - GNU windres.exe (MinGW)
    #
    # If neither is discoverable, fail early with actionable guidance.

    $rc = Get-Command rc.exe -ErrorAction SilentlyContinue
    if ($null -ne $rc) {
        return
    }

    $windres = Get-Command windres.exe -ErrorAction SilentlyContinue
    if ($null -ne $windres) {
        return
    }

    # Try to locate rc.exe from installed Windows SDK and temporarily add it to PATH.
    $possibleKeys = @(
        "HKLM:\SOFTWARE\Microsoft\Windows Kits\Installed Roots",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows Kits\Installed Roots"
    )

    $kitRoots = @()
    foreach ($keyPath in $possibleKeys) {
        if (Test-Path $keyPath) {
            try {
                $props = Get-ItemProperty -Path $keyPath
                foreach ($name in @("KitsRoot10", "KitsRoot81")) {
                    $val = $props.$name
                    if ($val -and (Test-Path $val)) {
                        $kitRoots += $val
                    }
                }
            } catch {
                # ignore and keep searching
            }
        }
    }

    $candidateRcDirs = @()
    foreach ($root in ($kitRoots | Select-Object -Unique)) {
        $binRoot = Join-Path $root "bin"
        if (-not (Test-Path $binRoot)) {
            continue
        }

        # Typical layout: <KitsRoot10>\bin\10.0.x.y\x64\rc.exe
        Get-ChildItem -Path $binRoot -Directory -ErrorAction SilentlyContinue |
            ForEach-Object {
                $x64 = Join-Path $_.FullName "x64"
                $rcExe = Join-Path $x64 "rc.exe"
                if (Test-Path $rcExe) {
                    $candidateRcDirs += $x64
                }
            }

        # Some SDKs also have: <KitsRoot>\bin\x64\rc.exe
        $flatX64 = Join-Path $binRoot "x64"
        if (Test-Path (Join-Path $flatX64 "rc.exe")) {
            $candidateRcDirs += $flatX64
        }
    }

    if ($candidateRcDirs.Count -gt 0) {
        # Pick the newest by parent folder version when possible.
        $best = $candidateRcDirs |
            Sort-Object -Descending -Property {
                $ver = Split-Path (Split-Path $_ -Parent) -Leaf
                try { [version]$ver } catch { [version]"0.0" }
            } |
            Select-Object -First 1

        $env:PATH = "$best;$env:PATH"

        $rc = Get-Command rc.exe -ErrorAction SilentlyContinue
        if ($null -ne $rc) {
            Write-Host "Found rc.exe via Windows SDK; added to PATH: $best" -ForegroundColor Green
            return
        }
    }

    throw @"
Missing Windows resource compiler (required by Tauri on Windows).

Tauri's build step needs either:
- rc.exe (Windows SDK)  OR
- windres.exe (MinGW)

Fix options (recommended):
1) Install Visual Studio Build Tools (or Visual Studio) with:
   - "Desktop development with C++"
   - "Windows 10/11 SDK" (10.0.19041+)
2) Re-open a new PowerShell and re-run this script.

If you already installed the SDK but still see this:
- Verify rc.exe exists under: C:\Program Files (x86)\Windows Kits\10\bin\<version>\x64\rc.exe
"@
}

# 1. Build Backend
if (-not $SkipBackend) {
    Write-Host "Building Backend..." -ForegroundColor Cyan
    Set-Location backend
    
    # Check if we are already in the photonflow environment
    if ($env:CONDA_DEFAULT_ENV -eq "photonflow") {
        Write-Host "Already in 'photonflow' environment. Running PyInstaller directly..."
        pyinstaller photonflow.spec --log-level=INFO --noconfirm
        Assert-LastExitCode "PyInstaller"
    }
    # Check for conda command if not in env
    elseif (Get-Command conda -ErrorAction SilentlyContinue) {
        Write-Host "Using Conda environment 'photonflow' via conda run..."
        # Use --no-capture-output to stream logs
        conda run -n photonflow --no-capture-output pyinstaller photonflow.spec --log-level=INFO --noconfirm
        Assert-LastExitCode "PyInstaller (conda run)"
    } else {
        Write-Host "Using current Python environment..."
        pyinstaller photonflow.spec --log-level=INFO --noconfirm
        Assert-LastExitCode "PyInstaller"
    }
    
    # --onedir output (directory) with exe inside
    if (-not (Test-Path "dist/photonflow-server/photonflow-server.exe")) {
        Write-Error "Backend build failed: dist/photonflow-server/photonflow-server.exe not found."
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
    Assert-LastExitCode "npm install"
    npm run build
    Assert-LastExitCode "npm run build"
    Set-Location ..
} else {
    Write-Host "Skipping Frontend Build..." -ForegroundColor Yellow
}

# 4. Build Tauri App
Write-Host "Building Tauri App..." -ForegroundColor Cyan

Ensure-WindowsResourceTooling

$TauriBuildArgs = @("build")
if ($NoMsi) {
    Write-Host "NoMsi enabled: building app without bundling (no MSI)." -ForegroundColor Yellow
    $TauriBuildArgs += "--no-bundle"
} else {
    $TauriBuildArgs += @("--bundles", "msi")
}

# Check for local tauri
if (Test-Path "frontend/node_modules/.bin/tauri.cmd") {
    & .\frontend\node_modules\.bin\tauri.cmd @TauriBuildArgs
    Assert-LastExitCode "tauri (npm)"
} elseif (Get-Command cargo-tauri -ErrorAction SilentlyContinue) {
    cargo-tauri @TauriBuildArgs
    Assert-LastExitCode "cargo-tauri"
} else {
    cargo tauri @TauriBuildArgs
    Assert-LastExitCode "cargo tauri"
}

Write-Host "Build Complete!" -ForegroundColor Green
