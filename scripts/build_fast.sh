#!/bin/bash
# Fast build script - builds executable without bundling installer
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
    CONDA_BASE=$(conda info --base 2>/dev/null || echo $HOME/miniconda3)
    if [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
        source "$CONDA_BASE/etc/profile.d/conda.sh"
        conda activate photonflow
        pyinstaller photonflow.spec --log-level=INFO --noconfirm
    elif command -v conda &> /dev/null; then
        conda run -n photonflow --no-capture-output pyinstaller photonflow.spec --log-level=INFO --noconfirm
    else
        pyinstaller photonflow.spec --log-level=INFO --noconfirm
    fi
    cd ..
fi

# 2. Prepare Sidecar
echo "Preparing Sidecar..."
mkdir -p src-tauri/binaries
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

# 4. Build Tauri (Release mode, no bundling)
echo "Building Tauri executable (no bundling)..."
cd src-tauri
cargo build --release
cd ..

echo ""
echo "✅ Fast Build Complete!"
echo "Executable: ./src-tauri/target/release/photonflow"
echo ""
echo "To run: ./src-tauri/target/release/photonflow"
echo "To build full installer: ./scripts/build_all.sh"
