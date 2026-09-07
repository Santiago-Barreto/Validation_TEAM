import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.core.runtime_paths import get_static_dir, is_frozen
from backend.routers import auth, landsat, mapbiomas, puntos, solar, stats

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
    logger.info("Validation TEAM ready.")
    yield
    dispose_engine()


app = FastAPI(
    title="GAIA 2026 — Validation TEAM API",
    version="1.0.0",
    description="MapBiomas Colombia Col3/Col4 validation API for the TEAM workflow.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(mapbiomas.router, tags=["MapBiomas"])
app.include_router(landsat.router, tags=["Landsat"])
app.include_router(stats.router, tags=["Statistics"])
app.include_router(puntos.router, tags=["Comments"])
app.include_router(solar.router, tags=["Solar"])


@app.get("/health")
def health_live():
    return {"status": "ok", "service": "validation-team"}


@app.get("/ready")
def health_ready():
    from backend.services.puntos_storage import readiness_info

    body = readiness_info()
    ok = body.get("ready", True)
    return JSONResponse(content=body, status_code=200 if ok else 503)


def _mount_static_ui() -> None:
    if not (is_frozen() or os.environ.get("SERVE_STATIC", "").strip() == "1"):
        return
    static_dir = get_static_dir()
    if static_dir is None:
        logger.warning("SERVE_STATIC=1 but frontend/dist is missing.")
        return

    assets_dir = static_dir / "assets"
    if assets_dir.is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=str(assets_dir)),
            name="visor-assets",
        )

    index_html = static_dir / "index.html"

    @app.get("/", include_in_schema=False)
    def serve_index():
        return FileResponse(index_html)

    logger.info("Serving static UI from %s", static_dir)


_mount_static_ui()
