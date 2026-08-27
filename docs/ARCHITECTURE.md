# Architecture

## Purpose

Validation TEAM lets analysts compare MapBiomas Colombia Collection 4 regional classifications against Collection 3 integration layers, inspect pixels, leave structured comments, and review biome-level statistics.

## Stack

| Layer | Technology |
|-------|------------|
| API | FastAPI, Earth Engine Python API, optional SQLAlchemy |
| Persistence | Local JSON (default), optional Google Sheets or PostgreSQL |
| Client | Vite, React 19, Leaflet, Plotly, Framer Motion |
| Packaging | PyInstaller launcher serving the production frontend build |

## Components

```
frontend ──HTTP──► backend ──► Earth Engine assets
                      │
                      ├── data/mapbiomas.db (statistics)
                      ├── data/*.xlsx (interpreter assignment)
                      └── backend/data/comentarios_team.json
```

### Backend (`backend/`)

| Area | Responsibility |
|------|----------------|
| `core/` | Config, EE auth, legend palette, biome catalogs, paths |
| `routers/` | HTTP surface (MapBiomas, Landsat, stats, comments) |
| `services/` | Mosaic building, inventory, bounds, Excel lookup, storage |
| `models/` / `db/` | Pydantic records and optional ORM |

### Frontend (`frontend/`)

| Area | Responsibility |
|------|----------------|
| `components/` | Map, control panel, layers, stats, comments |
| `hooks/` | Layer orchestration and debounce |
| `config/` | API base URL, basemaps, comment marker style |
| `services/` | Offline comment queue |

## Primary flows

1. Select biomes → execute → inventory Col4 assets → load tiles.
2. Adjust year / opacity / coverage filters.
3. Click map → optional correction comment (name, text, suggested class).
4. Open statistics panel → biome or region metrics and heatmap.

## Comments storage

Default: Google Sheets (`Comentarios_APP_TEAM`).

```
timestamp | lat | lon | nombre | comentario | clase_sugerida | anio_contexto | bioma | resuelto | creado_por | resuelto_por | foto_url | grupo_id
```

`resuelto` values: empty (open on map), `check` (✓), or `x` (✗). Resolved comments stay in the sheet but are hidden on the map. `creado_por` / `resuelto_por` store Gaia Amazonas emails after Google Sign-In. `foto_url` stores the author's Google profile picture for map markers. `grupo_id` links multiple points that share the same comment entity (resolve applies to the whole group).

Offline queue: `gaia2026_team_comments_queue` → `POST /guardar`.

## External assets

- Regions: `…/VECTORES/col-clasificacion-regiones-c3`
- Col3: `…/COLECCION3/INTEGRACION/integracion-regiones`
- Col4: `…/COLECCION4/clasificacion-ft`
- Landsat mosaics: `…/MOSAICOS/VALIDATOR/mosaico_landsat_{year}`

## Isolation from Validation

TEAM comments use a dedicated spreadsheet ID and must not reuse the Validation sheet.
