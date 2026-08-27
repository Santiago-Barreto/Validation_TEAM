"""Endpoints MapBiomas TEAM: configuración, tiles Col3/Col4, inspector."""

from typing import List, Optional

from fastapi import APIRouter, Query

from backend.core.biomas import BIOMAS_VISIBLES, BIOMAS_INTERNOS, COLOR_POR_BIOMA
from backend.core.leyenda import leyenda_frontend
from backend.core.paths import COL3_MAX_YEAR, YEAR_MAX, YEAR_MIN
from backend.services import comparacion_service
from backend.services.landsat_service import listar_estilos_landsat

router = APIRouter()


@router.get("/configuracion")
def obtener_configuracion():
    return {
        "yearMin": YEAR_MIN,
        "yearMax": YEAR_MAX,
        "col3MaxYear": COL3_MAX_YEAR,
        "biomasVisibles": BIOMAS_VISIBLES,
        "biomasInternos": BIOMAS_INTERNOS,
        "coloresBioma": COLOR_POR_BIOMA,
        "leyenda": leyenda_frontend(),
        "landsatStyles": listar_estilos_landsat(),
        "capas": [
            {
                "id": "col4",
                "label": "Colección 4",
                "defaultShow": True,
                "zIndex": 40,
            },
            {
                "id": "col3",
                "label": "Colección 3",
                "defaultShow": False,
                "zIndex": 30,
            },
            {
                "id": "bordes",
                "label": "Bordes biomas",
                "defaultShow": False,
                "zIndex": 50,
            },
            {
                "id": "landsat",
                "label": "Landsat mosaico 🛰️",
                "defaultShow": False,
                "zIndex": 5,
            },
        ],
    }


@router.get("/inventario")
def inventario(biomas: List[str] = Query(..., description="Biomas visibles UI")):
    return comparacion_service.inventario_assets(biomas)


@router.get("/tiles/col4")
def tiles_col4(
    year: int = Query(...),
    biomas: List[str] = Query(...),
    class_id: Optional[str] = Query(None),
):
    return comparacion_service.obtener_tile_col4(biomas, year, class_id)


@router.get("/tiles/col3")
def tiles_col3(
    year: int = Query(...),
    biomas: List[str] = Query(...),
    class_id: Optional[str] = Query(None),
):
    return comparacion_service.obtener_tile_col3(biomas, year, class_id)


@router.get("/tiles/bordes")
def tiles_bordes(biomas: List[str] = Query(...)):
    return comparacion_service.obtener_tile_bordes(biomas)


@router.get("/identificar-clase")
def identificar_clase(
    lat: float,
    lon: float,
    year: int = Query(...),
    biomas: Optional[List[str]] = Query(None),
):
    return comparacion_service.identificar_punto(lat, lon, year, biomas)
