"""Endpoint de mosaicos Landsat (recortados al bioma activo)."""

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Query

from backend.services import landsat_service

router = APIRouter()


@router.get("/landsat/styles")
def list_landsat_styles():
    return {"styles": landsat_service.listar_estilos_landsat()}


@router.get("/landsat")
def get_landsat_mosaico(
    background_tasks: BackgroundTasks,
    year: int = Query(2024, ge=1985, le=2024),
    biomas: Optional[List[str]] = Query(
        None, description="Biomas visibles UI (recorta el mosaico)"
    ),
    style: str = Query(
        landsat_service.DEFAULT_LANDSAT_STYLE,
        description="green | red | gamma",
    ),
    prefetch: bool = Query(True, description="Warm other styles in background"),
):
    result = landsat_service.obtener_mosaico_landsat_url(year, biomas, style)
    if prefetch and not result.get("cached"):
        background_tasks.add_task(
            landsat_service.prefetch_landsat_styles,
            year,
            biomas,
            style,
        )
    return result
