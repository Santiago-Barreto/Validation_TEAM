# Validation TEAM

Collaborative MapBiomas Colombia validation workstation (Collection 3 vs Collection 4).

FastAPI backend + React / Leaflet frontend. Supports biome mosaics, Landsat overlays, pixel inspection, team comments, and a statistics panel.

## Repository layout

```
Validation_TEAM/
├── backend/                 API (FastAPI, Earth Engine, stats, comments)
├── frontend/                Web client (Vite + React + Leaflet)
├── data/                    Local runtime assets (SQLite, Excel)
│   └── reference/           Non-runtime reference material
├── docs/                    Product and operations documentation
├── scripts/                 setup_dev.ps1, clean.ps1, build_exe.ps1
├── packaging/               Desktop packaging notes
├── .github/workflows/       CI (pytest + frontend build)
├── launcher.py              Windows executable entrypoint
└── Validation_TEAM.spec     PyInstaller specification
```

## Requirements

- Conda or Python 3.13+
- Node.js 20+
- Google Earth Engine service account (`backend/credentials.json`)
- Internet access (EE tiles, basemaps)

## First clone (checklist)

1. Clone the repository
2. Run `.\scripts\setup_dev.ps1`
3. Copy `backend/credentials.json` (Earth Engine service account)
4. Copy `backend/.env.example` → `backend/.env` and set OAuth / Sheets IDs
5. Copy `data/mapbiomas.db` from the Statistics project ([data/README.md](data/README.md))
6. Optional: copy Excel interpreter file into `data/` (already in repo if present)

See [docs/SETUP.md](docs/SETUP.md) for full configuration.

## Local development

```powershell
conda activate validation-team
cd D:\GAIA2026_desarrollo\Validation_TEAM
.\scripts\setup_dev.ps1
```

Terminal 1 — API:

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000 --app-dir .
```

Terminal 2 — UI:

```powershell
cd frontend
npm run dev
```

- API: http://127.0.0.1:8000  
- UI: http://127.0.0.1:5173  

## Maintenance scripts

| Script | Purpose |
|--------|---------|
| `scripts/setup_dev.ps1` | Install Python + npm deps, verify local config |
| `scripts/clean.ps1` | Remove build artifacts, `__pycache__`, SQLite WAL sidecars |
| `scripts/build_exe.ps1` | Build Windows desktop package |

## Desktop package

```powershell
.\scripts\build_exe.ps1
```

Output: `release/Validation_TEAM/`. See [docs/PACKAGING.md](docs/PACKAGING.md).

## Documentation

| Document | Topic |
|----------|--------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | Team workflow, PR checklist |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design and data flow |
| [docs/SETUP.md](docs/SETUP.md) | Environment and configuration |
| [docs/CREDENTIALS.md](docs/CREDENTIALS.md) | Secrets and persistence backends |
| [docs/AUTH.md](docs/AUTH.md) | Google Sign-In (@gaiaamazonas.org) |
| [docs/PACKAGING.md](docs/PACKAGING.md) | Windows `.exe` distribution |
| [data/README.md](data/README.md) | Local data assets |

## License / ownership

Internal GAIA 2026 / MapBiomas Colombia tooling.
