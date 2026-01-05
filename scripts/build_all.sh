#!/bin/bash
set -e

SKIP_BACKEND=false
SKIP_FRONTEND=false

# Parse arguments
for arg in "$@"; do
  case $arg in
    --skip-backend)
      SKIP_BACKEND=true
      shift
      ;;
    --skip-frontend)
      SKIP_FRONTEND=true
      shift
      ;;
  esac
done

# 1. Build Backend
if [ "$SKIP_BACKEND" = true ]; then
    echo "Skipping Backend Build..."
else
    echo "Building Backend..."
    cd backend
    # Ensure we are using the photonflow environment
    # Use source activate to avoid output buffering issues with 'conda run'
    # Try to find conda base path
    CONDA_BASE=$(conda info --base 2>/dev/null || echo $HOME/miniconda3)
    if [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
        source "$CONDA_BASE/etc/profile.d/conda.sh"
        conda activate photonflow
        pyinstaller photonflow.spec --log-level=INFO --noconfirm
    elif command -v conda &> /dev/null; then
        # Fallback if we can't source
        conda run -n photonflow --no-capture-output pyinstaller photonflow.spec --log-level=INFO --noconfirm
    else
        pyinstaller photonflow.spec --log-level=INFO --noconfirm
    fi
    cd ..
fi

# 2. Prepare Sidecar (--onedir mode)
echo "Preparing Sidecar..."
mkdir -p src-tauri/binaries

# Detect target triple
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
case "$OS" in
    linux)
        case "$ARCH" in
            x86_64) TARGET="x86_64-unknown-linux-gnu" ;;
            aarch64) TARGET="aarch64-unknown-linux-gnu" ;;
            *) TARGET="$ARCH-unknown-linux-gnu" ;;
        esac
        EXT=""
        ;;
    darwin)
        case "$ARCH" in
            x86_64) TARGET="x86_64-apple-darwin" ;;
            arm64) TARGET="aarch64-apple-darwin" ;;
            *) TARGET="$ARCH-apple-darwin" ;;
        esac
        EXT=""
        ;;
    *)
        echo "Unsupported OS: $OS"
        exit 1
        ;;
esac

# --onedir mode: PyInstaller generates a directory with exe and dependencies
SOURCE_DIR="backend/dist/photonflow-server"

if [ -d "$SOURCE_DIR" ]; then
    # Clean old binaries directory content
    rm -rf src-tauri/binaries/*
    
    # Copy all files from onedir output to binaries folder
    # This includes the exe and all its dependencies
    cp -r "$SOURCE_DIR"/* src-tauri/binaries/
    
    # Rename the executable to match Tauri's naming convention
    SOURCE_EXE="src-tauri/binaries/photonflow-server$EXT"
    DEST_EXE="src-tauri/binaries/server-$TARGET$EXT"
    if [ -f "$SOURCE_EXE" ]; then
        mv "$SOURCE_EXE" "$DEST_EXE"
        chmod +x "$DEST_EXE"
        echo "Sidecar prepared at $DEST_EXE (with dependencies)"
    else
        echo "Error: photonflow-server not found in $SOURCE_DIR"
        exit 1
    fi
else
    if [ "$SKIP_BACKEND" = true ]; then
        echo "Warning: Backend directory not found. Ensure it was built previously."
    else
        echo "Error: Source directory not found at $SOURCE_DIR. PyInstaller --onedir should create this."
        exit 1
    fi
fi

# 3. Build Frontend
if [ "$SKIP_FRONTEND" = true ]; then
    echo "Skipping Frontend Build..."
else
    echo "Building Frontend..."
    cd frontend
    npm install
    npm run build
    cd ..
fi

# 4. Build Tauri App
echo "Building Tauri App..."

# Determine bundle type based on OS
case "$OS" in
    linux)
        BUNDLE_TYPE="deb"
        ;;
    darwin)
        BUNDLE_TYPE="dmg"
        ;;
    *)
        BUNDLE_TYPE="all"
        ;;
esac

# Use the local tauri cli installed in frontend
if [ -f "frontend/node_modules/.bin/tauri" ]; then
    ./frontend/node_modules/.bin/tauri build --bundles "$BUNDLE_TYPE"
elif command -v cargo-tauri &> /dev/null; then
    cargo-tauri build --bundles "$BUNDLE_TYPE"
else
    cargo tauri build --bundles "$BUNDLE_TYPE"
fi

echo "Build Complete!"
