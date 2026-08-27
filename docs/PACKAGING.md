# Packaging (Windows)

## Build

```powershell
conda activate validation-team
cd D:\GAIA2026_desarrollo\Validation_TEAM
.\scripts\build_exe.ps1
```

Produces `release/Validation_TEAM/` with:

- `Validation_TEAM.exe`
- `_internal/` (PyInstaller runtime; keep intact)
- `backend/credentials.json` (copied if present on the build machine)
- `data/mapbiomas.db` and Excel assets when available

## Distribute

Copy the entire `release/Validation_TEAM` folder to the target PC. Internet is required.

## Run

Double-click `Validation_TEAM.exe`. The API serves the built frontend and opens a browser. Stop with Ctrl+C in the console window.

If port 8000 is busy, the launcher selects another local port.

## Rebuild notes

- Frontend source lives under `frontend/`
- Spec file: `Validation_TEAM.spec`
- Entry: `launcher.py`
