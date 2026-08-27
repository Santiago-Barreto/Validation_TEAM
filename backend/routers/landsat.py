"""Endpoint de mosaicos Landsat (recortados al bioma activo)."""

from typing import List, Optional

from fastapi import APIRouter, Query

from backend.services import landsat_service

router = APIRouter()


@router.get("/landsat")
def get_landsat_mosaico(
    year: int = Query(2024, ge=1985, le=2024),
    biomas: Optional[List[str]] = Query(
        None, description="Biomas visibles UI (recorta el mosaico)"
    ),
):
    return landsat_service.obtener_mosaico_landsat_url(year, biomas)
