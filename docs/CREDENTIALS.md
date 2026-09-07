# Credentials and secrets

## Local files

| File | Role |
|------|------|
| `backend/credentials.json` | Google service account (Earth Engine; optional Sheets) |
| `backend/data/comentarios_team.json` | Default TEAM comment store |

Never commit credentials to public remotes.

## Environment variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_CREDENTIALS` | Inline service-account JSON (hosted deploys) |
| `PUNTOS_BACKEND` | `json` (default), `sheets`, `database`, or `auto` |
| `PUNTOS_JSON_PATH` | Override path for the JSON comment store |
| `GOOGLE_SHEET_ID` | Dedicated TEAM spreadsheet only (do not reuse Validation) |
| `DATABASE_URL` | Optional PostgreSQL URL |
| `STATISTICS_DB_PATH` | Override path to `mapbiomas.db` |
| `AVANCE_SHEET_ID` | Google Spreadsheet for interpreter assignment (online; preferred) |
| `AVANCE_SHEET_GID` | Tab gid within that spreadsheet (optional; e.g. `200812869`) |
| `AVANCE_SHEET` | Tab name (default `MAPA GENERAL COLOMBIA`) |
| `AVANCE_COLOMBIA_XLSX` | Fallback local Excel if Sheets is unavailable |
| `SERVE_STATIC` | `1` to serve `frontend/dist` from the API |
| `VALIDATION_TEAM_ROOT` | Install root override for packaged builds |

## Practices

- Keep TEAM comments isolated from the Validation spreadsheet.
- Prefer local JSON for day-to-day team work.
- Rotate service-account keys when access changes.
