"""Endpoint de estadísticas agregadas por bioma / región (proyecto Statistics)."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.services import region_bounds_service, stats_service

router = APIRouter()


@router.get("/stats/bioma")
def stats_bioma(
    biomas: List[str] = Query(..., description="Biomas visibles UI (ej. Amazonía)"),
):
    """Serie temporal del bioma + lista de regiones (versión deseada)."""
    return stats_service.estadisticas_bioma(biomas)


@router.get("/stats/bioma/heatmap")
def stats_bioma_heatmap(
    biomas: List[str] = Query(...),
    class_id: str = Query(..., description="Cobertura ID03 / 3 / etc."),
):
    """Heatmap Δha región×periodo para una cobertura (payload liviano)."""
    return stats_service.heatmap_bioma(biomas, class_id)


@router.get("/stats/region")
def stats_region(
    region_id: str = Query(..., description="id_regionC (ej. 30201)"),
):
    """Serie temporal de una región con la versión de VERSIONES_DESEADAS."""
    return stats_service.estadisticas_region(region_id)


@router.get("/stats/bounds")
def stats_bounds(
    region_id: Optional[str] = Query(None, description="Zoom a una región"),
    biomas: Optional[List[str]] = Query(None, description="Zoom al bioma completo"),
):
    """Bbox (+ geojson de región) para animar el mapa al cambiar el ámbito."""
    if region_id:
        return region_bounds_service.bounds_region(region_id)
    if biomas:
        return region_bounds_service.bounds_biomas(biomas)
    raise HTTPException(
        status_code=400, detail="Indica region_id o biomas para el encuadre."
    )
