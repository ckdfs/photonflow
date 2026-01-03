# PhotonFlow

PhotonFlow is a composable optical/electrical modulation simulator with a web UI.

## Structure
- `frontend/`: React + Vite UI
- `backend/`: Python simulation engine + API
- `docs/`: design docs and model notes

## Backend (dev)
```bash
cd backend
PYTHONPATH=src uvicorn photonflow.server.app:app --host 0.0.0.0 --port 8000 --reload
```

## Frontend (dev)
```bash
cd frontend
npm install
npm run dev
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
