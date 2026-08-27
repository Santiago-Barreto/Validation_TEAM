"""
Servicio Col3 / Col4 por bioma — misma lógica que el script GEE base.

Construye mosaicos regionales Col4 filtrados por VERSIONES_DESEADAS,
integra Col3 por región, aplica máscara de bioma y genera tiles XYZ.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import ee
from fastapi import HTTPException

from backend.core import ee_client  # noqa: F401 — inicializa EE
from backend.core.biomas import COLOR_POR_BIOMA, expandir_biomas
from backend.core.cache import cache
from backend.core.leyenda import PALETTE, VIS_MAX, VIS_MIN, nombre_clase
from backend.core.paths import BANDAS_COL4, COL3_MAX_YEAR, PATHS, YEAR_MAX, YEAR_MIN
from backend.core.versiones_col4 import VERSIONES_DESEADAS
from backend.services.asignacion_excel import interprete_de_region

logger = logging.getLogger(__name__)


def year_band(year: int) -> str:
    return f"classification_{int(year)}"


def _annotate_col4(img: ee.Image) -> ee.Image:
    parts = ee.String(img.id()).split("-")
    reg = parts.get(-2)
    ver = parts.get(-1)
    return img.toByte().set(
        {
            "r": ee.Number.parse(reg),
            "v": ee.Number.parse(ver),
            "tag": ee.String("COLOMBIA-").cat(reg).cat("-").cat(ver),
        }
    )


def _region_class(biomas_internos: list[str]) -> ee.FeatureCollection:
    return ee.FeatureCollection(PATHS["region_vector"]).filter(
        ee.Filter.inList("bioma", biomas_internos)
    )


def _col4_selected(region_class: ee.FeatureCollection) -> ee.ImageCollection:
    ids = region_class.aggregate_array("id_regionC")
    col4_all = ee.ImageCollection(PATHS["col4_folder"]).map(_annotate_col4)
    return (
        col4_all.filter(ee.Filter.inList("tag", VERSIONES_DESEADAS))
        .filter(ee.Filter.inList("r", ids))
        .map(lambda img: img.select(BANDAS_COL4).toByte())
    )


def _mask_from_region(region_class: ee.FeatureCollection) -> ee.Image:
    return (
        ee.Image(region_class.reduceToImage(["id_regionC"], ee.Reducer.first())).gt(0)
    )


def _filtrar_coberturas(image: ee.Image, class_ids: Optional[list[int]]) -> ee.Image:
    if not class_ids:
        return image
    mask_cob = ee.Image(0)
    for cid in class_ids:
        mask_cob = mask_cob.Or(image.eq(int(cid)))
    return image.updateMask(mask_cob)


def _parse_class_ids(class_id: Optional[str]) -> Optional[list[int]]:
    if class_id is None or str(class_id).strip() == "":
        return None
    return [int(x) for x in str(class_id).split(",") if str(x).strip()]


def _vis_params() -> dict:
    # EE getMapId espera hex sin # en algunos contextos; usamos sin #
    palette = [c.lstrip("#") for c in PALETTE]
    return {"min": VIS_MIN, "max": VIS_MAX, "palette": palette}


def _tile_url(image: ee.Image, cache_key: str) -> str:
    if cache_key in cache:
        return cache[cache_key]
    map_id = image.getMapId(_vis_params())
    url = map_id["tile_fetcher"].url_format
    cache[cache_key] = url
    return url


def inventario_assets(biomas: list[str]) -> dict[str, Any]:
    """Lista tags Col4 encontrados / faltantes para los biomas seleccionados."""
    internos = expandir_biomas(biomas)
    if not internos:
        raise HTTPException(status_code=400, detail="Selecciona al menos un bioma.")

    region_class = _region_class(internos)
    col4_selected = _col4_selected(region_class)

    try:
        tags = col4_selected.aggregate_array("tag").sort().getInfo() or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inventariando Col4: {e}") from e

    encontrados = set(tags)
    faltantes = [t for t in VERSIONES_DESEADAS if t not in encontrados]

    return {
        "biomas": internos,
        "encontrados": tags,
        "faltantes": faltantes,
        "total_encontrados": len(tags),
        "total_faltantes": len(faltantes),
    }


def obtener_tile_col4(
    biomas: list[str],
    year: int,
    class_id: Optional[str] = None,
) -> dict[str, str]:
    internos = expandir_biomas(biomas)
    if not internos:
        raise HTTPException(status_code=400, detail="Selecciona al menos un bioma.")

    year = max(YEAR_MIN, min(int(year), YEAR_MAX))
    classes = _parse_class_ids(class_id)
    cache_key = f"col4_vis2_{'-'.join(internos)}_{year}_{class_id or 'all'}"

    try:
        region_class = _region_class(internos)
        mask = _mask_from_region(region_class)
        mosaic = ee.Image(_col4_selected(region_class).mosaic())
        band = mosaic.select(year_band(year)).updateMask(mask)
        band = _filtrar_coberturas(band, classes)
        url = _tile_url(band, cache_key)
        return {"url": url, "year": year, "layer": "col4"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error tile Col4")
        raise HTTPException(status_code=500, detail=str(e)) from e


def obtener_tile_col3(
    biomas: list[str],
    year: int,
    class_id: Optional[str] = None,
) -> dict[str, Any]:
    internos = expandir_biomas(biomas)
    if not internos:
        raise HTTPException(status_code=400, detail="Selecciona al menos un bioma.")

    year = int(year)
    if year > COL3_MAX_YEAR:
        return {
            "url": None,
            "year": year,
            "layer": "col3",
            "available": False,
            "reason": f"Col3 solo hasta {COL3_MAX_YEAR}",
        }

    year = max(YEAR_MIN, min(year, COL3_MAX_YEAR))
    classes = _parse_class_ids(class_id)
    cache_key = f"col3_vis2_{'-'.join(internos)}_{year}_{class_id or 'all'}"

    try:
        region_class = _region_class(internos)
        ids = region_class.aggregate_array("id_regionC")
        mask = _mask_from_region(region_class)
        col4_mosaic = ee.Image(_col4_selected(region_class).mosaic())
        col3_mosaic = ee.Image(
            ee.ImageCollection(PATHS["col3"])
            .filter(ee.Filter.inList("region", ids))
            .mosaic()
        )
        band = (
            col3_mosaic.select(year_band(year))
            .updateMask(mask)
            .updateMask(col4_mosaic.select(0).mask())
        )
        band = _filtrar_coberturas(band, classes)
        url = _tile_url(band, cache_key)
        return {"url": url, "year": year, "layer": "col3", "available": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error tile Col3")
        raise HTTPException(status_code=500, detail=str(e)) from e


def obtener_tile_bordes(biomas: list[str]) -> dict[str, str]:
    internos = expandir_biomas(biomas)
    if not internos:
        raise HTTPException(status_code=400, detail="Selecciona al menos un bioma.")

    cache_key = f"bordes_{'-'.join(internos)}"
    if cache_key in cache:
        return {"url": cache[cache_key]}

    try:
        region_class = _region_class(internos)
        color_dict = ee.Dictionary(COLOR_POR_BIOMA)

        styled = ee.Image(
            region_class.map(
                lambda f: f.set(
                    "style",
                    {
                        "color": color_dict.get(f.get("bioma"), "#000000"),
                        "width": 2,
                        "fillColor": "00000000",
                    },
                )
            ).style(styleProperty="style")
        )
        map_id = styled.getMapId({})
        url = map_id["tile_fetcher"].url_format
        cache[cache_key] = url
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


def identificar_punto(
    lat: float,
    lon: float,
    year: int,
    biomas: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Compara Col3 vs Col4 en un punto (inspector del script GEE)."""
    year = max(YEAR_MIN, min(int(year), YEAR_MAX))
    point = ee.Geometry.Point([lon, lat])
    band = year_band(year)

    try:
        if biomas:
            internos = expandir_biomas(biomas)
            region_class = _region_class(internos)
            col4_ic = _col4_selected(region_class)
            col4 = ee.Image(col4_ic.mosaic())
            ids = region_class.aggregate_array("id_regionC")
            col3 = ee.Image(
                ee.ImageCollection(PATHS["col3"])
                .filter(ee.Filter.inList("region", ids))
                .mosaic()
            )
        else:
            internos = None
            region_class = ee.FeatureCollection(PATHS["region_vector"])
            col4_ic = (
                ee.ImageCollection(PATHS["col4_folder"])
                .map(_annotate_col4)
                .filter(ee.Filter.inList("tag", VERSIONES_DESEADAS))
                .map(lambda img: img.select(BANDAS_COL4).toByte())
            )
            col4 = ee.Image(col4_ic.mosaic())
            col3 = ee.Image(ee.ImageCollection(PATHS["col3"]).mosaic())

        # Región de clasificación bajo el clic
        region_info: dict[str, Any] = {}
        hit = region_class.filterBounds(point)
        try:
            n = int(hit.size().getInfo() or 0)
            if n > 0:
                props = (
                    ee.Feature(hit.first())
                    .toDictionary(["bioma", "id_regionC", "id_region"])
                    .getInfo()
                    or {}
                )
                rid = props.get("id_regionC")
                region_info = {
                    "bioma": props.get("bioma"),
                    "id_regionC": rid,
                    "id_region": props.get("id_region"),
                    # Columna A del Excel local (no depende del vector EE ni de Statistics)
                    "interprete_responsable": interprete_de_region(rid),
                }
                if rid is not None:
                    tags = (
                        col4_ic.filter(ee.Filter.eq("r", int(rid)))
                        .aggregate_array("tag")
                        .getInfo()
                        or []
                    )
                    if tags:
                        region_info["tag_col4"] = tags[0]
        except Exception:
            logger.debug("Sin feature de región en el punto", exc_info=True)

        stack = col4.select([band], ["v4"])
        include_col3 = year <= COL3_MAX_YEAR
        if include_col3:
            stack = stack.addBands(col3.select([band], ["v3"]))

        info = stack.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=30,
            bestEffort=True,
        ).getInfo()

        v4 = info.get("v4")
        v3 = info.get("v3") if include_col3 else None

        if v4 is None:
            return {
                "lat": lat,
                "lon": lon,
                "year": year,
                "fuera_de_area": True,
                "region": region_info or None,
            }

        cambio = None
        if not include_col3 or v3 is None:
            cambio = "solo_col4"
        elif int(v3) == int(v4):
            cambio = "sin_cambios"
        else:
            cambio = "detectado"

        return {
            "lat": lat,
            "lon": lon,
            "year": year,
            "fuera_de_area": False,
            "region": region_info or None,
            "col3": {
                "id": v3,
                "nombre": nombre_clase(v3) if v3 is not None else "N/A",
            },
            "col4": {
                "id": v4,
                "nombre": nombre_clase(v4),
            },
            "cambio": cambio,
        }
    except Exception as e:
        logger.exception("Error identificar punto")
        raise HTTPException(status_code=500, detail=str(e)) from e
