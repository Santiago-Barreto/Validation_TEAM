"""
backend/main.py — GAIA 2026 Validation TEAM API.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.routers import landsat, mapbiomas, puntos, stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from backend.services.puntos_storage import validate_startup_settings
    from backend.db.session import configure_engine, init_db, dispose_engine

    validate_startup_settings()
    configure_engine()
    init_db()
    logger.info("Validation TEAM listo (Sheets bajo demanda).")
    yield
    dispose_engine()


app = FastAPI(
    title="GAIA 2026 — Validation TEAM API",
    version="1.0.0",
    description=(
        "Comparación Col3/Col4 por bioma + sistema de comentarios "
        "para correcciones del equipo de validación."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mapbiomas.router, tags=["MapBiomas"])
app.include_router(landsat.router, tags=["Landsat"])
app.include_router(stats.router, tags=["Estadísticas"])
app.include_router(puntos.router, tags=["Comentarios"])


@app.get("/health")
def health_live():
    return {"status": "ok", "service": "validation-team"}


@app.get("/ready")
def health_ready():
    from backend.services.puntos_storage import readiness_info

    body = readiness_info()
    ok = body.get("ready", True)
    return JSONResponse(content=body, status_code=200 if ok else 503)
