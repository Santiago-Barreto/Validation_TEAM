"""
Bounds / geometría simplificada de regiones (EE) para zoom del mapa.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import ee
from fastapi import HTTPException

from backend.core import ee_client  # noqa: F401
from backend.core.biomas import expandir_biomas
from backend.core.cache import cache
from backend.core.paths import PATHS

logger = logging.getLogger(__name__)


def _leaflet_from_geojson_bounds(bounds_geom: dict) -> dict[str, Any]:
    """Convierte Polygon de .bounds() a bbox Leaflet [[s,w],[n,e]]."""
    coords = (bounds_geom.get("coordinates") or [[]])[0]
    if not coords:
        raise ValueError("Geometría sin coordenadas")
    lons = [float(c[0]) for c in coords]
    lats = [float(c[1]) for c in coords]
    south, north = min(lats), max(lats)
    west, east = min(lons), max(lons)
    return {
        "south": south,
        "west": west,
        "north": north,
        "east": east,
        "leaflet": [[south, west], [north, east]],
        "center": [(south + north) / 2, (west + east) / 2],
    }


def bounds_region(region_id: str) -> dict[str, Any]:
    """Bbox + GeoJSON simplificado de una región (id_regionC)."""
    rid = str(region_id).strip()
    try:
        rid_int = int(float(rid))
    except (TypeError, ValueError) as e:
        raise HTTPException(status_code=400, detail="region_id inválido") from e

    cache_key = f"bounds_region_{rid_int}"
    if cache_key in cache:
        return cache[cache_key]

    try:
        fc = ee.FeatureCollection(PATHS["region_vector"]).filter(
            ee.Filter.eq("id_regionC", rid_int)
        )
        n = int(fc.size().getInfo() or 0)
        if n == 0:
            raise HTTPException(
                status_code=404, detail=f"Región {rid_int} no encontrada en vector"
            )

        geom = fc.geometry()
        bounds_info = geom.bounds(maxError=100).getInfo()
        bbox = _leaflet_from_geojson_bounds(bounds_info)
        # Contorno ligero para resaltar en el mapa
        outline = geom.simplify(maxError=500).getInfo()

        props = (
            ee.Feature(fc.first())
            .toDictionary(["bioma", "id_regionC"])
            .getInfo()
            or {}
        )
        out = {
            "region_id": str(rid_int),
            "bioma": props.get("bioma"),
            **bbox,
            "geojson": {
                "type": "Feature",
                "properties": {
                    "id_regionC": rid_int,
                    "bioma": props.get("bioma"),
                },
                "geometry": outline,
            },
        }
        cache[cache_key] = out
        return out
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error bounds región %s", rid_int)
        raise HTTPException(status_code=500, detail=str(e)) from e


def bounds_biomas(biomas: list[str]) -> dict[str, Any]:
    """Bbox del conjunto de biomas ejecutados (para volver al encuadre)."""
    if not biomas:
        raise HTTPException(status_code=400, detail="Selecciona al menos un bioma.")
    internos = expandir_biomas(biomas)
    cache_key = f"bounds_bioma_{'-'.join(sorted(internos))}"
    if cache_key in cache:
        return cache[cache_key]

    try:
        fc = ee.FeatureCollection(PATHS["region_vector"]).filter(
            ee.Filter.inList("bioma", internos)
        )
        n = int(fc.size().getInfo() or 0)
        if n == 0:
            raise HTTPException(
                status_code=404, detail="Sin regiones para esos biomas"
            )
        # No unir polígonos detallados (Andes > 2M edges). Solo bbox por feature.
        boxes = fc.map(
            lambda f: ee.Feature(ee.Feature(f).geometry().bounds(maxError=2000))
        )
        bounds_info = boxes.geometry().bounds(maxError=100).getInfo()
        bbox = _leaflet_from_geojson_bounds(bounds_info)
        out = {
            "biomas": biomas,
            "biomas_internos": internos,
            **bbox,
            "geojson": None,
        }
        cache[cache_key] = out
        return out
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error bounds biomas")
        raise HTTPException(status_code=500, detail=str(e)) from e
