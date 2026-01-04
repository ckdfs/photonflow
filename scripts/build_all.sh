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

# 2. Prepare Sidecar
echo "Preparing Sidecar..."
mkdir -p src-tauri/binaries
# Detect architecture (simplified for x86_64 linux)
TARGET="x86_64-unknown-linux-gnu"
if [ -f "backend/dist/photonflow-server" ]; then
    cp backend/dist/photonflow-server src-tauri/binaries/server-$TARGET
else
    echo "Warning: Backend binary not found. If you skipped backend build, ensure it was built previously."
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
# Use the local tauri cli installed in frontend
if [ -f "frontend/node_modules/.bin/tauri" ]; then
    ./frontend/node_modules/.bin/tauri build
elif command -v cargo-tauri &> /dev/null; then
    cargo-tauri build
else
    cargo tauri build
fi

echo "Build Complete!"
