# Architecture — Validation TEAM

## Propósito

Permitir al equipo de validación MapBiomas Colombia:

1. Visualizar **Colección 4** (clasificación regional filtrada) y **Colección 3** (integración por región) por bioma.
2. Comparar clases en un punto (año 1985–2025; Col3 hasta 2024).
3. Dejar **comentarios de corrección** persistentes que refrescan el mapa.

La UI no replica el Code Editor de Earth Engine; replica la **metodología** del script base (biomas internos, `VERSIONES_DESEADAS`, máscaras, filtro de coberturas, inspector).

## Stack

| Capa | Tecnología | Notas |
|------|------------|--------|
| API | FastAPI + Earth Engine Python | Tiles XYZ vía `getMapId` |
| Persistencia | JSON local (default) / Sheets propio / DB | **Aislado de Validation** (`comentarios_team.json`) |
| Cliente | Vite, React 19, Leaflet, MarkerCluster | Modo comentario + drawer |
| Offline | `localStorage` queue | Flush al recuperar red |

## Flujo de datos

```
┌────────────┐   GET /configuracion    ┌──────────────┐
│  visor-team│ ◄────────────────────── │   backend    │
│            │                         │              │
│  Ejecutar  │ ── GET /inventario ───► │ biomas +     │
│  biomas    │ ── GET /landsat ──────► │ mosaico LS   │
│            │ ── GET /tiles/col4 ───► │ Col4 mosaic  │
│            │ ── GET /tiles/col3 ───► │ Col3 mosaic  │
│  Clic mapa │ ── GET /identificar ──► │ reduceRegion │
│            │ ── POST /guardar ─────► │ Sheets/JSON  │
│            │ ◄─ GET /puntos ──────── │              │
└────────────┘                         └──────────────┘
```

## Lógica Earth Engine (paridad con script)

| Concepto script | Módulo backend |
|-----------------|----------------|
| `biomasInternos` / colores | `core/biomas.py` |
| `VERSIONES_DESEADAS` | `core/versiones_col4.py` |
| `paths`, `YEAR_*`, bandas | `core/paths.py` |
| `COBERTURAS_GRUPOS`, `palette` | `core/leyenda.py` |
| `annotateCol4` + mosaic + mask | `services/comparacion_service.py` |
| Mosaico Landsat VALIDATOR | `services/landsat_service.py` → `GET /landsat` |
| Inspector click Col3/Col4 | `GET /identificar-clase` |

Assets:

- Regiones: `…/VECTORES/col-clasificacion-regiones-c3`
- Col3: `…/COLECCION3/INTEGRACION/integracion-regiones`
- Col4: `…/COLECCION4/clasificacion-ft`
- Landsat: `…/MOSAICOS/VALIDATOR/mosaico_landsat_{year}` (1985–2024) — mismo servicio que Validation (`GET /landsat`)

## Sistema de comentarios

### Categorías (`clasificacion`)

| Valor | Uso |
|-------|-----|
| `correction` | Propuesta de cambio (opcional `clase_sugerida`) |
| `confirmed` | Col4 correcta |
| `doubt` | Requiere segunda revisión |
| `note` | Observación libre |

### Esquema de fila

```
timestamp | lat | lon | comentario | nombre | clasificacion |
anio_contexto | clase_col3 | clase_col4 | bioma | clase_sugerida
```

Frontend: `utils/normalizeComment.js` → marcadores coloreados por categoría.

Offline: clave `gaia2026_team_comments_queue` → `POST /guardar` en orden.

## Modularización frontend

| Archivo | Responsabilidad |
|---------|-----------------|
| `App.jsx` | Orquestación estado |
| `ControlPanel.jsx` | Biomas, capas, año, filtros, modo comentario |
| `MapView.jsx` | Leaflet + tiles + cluster |
| `CommentDrawer.jsx` | Formulario + identify |
| `hooks/useTeamLayers.js` | Fetch tiles / inventario / puntos |
| `config/commentCategories.js` | Extender tipos sin tocar el mapa |

Para añadir una categoría nueva: actualizar `commentCategories.js`, el `Literal` en `models/registro.py` y el estilo del pin.

## Despliegue futuro (no requerido ahora)

- **Render**: `uvicorn backend.main:app` + `GOOGLE_CREDENTIALS` / `DATABASE_URL`.
- **Vercel**: build de `visor-team`; `API_URL` en `config/api.js` apunta al servicio Render.

Localmente los comentarios van a `backend/data/comentarios_team.json` (default `PUNTOS_BACKEND=json`). Nunca a la hoja de Validation.

## Extensiones previstas

- Dibujar polígonos / áreas de corrección (hoy: punteros + comentario).
- Hoja Google **propia** de TEAM (`GOOGLE_SHEET_ID` explícito).
- Estadísticas por bioma vía SQLite de `Statistics` (`GET /stats/bioma`).
- Filtro de marcadores por categoría / bioma / año.
- Side-by-side Col3 | Col4 (Leaflet side-by-side).
