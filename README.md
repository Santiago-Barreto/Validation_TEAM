# Validation TEAM (GAIA 2026)

Herramienta de **validación colaborativa** MapBiomas Colombia (Col3 vs Col4) para el equipo técnico. Misma estrategia operativa que `Validation` (FastAPI + React/Leaflet + Earth Engine + Sheets/JSON), con la **lógica del script GEE base** (biomas, versiones regionales Col4, filtro de coberturas, inspector Col3/Col4) y un **sistema de comentarios** orientado a correcciones.

> No es una copia del editor Code Editor: es el mismo flujo de decisión (bioma → mosaico → año → inspección → comentario), implementado como app web modular.

## Estructura

```
Validation_TEAM/
├── backend/                 # API FastAPI
│   ├── core/                # config, biomas, leyenda, versiones, paths, EE, Sheets
│   ├── services/            # comparación Col3/Col4 + persistencia comentarios
│   ├── routers/             # HTTP
│   ├── models/              # Pydantic Registro TEAM
│   ├── db/                  # SQLAlchemy (opcional)
│   ├── credentials.json     # service account (copiado de Validation)
│   └── data/                # fallback JSON local
├── visor-team/              # Frontend Vite + React + Leaflet
├── docs/ARCHITECTURE.md
└── README.md
```

## Arranque local (Conda + 2 terminales)

### Una vez — crear el entorno

```powershell
conda create -n validation-team python=3.13 -y
conda activate validation-team
cd D:\GAIA2026_desarrollo\Validation_TEAM
pip install -r backend\requirements.txt
```

### Terminal 1 — Backend

```powershell
conda activate validation-team
cd D:\GAIA2026_desarrollo\Validation_TEAM
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000 --app-dir .
```

API: `http://127.0.0.1:8000` · docs: `/docs`

Los comentarios viven solo en `backend/data/comentarios_team.json` (no en la hoja de Validation).

### Terminal 2 — Frontend

```powershell
cd D:\GAIA2026_desarrollo\Validation_TEAM\visor-team
npm install
npm run dev
```

Visor: `http://127.0.0.1:5173`

## Flujo de uso

1. Marcar uno o más **biomas** y pulsar **Ejecutar**.
2. Revisar inventario de assets Col4 (encontrados / faltantes).
3. Ajustar **año**, capas Col3/Col4/bordes/Landsat y filtro de coberturas.
4. Clic en el mapa para inspeccionar Col3 vs Col4; modo comentario para guardar.
5. Guardar: Corrección / Confirmado / Duda / Nota.

## Credenciales

- `backend/credentials.json` — misma service account que `Validation` (solo EE).
- Comentarios: **separados** de Validation. Default JSON local.
- Variables opcionales: ver `backend/.env.example` (`PUNTOS_BACKEND`, `GOOGLE_SHEET_ID` propio de TEAM, `DATABASE_URL`).

Para producción futura (mismo patrón Vercel + Render), no es necesario desplegar ahora: el foco es funcionalidad local.

## Documentación

Ver [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
