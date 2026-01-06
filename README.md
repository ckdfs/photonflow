# PhotonFlow

PhotonFlow is a composable optical/electrical modulation simulator with a web UI and desktop application.

## Structure
- `frontend/`: React + Vite UI
- `backend/`: Python simulation engine + FastAPI server
- `src-tauri/`: Tauri desktop application wrapper
- `docs/`: design docs and model notes
- `scripts/`: build and utility scripts

## Quick Start

### Development Mode

#### Backend (dev)
```bash
cd backend
uvicorn photonflow.server.app:app --host 0.0.0.0 --port 8000 --reload --app-dir src
```

#### Frontend (dev)
```bash
cd frontend
npm install
npm run dev
```

#### Desktop App (dev)
```bash
# Tauri will auto-start backend and frontend
cd src-tauri
cargo tauri dev
```

### Docker Deployment
```bash
docker-compose up
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

## Docs generation
```bash
conda run -n photonflow bash -lc "PYTHONPATH=backend/src python backend/scripts/generate_param_docs.py"
```

## Tests (backend)
```bash
conda run -n photonflow bash -lc "PYTHONPATH=backend/src python -m unittest discover -s backend/tests"
```

## Verify (docs + tests)
```bash
./scripts/verify.sh
```

## Install git hooks
```bash
./scripts/install_git_hooks.sh
```

## CI
GitHub Actions 会运行 `./scripts/verify.sh`（生成文档 + 后端测试）。

## Quick sanity test (backend)
```bash
PYTHONPATH=backend/src python -c "from photonflow.core import Graph, SimConfig; data={'version':'0.1','sim':{'backend':'torch','device':'cpu','fs':1e10,'oversample':4,'seed':0,'window':'hann','duration_s':1e-8},'nodes':[{'id':'laser1','type':'Laser','params':{'power_dbm':0.0}},{'id':'rf1','type':'RFSource','params':{'freq_hz':1e9,'amplitude':1.0}},{'id':'pm1','type':'PM','params':{'Vpi':4.0}},{'id':'osa1','type':'OSAProbe'},{'id':'pd1','type':'PD','params':{'responsivity':1.0}},{'id':'esa1','type':'ESAProbe'}],'edges':[{'src':'laser1','src_port':'opt_out','dst':'pm1','dst_port':'opt_in'},{'src':'rf1','src_port':'elec_out','dst':'pm1','dst_port':'elec_in'},{'src':'pm1','src_port':'opt_out','dst':'pd1','dst_port':'opt_in'},{'src':'pm1','src_port':'opt_out','dst':'osa1','dst_port':'opt_in'},{'src':'pd1','src_port':'elec_out','dst':'esa1','dst_port':'elec_in'}],'outputs':{'extra':[{'node':'osa1','port':'opt_in','kind':'osa'},{'node':'esa1','port':'elec_in','kind':'esa'}]}}; graph=Graph.from_dict(data, validate=True); outputs=graph.run(SimConfig(fs=1e10, duration_s=1e-8)); print('ok', len(outputs))"
```

## Build & Release

### Windows Desktop Build
```powershell
# Full build (backend + frontend + tauri)
.\scripts\build_windows.ps1

# Skip specific parts
.\scripts\build_windows.ps1 -SkipBackend
.\scripts\build_windows.ps1 -SkipFrontend

# Output: src-tauri/target/release/bundle/
```

### Linux/macOS Build
```bash
# Build backend with PyInstaller
cd backend
pyinstaller photonflow.spec --log-level=INFO --noconfirm

# Copy sidecar binary
mkdir -p ../src-tauri/binaries
cp dist/photonflow-server ../src-tauri/binaries/server-<target-triple>

# Build frontend
cd ../frontend
npm install && npm run build

# Build Tauri app
cd ../src-tauri
cargo tauri build
```

### Production Docker
```bash
# Build images
docker-compose build

# Run in production
docker-compose up -d

# View logs
docker-compose logs -f
```

## Available Blocks

**Optical**: Laser, PM, MZM, DPMZM, Coupler, PhaseShifter, Attenuator, OpticalFiber, OpticalFilter, PolarizationRotator, PolarizationPDL, PolarizationWaveplate, PolarizationController

**Electrical**: RFSource, DCSource, ElecSplitter, ElecGain

**Detectors**: PD (Photodetector)

**Measurement**: OSAProbe (Optical Spectrum), ESAProbe (Electrical Spectrum), ScopeProbe (Time Domain)

## Troubleshooting

### Desktop App Issues

**App crashes immediately after splash screen:**
- Check if backend sidecar processes are still running: `Get-Process | Where-Object {$_.ProcessName -eq "server"}`
- Kill stale processes: `Get-Process -Name server* | Stop-Process -Force`
- Ensure sidecar name in `src-tauri/src/main.rs` matches `tauri.conf.json`:
  - Config: `"externalBin": ["binaries/server"]`
  - Rust: `.sidecar("server")`

**Build fails with "Permission Denied" error:**
- Kill any running backend processes before rebuilding
- Clean build cache: `Remove-Item -Recurse -Force src-tauri\target\release\build`

**Sidecar not found:**
- Verify binary exists: `src-tauri/binaries/server-x86_64-pc-windows-msvc.exe`
- Rebuild backend: `.\scripts\build_windows.ps1 -SkipFrontend`

### Backend Development

**Import errors:**
- Ensure `PYTHONPATH=backend/src` is set
- Activate conda environment: `conda activate photonflow`

**Module not found (torch/fastapi):**
- Install dependencies: `pip install -r backend/requirements.txt`

### Frontend Development

**React component errors:**
- Clear node_modules and reinstall: `cd frontend && rm -rf node_modules && npm install`
- Check browser console for detailed error messages
