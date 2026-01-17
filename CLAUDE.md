# CLAUDE Persistent Context

## Project Overview
- **Project**: PhotonFlow
- **Focus**: Composable optical/electrical modulation simulator with Web UI and Desktop App
- **Version**: 0.2.0
- **License**: See LICENSE file

## Technology Stack
### Backend
- **Language**: Python 3.x
- **Framework**: FastAPI (async REST API)
- **Simulation Engine**: PyTorch (CPU/CUDA support)
- **Schema Validation**: JSON Schema (Draft 2020-12) + Pydantic
- **Packaging**: PyInstaller (sidecar binary for Tauri)

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite 5
- **Graph Editor**: ReactFlow 11
- **HTTP Client**: Axios
- **i18n**: Custom bilingual support (zh/en)

### Desktop App
- **Framework**: Tauri 2.x
- **Language**: Rust
- **Architecture**: Sidecar pattern (embedded backend server)
- **Platform**: Windows, Linux, macOS

### Deployment
- **Container**: Docker + Docker Compose
- **CI/CD**: GitHub Actions (verify.sh: docs generation + tests)

## Architecture
```
┌─────────────────────────────────────────┐
│         Tauri Desktop App               │
│  ┌───────────────────────────────────┐  │
│  │   Frontend (React + ReactFlow)   │  │
│  │   - Graph Editor                  │  │
│  │   - Block Library                 │  │
│  │   - Inspector Panel               │  │
│  │   - Spectrum/Time Plots           │  │
│  └───────────┬───────────────────────┘  │
│              │ HTTP/WebSocket            │
│  ┌───────────▼───────────────────────┐  │
│  │   Backend Sidecar (FastAPI)      │  │
│  │   - Block Registry               │  │
│  │   - Graph Compiler & Validator   │  │
│  │   - Simulation Engine (PyTorch)  │  │
│  │   - Job Manager (async queue)    │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Key Design Decisions
### 1. Signal Representation
- **Optical**: Complex envelope E(t) with explicit center frequency f0
- **Electrical**: Real or complex baseband signal
- **Polarization**: Jones vector [Ex, Ey] for dual-pol support
- **Time Domain**: Uniform sampling with configurable fs and duration

### 2. Block System
- **Base Class**: `BaseBlock` with `process(inputs, backend) -> outputs`
- **Registry**: Decorator-based auto-registration
- **Composites**: Templates expanded at compile time (MZM, DPMZM)
- **Ports**: Typed (optical/electrical/control) with compatibility checks
- **Parameters**: Separate `params` (ideal) and `nonideal` (with enable switch)

### 3. Graph Execution
- **Compilation**: Topological sort + port validation
- **Expansion**: Composites flattened to atomic blocks
- **Execution**: Sequential (future: chunked/streaming for long waveforms)
- **Outputs**: Via probe nodes (OSAProbe, ESAProbe, ScopeProbe)

### 4. Measurement Probes
- **OSAProbe**: Optical spectrum (FFT + windowing)
- **ESAProbe**: Electrical spectrum (FFT + windowing)
- **ScopeProbe**: Time-domain waveform
- **Non-intrusive**: Probes don't modify signal flow

### 5. Nonideality Model
- **Default**: All nonideal parameters = 0 or false (ideal behavior)
- **Enable Switch**: `nonideal.enable` gates all impairments
- **Modular**: Each impairment can be toggled individually
- **Reproducible**: Controlled by global random seed

## File Organization
- `backend/src/photonflow/`: Python package root
  - `blocks/`: Block implementations (optical, electrical, detectors, measurement)
  - `core/`: Graph, Signal, SimConfig, Schema, Composites
  - `server/`: FastAPI app, JobManager, SimRunner
  - `measurements/`: Spectrum analysis helpers
  - `schema/`: JSON schema definition
- `frontend/src/`: TypeScript/React UI
  - `components/`: BlockLibrary, Inspector, Outputs, Plots, Nodes
  - `api.ts`: Backend HTTP client
  - `i18n.ts`: Bilingual labels
- `src-tauri/`: Rust desktop wrapper
  - `binaries/`: Sidecar executables (platform-specific)
  - `src/main.rs`: Tauri app entry
- `docs/`: Technical documentation
  - `basic_definitions.md`: Core concepts
  - `physics_models.md`: Formulas and equations
  - `params_graph_ui.md`: Parameter specs (auto-generated)
  - `graph_json_schema.md`: JSON format spec
  - `next_steps.md`: Roadmap
- `scripts/`: Build and utility scripts
  - `build_windows.ps1`: Windows build automation
  - `generate_param_docs.py`: Auto-generate parameter tables
  - `verify.sh`: CI validation (docs + tests)

## Development Workflow
1. **Backend Dev**: `PYTHONPATH=backend/src uvicorn photonflow.server.app:app --reload`
2. **Frontend Dev**: `cd frontend && npm run dev`
3. **Desktop Dev**: `cd src-tauri && cargo tauri dev`
4. **Tests**: `conda run -n photonflow python -m unittest discover -s backend/tests`
5. **Docs**: `./scripts/generate_param_docs.py` (requires photonflow conda env)
6. **Build**: `./scripts/build_windows.ps1` or `./scripts/build_all.sh`

## Important Conventions
- **Units**: Always specify in parameter descriptions (V, Hz, dBm, rad, etc.)
- **dB vs Linear**: Power in dBm/dB for params, linear internally
- **Zero = Disabled**: bandwidth_hz=0 means no bandwidth limit
- **Enum Defaults**: First option in list (e.g., bandwidth_kind="rect")
- **Port Naming**: `opt_in`, `opt_out`, `elec_in`, `elec_out`, etc.
- **Node IDs**: Must match `^[A-Za-z_][A-Za-z0-9_\-]*$`
