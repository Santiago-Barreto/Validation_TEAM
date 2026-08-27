# Contributing — Validation TEAM

Internal GAIA / MapBiomas Colombia tooling. This guide helps new team members work independently on backend, frontend, or packaging.

## Repository areas

| Path | Owner focus |
|------|-------------|
| `backend/` | FastAPI, Earth Engine, comments storage, statistics |
| `frontend/` | React map client, auth, UI |
| `data/` | Runtime assets (DB, Excel); see `data/README.md` |
| `docs/` | Architecture, setup, credentials, auth, packaging |
| `scripts/` | Dev setup, cleanup, Windows `.exe` build |
| `packaging/` | Release notes consumed by the build script |

## First-time setup

```powershell
.\scripts\setup_dev.ps1
```

Then configure secrets and data per [docs/SETUP.md](docs/SETUP.md).

## Daily development

Terminal 1 — API:

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000 --app-dir .
```

Terminal 2 — UI:

```powershell
cd frontend
npm run dev
```

## Branching

- `main` — stable, deployable
- Feature branches — short-lived, named by task (e.g. `feat/legend-filter`, `fix/auth-skew`)

## Before opening a PR

1. Run backend tests: `python -m pytest backend/tests -q`
2. Build frontend: `cd frontend && npm run build`
3. Do **not** commit secrets (`.env`, `credentials.json`, `mapbiomas.db`, `comentarios_team.json`)
4. Update docs if behaviour, env vars, or folder layout changes

## Cleanup local artifacts

```powershell
.\scripts\clean.ps1
```

Removes build output, bytecode, and SQLite WAL sidecars. Keeps `.venv`, `node_modules`, and runtime data.

## Packaging (Windows)

```powershell
.\scripts\build_exe.ps1
```

Output: `release/Validation_TEAM/`. See [docs/PACKAGING.md](docs/PACKAGING.md).

## Questions

- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Credentials / Sheets: [docs/CREDENTIALS.md](docs/CREDENTIALS.md)
- Google Sign-In: [docs/AUTH.md](docs/AUTH.md)
