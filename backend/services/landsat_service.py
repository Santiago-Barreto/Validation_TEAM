"""
Mosaicos Landsat VALIDATOR, recortados al bioma activo (misma máscara que Col3/Col4).
"""

from __future__ import annotations

from typing import Optional

import ee
from fastapi import HTTPException

from backend.core import ee_client  # noqa: F401 — inicializa EE
from backend.core.biomas import expandir_biomas
from backend.core.cache import cache
from backend.core.paths import PATHS

BASE_COLLECTION = "projects/mapbiomas-mosaics/assets/LANDSAT/LULC/COLOMBIA/mosaics-1"

VIS_PARAMS = {
    "bands": ["swir1_median", "nir_median", "red_median"],
    "min": 0,
    "max": 5615,
    "gamma": 1,
}


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


def obtener_mosaico_landsat_url(year: int, biomas: Optional[list[str]] = None):
    """
    Genera URL de tiles Landsat (falso color SWIR1/NIR/Red).
    Si hay biomas, recorta con la máscara regional del script GEE.
    """
    year = int(year)
    biomas = biomas or []
    bio_key = "-".join(sorted(biomas)) if biomas else "nacional"
    cache_key = f"landsat_mosaico_{year}_{bio_key}_v4"

    if cache_key in cache:
        return {"url": cache[cache_key]}

    try:
        asset_path = (
            f"projects/mapbiomas-colombia/assets/MOSAICOS/VALIDATOR/"
            f"mosaico_landsat_{year}"
        )
        mosaico = ee.Image(asset_path)

        if biomas:
            mask = _mask_bioma(biomas)
            mosaico = mosaico.updateMask(mask)

        map_id = mosaico.getMapId(VIS_PARAMS)
        url = map_id["tile_fetcher"].url_format
        cache[cache_key] = url
        return {"url": url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
