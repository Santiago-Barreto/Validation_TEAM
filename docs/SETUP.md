# Setup

## Quick start (new machine)

```powershell
conda create -n validation-team python=3.13 -y
conda activate validation-team
cd D:\GAIA2026_desarrollo\Validation_TEAM
.\scripts\setup_dev.ps1
```

### Required local files (not in git)

| File | Purpose |
|------|---------|
| `backend/credentials.json` | Earth Engine service account |
| `backend/.env` | OAuth client ID, Sheets backend, optional paths |
| `data/mapbiomas.db` | Statistics panel (copy from Statistics project) |

### Optional local files

| File | Purpose |
|------|---------|
| `data/COLOMBIA_COL_4_Formatos de avance detallado Colombia.xlsx` | Interpreter lookup on map click |
| `backend/data/comentarios_team.json` | Only when `PUNTOS_BACKEND=json` (copy from `comentarios_team.example.json`) |

## Python environment (manual)

```powershell
conda activate validation-team
pip install -r backend\requirements.txt
```

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Comments backend

Default in `backend/.env.example` is Google Sheets:

| Setting | Value |
|---------|--------|
| Spreadsheet | **Comentarios_APP_TEAM** |
| `GOOGLE_SHEET_ID` | See `.env.example` |
| Service account | Editor access on the sheet |

Each packaged PC needs `backend/.env` with the same `GOOGLE_SHEET_ID`.

For offline / local JSON mode, set `PUNTOS_BACKEND=json` and create `backend/data/comentarios_team.json` from the example file.

## Runtime data

| Path | Required for | Notes |
|------|--------------|-------|
| `backend/credentials.json` | Map tiles / EE | Gitignored |
| `data/mapbiomas.db` | Statistics panel | Gitignored; copy from Statistics project |
| `data/COLOMBIA_COL_4_Formatos de avance detallado Colombia.xlsx` | Interpreter on click | Optional |

See `backend/.env.example` for optional environment variables.

## Health checks

- `GET /health` — process alive
- `GET /ready` — storage backend readiness
- `GET /configuracion` — client bootstrap payload

## Development ports

| Service | Port |
|---------|------|
| API | 8000 |
| Vite | 5173 |

## Cleanup

Remove build artifacts and bytecode without touching secrets or runtime DB:

```powershell
.\scripts\clean.ps1
```

## Tests

```powershell
python -m pytest backend/tests -q
```
