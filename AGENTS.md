# AGENTS Persistent Context

## Code Organization Rules
- **Backend**: Keep all Python code under `backend/src/photonflow/`
- **Frontend**: Keep all TypeScript/React code under `frontend/src/`
- **Tauri**: Keep Rust code under `src-tauri/src/`
- **Docs**: Keep documentation under `docs/`
- **Scripts**: Keep build/utility scripts under `scripts/`

## Development Principles
1. **Incremental Changes**: Make small, verifiable changes one at a time
2. **Test First**: Run tests after each significant change
3. **Document Updates**: Update docs when adding features or changing APIs
4. **Type Safety**: Use type hints in Python, TypeScript in frontend
5. **Error Handling**: Validate inputs early, provide clear error messages

## Code Style
### Python (Backend)
- **Formatting**: Follow PEP 8
- **Type Hints**: Use for all public functions
- **Docstrings**: Use for all classes and public methods
- **Imports**: Absolute imports from `photonflow.*`
- **Testing**: Use `unittest` framework

### TypeScript (Frontend)
- **Formatting**: Use consistent 2-space indentation
- **Types**: Prefer interfaces over types for object shapes
- **Components**: Functional components with hooks
- **State**: Use useState/useEffect appropriately

### Rust (Tauri)
- **Formatting**: Use `cargo fmt`
- **Linting**: Address `cargo clippy` warnings
- **Safety**: Prefer safe Rust, avoid `unsafe` unless necessary

## Adding New Blocks
1. Create new file in `backend/src/photonflow/blocks/{category}/`
2. Inherit from `BaseBlock`
3. Use `@register_block()` decorator
4. Define `ports` class variable (dict)
5. Define `spec` class variable (params + nonideal)
6. Implement `process(inputs, backend)` method
7. Import in `backend/src/photonflow/blocks/__init__.py`
8. Run `generate_param_docs.py` to update docs
9. Add tests in `backend/tests/`
10. Update frontend `i18n.ts` for labels

## Modifying Graph Schema
1. Update `backend/src/photonflow/schema/graph_schema.json`
2. Update `docs/graph_json_schema.md` to match
3. Update `Graph.from_dict()` if needed
4. Update frontend TypeScript interfaces
5. Run validation tests

## Adding Documentation
- **Physics Models**: Add to `docs/physics_models.md` with formulas
- **Parameters**: Auto-generated in `docs/params_graph_ui.md`
- **Concepts**: Add to `docs/basic_definitions.md`
- **Roadmap**: Update `docs/next_steps.md`

## Common Tasks
### Run Backend Dev Server
```bash
cd backend
PYTHONPATH=src uvicorn photonflow.server.app:app --reload
```

### Run Frontend Dev Server
```bash
cd frontend
npm run dev
```

### Run Tauri Dev
```bash
cd src-tauri
cargo tauri dev
```

### Run Tests
```bash
conda run -n photonflow python -m unittest discover -s backend/tests
```

### Regenerate Docs
```bash
conda run -n photonflow bash -lc "PYTHONPATH=backend/src python backend/scripts/generate_param_docs.py"
```

### Build Desktop App (Windows)
```powershell
.\scripts\build_windows.ps1
```

### Build Desktop App (Linux/macOS)
```bash
./scripts/build_all.sh
```

## Debugging Tips
1. **Backend Errors**: Check FastAPI logs, validate JSON against schema
2. **Frontend Errors**: Check browser console, React DevTools
3. **Graph Compilation**: Use `/graph/validate` endpoint
4. **Expansion Issues**: Use `/graph/expand` with `annotate=true`
5. **Simulation Errors**: Check `sim_runner.py` logs, verify signal shapes
6. **Tauri Sidecar Issues**: 
   - Ensure sidecar name consistency between `tauri.conf.json` and Rust code
   - Kill stale backend processes before rebuilding: `Get-Process -Name server* | Stop-Process -Force`
   - Verify sidecar binary exists in `src-tauri/binaries/`

## Tauri Development Notes

### Sidecar Configuration
**Critical**: Sidecar name must match between config and code:
- `tauri.conf.json`: `"externalBin": ["binaries/server"]`
- `main.rs`: `app.shell().sidecar("server")`
- Binary file: `src-tauri/binaries/server-{target-triple}.exe`

### Common Pitfalls
1. **Bundle Identifier**: Don't use `.app` suffix (conflicts with macOS)
2. **Process Cleanup**: Always kill sidecar processes before rebuilding
3. **Binary Path**: Use forward slashes in config, even on Windows
4. **Window Lifecycle**: Main window must be hidden initially, shown after backend ready

## Git Hooks
- Install with `./scripts/install_git_hooks.sh`
- Pre-commit: Runs `verify.sh` (docs + tests)
- Ensure all tests pass before committing

## CI/CD
- **GitHub Actions**: Runs `./scripts/verify.sh` on push
- **Verify Script**: Generates docs + runs backend tests
- Fix failures before merging PRs
