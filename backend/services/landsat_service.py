"""
Mosaicos Landsat VALIDATOR, recortados al bioma activo (misma máscara que Col3/Col4).
"""

from __future__ import annotations

from typing import Any, Optional

import ee
from fastapi import HTTPException

from backend.core import ee_client  # noqa: F401 — inicializa EE
from backend.core.biomas import expandir_biomas
from backend.core.cache import cache
from backend.core.paths import PATHS

LANDSAT_STYLES: dict[str, dict[str, Any]] = {
    "green": {
        "id": "green",
        "label": "Mosaic Green",
        "vis": {
            "bands": ["swir1_median", "nir_median", "red_median"],
            "gain": [0.08, 0.06, 0.2],
        },
    },
    "red": {
        "id": "red",
        "label": "Mosaic Red",
        "vis": {
            "bands": ["nir_median", "swir1_median", "red_median"],
            "gain": [0.06, 0.08, 0.2],
        },
    },
    "gamma": {
        "id": "gamma",
        "label": "Mosaic Gamma",
        "vis": {
            "bands": ["nir_median", "swir1_median", "red_median"],
            "gain": [0.06, 0.08, 0.21],
            "gamma": 0.45,
        },
    },
}

DEFAULT_LANDSAT_STYLE = "green"


def listar_estilos_landsat() -> list[dict[str, str]]:
    return [
        {"id": s["id"], "label": s["label"]} for s in LANDSAT_STYLES.values()
    ]


def _mask_bioma(biomas: list[str]) -> ee.Image:
    internos = expandir_biomas(biomas)
    if not internos:
        raise HTTPException(status_code=400, detail="Selecciona al menos un bioma.")
    region_class = ee.FeatureCollection(PATHS["region_vector"]).filter(
        ee.Filter.inList("bioma", internos)
    )
    return ee.Image(
        region_class.reduceToImage(["id_regionC"], ee.Reducer.first())
    ).gt(0)


def obtener_mosaico_landsat_url(
    year: int,
    biomas: Optional[list[str]] = None,
    style: str = DEFAULT_LANDSAT_STYLE,
):
    year = int(year)
    biomas = biomas or []
    style_key = (style or DEFAULT_LANDSAT_STYLE).strip().lower()
    if style_key not in LANDSAT_STYLES:
        raise HTTPException(
            status_code=400,
            detail=f"Estilo Landsat desconocido: {style_key}",
        )

    bio_key = "-".join(sorted(biomas)) if biomas else "nacional"
    cache_key = f"landsat_{year}_{bio_key}_{style_key}_v5"

    if cache_key in cache:
        return {
            "url": cache[cache_key],
            "style": style_key,
            "cached": True,
        }

    try:
        asset_path = (
            f"projects/mapbiomas-colombia/assets/MOSAICOS/VALIDATOR/"
            f"mosaico_landsat_{year}"
        )
        mosaico = ee.Image(asset_path)

        if biomas:
            mask = _mask_bioma(biomas)
            mosaico = mosaico.updateMask(mask)

        map_id = mosaico.getMapId(LANDSAT_STYLES[style_key]["vis"])
        url = map_id["tile_fetcher"].url_format
        cache[cache_key] = url
        return {"url": url, "style": style_key, "cached": False}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


def prefetch_landsat_styles(
    year: int,
    biomas: Optional[list[str]] = None,
    primary: str = DEFAULT_LANDSAT_STYLE,
) -> None:
    """Warm cache for alternate styles (best-effort)."""
    for style_id in LANDSAT_STYLES:
        if style_id == primary:
            continue
        try:
            obtener_mosaico_landsat_url(year, biomas, style_id)
        except Exception:
            continue
