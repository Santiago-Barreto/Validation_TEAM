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


def _bbox_polygon_geojson(bounds_geom: dict) -> dict:
    """Rectángulo del bbox como Polygon GeoJSON (fallback de máscara)."""
    ring = list((bounds_geom.get("coordinates") or [[]])[0])
    if len(ring) < 4:
        raise ValueError("Geometría bounds sin anillo usable")
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    return {"type": "Polygon", "coordinates": [ring]}


def _extract_polygon_geojson(geom: dict) -> dict | None:
    """Extrae Polygon/MultiPolygon de GeoJSON (incl. GeometryCollection)."""
    if not geom:
        return None
    t = geom.get("type")
    if t == "Polygon":
        return geom
    if t == "MultiPolygon":
        return geom
    if t == "GeometryCollection":
        polys: list[dict] = []
        for g in geom.get("geometries") or []:
            extracted = _extract_polygon_geojson(g)
            if extracted:
                polys.append(extracted)
        if not polys:
            return None
        if len(polys) == 1:
            return polys[0]
        mp: list = []
        for p in polys:
            if p["type"] == "Polygon":
                mp.append(p["coordinates"])
            else:
                mp.extend(p["coordinates"])
        return {"type": "MultiPolygon", "coordinates": mp}
    return None


def _is_usable_mask_geometry(geom: dict) -> bool:
    t = geom.get("type")
    if t == "Polygon":
        ring = (geom.get("coordinates") or [[]])[0]
        return len(ring) >= 4
    if t == "MultiPolygon":
        return any(
            poly and poly[0] and len(poly[0]) >= 4
            for poly in (geom.get("coordinates") or [])
        )
    if t == "GeometryCollection":
        return any(
            _is_usable_mask_geometry(g) for g in (geom.get("geometries") or [])
        )
    return False


def _ring_bbox_area(ring: list) -> float:
    if not ring:
        return 0.0
    lons = [float(c[0]) for c in ring]
    lats = [float(c[1]) for c in ring]
    return max(max(lats) - min(lats), 0.0) * max(max(lons) - min(lons), 0.0)


def _mask_covers_bounds(geom: dict, bounds_info: dict, min_ratio: float = 0.12) -> bool:
    """Evita máscaras degeneradas (fragmentos LineString/Polygon tras simplify)."""
    bounds_ring = (bounds_info.get("coordinates") or [[]])[0]
    bounds_area = _ring_bbox_area(bounds_ring)
    if bounds_area <= 0:
        return True

    extracted = _extract_polygon_geojson(geom)
    if not extracted:
        return False

    mask_area = 0.0
    if extracted["type"] == "Polygon":
        mask_area = _ring_bbox_area(extracted["coordinates"][0])
    else:
        for poly in extracted.get("coordinates") or []:
            if poly and poly[0]:
                mask_area = max(mask_area, _ring_bbox_area(poly[0]))

    return mask_area >= bounds_area * min_ratio


def _drop_tiny_polygons(geom: dict, bounds_info: dict, min_ratio: float = 0.01) -> dict:
    """Elimina fragmentos diminutos tras simplify que generan agujeros falsos."""
    bounds_ring = (bounds_info.get("coordinates") or [[]])[0]
    bounds_area = _ring_bbox_area(bounds_ring)
    min_area = bounds_area * min_ratio

    if geom.get("type") == "Polygon":
        return geom

    kept = [
        poly
        for poly in (geom.get("coordinates") or [])
        if poly and poly[0] and _ring_bbox_area(poly[0]) >= min_area
    ]
    if not kept:
        return _bbox_polygon_geojson(bounds_info)
    if len(kept) == 1:
        return {"type": "Polygon", "coordinates": kept[0]}
    return {"type": "MultiPolygon", "coordinates": kept}


def _geometry_for_mask(geom: ee.Geometry, bounds_info: dict) -> dict:
    """
    GeoJSON polygonal simplificado para máscara SVG.
    Si EE devuelve geometría degenerada, usa bbox.
    """
    try:
        raw = geom.getInfo()
        poly = _extract_polygon_geojson(raw)
        if poly is not None:
            ee_poly = ee.Geometry(poly)
            for err in (600, 1200, 2500, 5000):
                simplified = ee_poly.simplify(maxError=err).getInfo()
                normalized = _extract_polygon_geojson(simplified)
                if (
                    normalized
                    and _is_usable_mask_geometry(normalized)
                    and _mask_covers_bounds(normalized, bounds_info)
                ):
                    return _drop_tiny_polygons(normalized, bounds_info)
    except Exception:
        logger.debug("No se pudo simplificar máscara; usando bbox.", exc_info=True)
    return _bbox_polygon_geojson(bounds_info)


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

    cache_key = f"bounds_region_v3_{rid_int}"
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

        geom = ee.Feature(fc.first()).geometry()
        bounds_info = geom.bounds(maxError=100).getInfo()
        bbox = _leaflet_from_geojson_bounds(bounds_info)
        outline = _geometry_for_mask(geom, bounds_info)

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
