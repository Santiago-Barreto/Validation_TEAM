"""Endpoints de comentarios / correcciones del equipo."""

import logging

from fastapi import APIRouter, HTTPException

from backend.models.registro import Registro
from backend.services import puntos_storage

logger = logging.getLogger(__name__)

router = APIRouter()


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
def guardar_registro(r: Registro):
    try:
        puntos_storage.append_registro(r)
        return {"status": "success"}
    except RuntimeError as e:
        logger.warning("%s", e)
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error guardando registro: %s", e)
        raise HTTPException(status_code=500, detail="Error al persistir la informacion")
