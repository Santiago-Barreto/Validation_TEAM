"""Endpoints de comentarios / correcciones del equipo."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.core.auth import AuthUser, require_user
from backend.models.registro import LoteComentarios, Registro
from backend.models.resolver import ResolverComentario
from backend.services import puntos_storage

logger = logging.getLogger(__name__)

router = APIRouter()

# Bbox aproximado de Colombia (sin Earth Engine)
_LAT_MIN, _LAT_MAX = -5.0, 13.6
_LON_MIN, _LON_MAX = -82.0, -66.0


def _en_colombia(lat: float, lon: float) -> bool:
    return _LAT_MIN <= float(lat) <= _LAT_MAX and _LON_MIN <= float(lon) <= _LON_MAX


@router.get("/puntos")
def leer_registros():
    try:
        return puntos_storage.list_registros()
    except RuntimeError as e:
        logger.warning("%s", e)
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception:
        logger.exception("Error al listar registros")
        raise HTTPException(status_code=500, detail="Error al consultar los registros")


@router.post("/guardar")
def guardar_registro(
    r: Registro,
    biomas: Optional[List[str]] = Query(
        None,
        description="Biomas ejecutados en el visor (visibles UI)",
    ),
    user: AuthUser = Depends(require_user),
):
    try:
        bio_list = list(biomas) if biomas else ([r.bioma] if r.bioma else [])
        if not bio_list:
            raise HTTPException(
                status_code=400,
                detail="Ejecuta al menos un bioma antes de crear comentarios.",
            )
        if not _en_colombia(r.lat, r.lon):
            raise HTTPException(
                status_code=400,
                detail="Solo se pueden crear comentarios dentro de Colombia.",
            )

        r.creado_por = user.email
        r.foto_url = (user.picture or "").strip() or (r.foto_url or "")
        r.nombre = (user.name or user.email or "").strip()
        if not (r.bioma or "").strip():
            r.bioma = bio_list[0]
        grupo_id = puntos_storage.append_registro(r)
        return {
            "status": "success",
            "creado_por": user.email,
            "grupo_id": grupo_id,
        }
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.warning("%s", e)
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error guardando registro: %s", e)
        raise HTTPException(status_code=500, detail="Error al persistir la informacion")


@router.post("/guardar-lote")
def guardar_lote(
    body: LoteComentarios,
    biomas: Optional[List[str]] = Query(
        None,
        description="Biomas ejecutados en el visor (visibles UI)",
    ),
    user: AuthUser = Depends(require_user),
):
    """Guarda N puntos con el mismo comentario (sin Earth Engine)."""
    try:
        bio_list = list(biomas) if biomas else ([body.bioma] if body.bioma else [])
        if not bio_list:
            raise HTTPException(
                status_code=400,
                detail="Ejecuta al menos un bioma antes de crear comentarios.",
            )

        registros: list[Registro] = []
        rechazados = 0
        for p in body.puntos:
            if not _en_colombia(p.lat, p.lon):
                rechazados += 1
                continue
            registros.append(
                Registro(
                    lat=p.lat,
                    lon=p.lon,
                    nombre=(user.name or user.email or "").strip(),
                    comentario=body.comentario.strip(),
                    anio_contexto=body.anio_contexto,
                    bioma=(body.bioma or bio_list[0]),
                    clase_sugerida=body.clase_sugerida,
                    creado_por=user.email,
                    foto_url=(user.picture or "").strip() or (body.foto_url or ""),
                    grupo_id=body.grupo_id,
                )
            )

        if not registros:
            raise HTTPException(
                status_code=400,
                detail="Ningún punto quedó dentro de Colombia.",
            )

        grupo_id = puntos_storage.append_registros(registros)
        return {
            "status": "success",
            "creado_por": user.email,
            "grupo_id": grupo_id,
            "guardados": len(registros),
            "rechazados": rechazados,
        }
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.warning("%s", e)
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error guardando lote: %s", e)
        raise HTTPException(status_code=500, detail="Error al persistir la informacion")


@router.post("/resolver")
def resolver_comentario(
    body: ResolverComentario, user: AuthUser = Depends(require_user)
):
    try:
        ok = puntos_storage.resolver_registro(
            timestamp=body.timestamp,
            lat=body.lat,
            lon=body.lon,
            resuelto=body.resuelto,
            resuelto_por=user.email,
            grupo_id=body.grupo_id,
        )
        if not ok:
            raise HTTPException(status_code=404, detail="Comentario no encontrado")
        return {
            "status": "success",
            "resuelto": body.resuelto,
            "resuelto_por": user.email,
            "actualizados": ok,
        }
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.warning("%s", e)
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error resolviendo comentario: %s", e)
        raise HTTPException(status_code=500, detail="Error al resolver el comentario")
