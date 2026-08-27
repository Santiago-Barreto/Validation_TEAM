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

        # Cobertura nacional (Colombia) vs biomas activos del visor.
        # Comentarios solo si hay biomas ejecutados y el punto cae en ellos.
        if region_info:
            en_colombia = True
            en_bioma_activo = bool(biomas)
        else:
            en_colombia = False
            try:
                n_col = int(
                    ee.FeatureCollection(PATHS["region_vector"])
                    .filterBounds(point)
                    .size()
                    .getInfo()
                    or 0
                )
                en_colombia = n_col > 0
            except Exception:
                logger.debug("No se pudo verificar cobertura Colombia", exc_info=True)
                en_colombia = _bbox_colombia(lat, lon)
            en_bioma_activo = False

        permite_comentario = bool(biomas) and en_colombia and en_bioma_activo
        if not biomas:
            mensaje_comentario = (
                "Ejecuta al menos un bioma antes de crear comentarios."
            )
        elif not en_colombia:
            mensaje_comentario = (
                "Solo se pueden crear comentarios dentro del territorio de Colombia."
            )
        elif not en_bioma_activo:
            mensaje_comentario = (
                "El punto está fuera de los biomas ejecutados. "
                "Ejecuta el bioma correspondiente para comentar aquí."
            )
        else:
            mensaje_comentario = ""

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

        base = {
            "lat": lat,
            "lon": lon,
            "year": year,
            "en_colombia": en_colombia,
            "en_bioma_activo": en_bioma_activo,
            "permite_comentario": permite_comentario,
            "mensaje_comentario": mensaje_comentario,
            "region": region_info or None,
        }

        if v4 is None:
            return {
                **base,
                "fuera_de_area": True,
            }

        cambio = None
        if not include_col3 or v3 is None:
            cambio = "solo_col4"
        elif int(v3) == int(v4):
            cambio = "sin_cambios"
        else:
            cambio = "detectado"

        return {
            **base,
            "fuera_de_area": False,
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


def _bbox_colombia(lat: float, lon: float) -> bool:
    return -5.0 <= float(lat) <= 13.6 and -82.0 <= float(lon) <= -66.0


def evaluar_ubicacion_comentario(
    lat: float, lon: float, biomas: Optional[list[str]] = None
) -> dict[str, Any]:
    """
    Validación ligera (solo vector de regiones, sin mosaicos Col3/Col4).
    Pensada para abrir el formulario de comentario sin esperar identify completo.
    """
    lat_f, lon_f = float(lat), float(lon)
    base: dict[str, Any] = {
        "lat": lat_f,
        "lon": lon_f,
        "en_colombia": False,
        "en_bioma_activo": False,
        "permite_comentario": False,
        "mensaje_comentario": "",
        "region": None,
    }

    if not biomas:
        base["mensaje_comentario"] = (
            "Ejecuta al menos un bioma antes de crear comentarios."
        )
        return base

    if not _bbox_colombia(lat_f, lon_f):
        base["mensaje_comentario"] = (
            "Solo se pueden crear comentarios dentro del territorio de Colombia."
        )
        return base

    internos = expandir_biomas(biomas)
    if not internos:
        base["mensaje_comentario"] = "Selecciona al menos un bioma ejecutado."
        return base

    point = ee.Geometry.Point([lon_f, lat_f])
    try:
        hit = _region_class(internos).filterBounds(point)
        # Un solo round-trip EE: tamaño + props de la región
        packed = (
            ee.Dictionary(
                {
                    "n": hit.size(),
                    "props": ee.Feature(hit.first()).toDictionary(
                        ["bioma", "id_regionC", "id_region"]
                    ),
                }
            ).getInfo()
            or {}
        )
        n_bio = int(packed.get("n") or 0)
        if n_bio > 0:
            props = packed.get("props") or {}
            rid = props.get("id_regionC")
            base.update(
                {
                    "en_colombia": True,
                    "en_bioma_activo": True,
                    "permite_comentario": True,
                    "mensaje_comentario": "",
                    "region": {
                        "bioma": props.get("bioma"),
                        "id_regionC": rid,
                        "id_region": props.get("id_region"),
                        "interprete_responsable": interprete_de_region(rid),
                    },
                }
            )
            return base

        n_col = int(
            ee.FeatureCollection(PATHS["region_vector"])
            .filterBounds(point)
            .size()
            .getInfo()
            or 0
        )
        en_colombia = n_col > 0
        base["en_colombia"] = en_colombia
        if not en_colombia:
            base["mensaje_comentario"] = (
                "Solo se pueden crear comentarios dentro del territorio de Colombia."
            )
        else:
            base["mensaje_comentario"] = (
                "El punto está fuera de los biomas ejecutados. "
                "Ejecuta el bioma correspondiente para comentar aquí."
            )
        return base
    except Exception as e:
        logger.exception("Error validando ubicación de comentario")
        raise HTTPException(
            status_code=503, detail=f"No se pudo validar la ubicación: {e}"
        ) from e


def validar_ubicacion_comentario(
    lat: float, lon: float, biomas: Optional[list[str]] = None
) -> None:
    """Raises HTTPException if the point cannot receive a TEAM comment."""
    result = evaluar_ubicacion_comentario(lat, lon, biomas)
    if not result.get("permite_comentario"):
        raise HTTPException(
            status_code=400,
            detail=result.get("mensaje_comentario")
            or "Ubicación no válida para comentarios.",
        )


def evaluar_ubicaciones_lote(
    puntos: list[tuple[float, float]],
    biomas: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """
    Valida N puntos en un solo round-trip a Earth Engine.
    puntos: lista de (lat, lon). Devuelve una entrada por punto (mismo orden).
    """
    if not puntos:
        return []

    if not biomas:
        msg = "Ejecuta al menos un bioma antes de crear comentarios."
        return [
            {
                "lat": float(lat),
                "lon": float(lon),
                "permite_comentario": False,
                "mensaje_comentario": msg,
                "region": None,
            }
            for lat, lon in puntos
        ]

    internos = expandir_biomas(biomas)
    if not internos:
        msg = "Selecciona al menos un bioma ejecutado."
        return [
            {
                "lat": float(lat),
                "lon": float(lon),
                "permite_comentario": False,
                "mensaje_comentario": msg,
                "region": None,
            }
            for lat, lon in puntos
        ]

    # Pre-filtro bbox (sin EE)
    prelim: list[dict[str, Any]] = []
    pendientes: list[tuple[int, float, float]] = []
    for i, (lat, lon) in enumerate(puntos):
        lat_f, lon_f = float(lat), float(lon)
        if not _bbox_colombia(lat_f, lon_f):
            prelim.append(
                {
                    "lat": lat_f,
                    "lon": lon_f,
                    "permite_comentario": False,
                    "mensaje_comentario": (
                        "Solo se pueden crear comentarios dentro del "
                        "territorio de Colombia."
                    ),
                    "region": None,
                }
            )
        else:
            prelim.append({})  # placeholder
            pendientes.append((i, lat_f, lon_f))

    if not pendientes:
        return prelim

    try:
        region = _region_class(internos)
        feats = [
            ee.Feature(
                ee.Geometry.Point([lon, lat]),
                {"idx": idx, "lat": lat, "lon": lon},
            )
            for idx, lat, lon in pendientes
        ]
        fc = ee.FeatureCollection(feats)

        def _annotate(f: ee.Feature) -> ee.Feature:
            hit = region.filterBounds(f.geometry())
            first = ee.Feature(hit.first())
            return f.set(
                {
                    "n": hit.size(),
                    "bioma": first.get("bioma"),
                    "id_regionC": first.get("id_regionC"),
                    "id_region": first.get("id_region"),
                }
            )

        annotated = fc.map(_annotate).getInfo() or {}
        features = annotated.get("features") or []
        by_idx: dict[int, dict[str, Any]] = {}
        for feat in features:
            props = feat.get("properties") or {}
            idx = int(props.get("idx"))
            n_bio = int(props.get("n") or 0)
            lat_f = float(props.get("lat"))
            lon_f = float(props.get("lon"))
            if n_bio > 0:
                rid = props.get("id_regionC")
                by_idx[idx] = {
                    "lat": lat_f,
                    "lon": lon_f,
                    "permite_comentario": True,
                    "mensaje_comentario": "",
                    "region": {
                        "bioma": props.get("bioma"),
                        "id_regionC": rid,
                        "id_region": props.get("id_region"),
                        "interprete_responsable": interprete_de_region(rid),
                    },
                }
            else:
                by_idx[idx] = {
                    "lat": lat_f,
                    "lon": lon_f,
                    "permite_comentario": False,
                    "mensaje_comentario": (
                        "El punto está fuera de los biomas ejecutados. "
                        "Ejecuta el bioma correspondiente para comentar aquí."
                    ),
                    "region": None,
                }

        for idx, lat_f, lon_f in pendientes:
            prelim[idx] = by_idx.get(
                idx,
                {
                    "lat": lat_f,
                    "lon": lon_f,
                    "permite_comentario": False,
                    "mensaje_comentario": "No se pudo validar la ubicación.",
                    "region": None,
                },
            )
        return prelim
    except Exception as e:
        logger.exception("Error validando lote de comentarios")
        raise HTTPException(
            status_code=503, detail=f"No se pudo validar la ubicación: {e}"
        ) from e
