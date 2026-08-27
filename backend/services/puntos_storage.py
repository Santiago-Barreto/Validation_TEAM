"""
Persistencia de comentarios TEAM: PostgreSQL/SQLite, Google Sheets o JSON local.

Fila:
timestamp | lat | lon | comentario | nombre | clasificacion | anio_contexto |
clase_col3 | clase_col4 | bioma | clase_sugerida
"""

from __future__ import annotations

import datetime
import json
import logging
import os
from typing import Any, List

from filelock import FileLock
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.core.config import (
    DATABASE_URL,
    PUNTOS_BACKEND,
    PUNTOS_JSON_PATH,
    SHEET_ID,
)
from backend.core import sheets_client
from backend.db.session import SessionLocal
from backend.db.models import PuntoValidacion
from backend.models.registro import Registro

logger = logging.getLogger(__name__)


def _resolved_mode() -> str:
    b = (PUNTOS_BACKEND or "json").strip().lower()
    if b == "auto":
        if DATABASE_URL:
            return "database"
        if SHEET_ID:
            return "sheets_fallback"
        return "json"
    if b in ("database", "sheets", "json"):
        return b
    logger.warning("PUNTOS_BACKEND desconocido %r; usando json (TEAM aislado).", b)
    return "json"


def _ensure_json_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def _json_read_rows(path: str) -> List[List[Any]]:
    lock_path = path + ".lock"
    if not os.path.exists(path):
        return []
    with FileLock(lock_path, timeout=30):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return list(data.get("registros", []))


def _json_append_row(path: str, row: List[Any]) -> None:
    lock_path = path + ".lock"
    _ensure_json_parent(path)
    with FileLock(lock_path, timeout=30):
        rows: List[List[Any]] = []
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                rows = list(data.get("registros", []))
        rows.append(row)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"registros": rows}, f, ensure_ascii=False, indent=2)


def _opt(v: Any) -> str:
    if v is None:
        return ""
    return str(v)


def _row_from_registro(r: Registro, timestamp: str) -> List[Any]:
    return [
        timestamp,
        r.lat,
        r.lon,
        r.comentario,
        r.nombre,
        r.clasificacion,
        r.anio_contexto if r.anio_contexto is not None else "",
        _opt(r.clase_col3),
        _opt(r.clase_col4),
        r.bioma or "",
        _opt(r.clase_sugerida),
    ]


def _db_row_to_api_row(p: PuntoValidacion) -> List[Any]:
    ts = p.created_at.strftime("%Y-%m-%d %H:%M")
    return [
        ts,
        p.lat,
        p.lon,
        p.comentario,
        p.nombre,
        p.clasificacion,
        p.anio_contexto or "",
        p.clase_col3 or "",
        p.clase_col4 or "",
        p.bioma or "",
        p.clase_sugerida or "",
    ]


def list_registros() -> List[List[Any]]:
    mode = _resolved_mode()
    if mode == "database":
        return _list_db()
    if mode == "json":
        return _json_read_rows(PUNTOS_JSON_PATH)
    if mode == "sheets":
        ws = sheets_client.require_worksheet()
        datos = ws.get_all_values()
        return datos[1:] if len(datos) > 1 else []

    ws = sheets_client.get_worksheet()
    if ws is not None:
        try:
            datos = ws.get_all_values()
            return datos[1:] if len(datos) > 1 else []
        except Exception:
            logger.exception("Lectura Sheets fallo; usando JSON si existe.")
    rows = _json_read_rows(PUNTOS_JSON_PATH)
    if rows:
        logger.info("Sirviendo %s registros desde fallback JSON.", len(rows))
    return rows


def _list_db() -> List[List[Any]]:
    if SessionLocal is None:
        raise RuntimeError("SessionLocal no inicializado (DATABASE_URL ausente).")
    db: Session = SessionLocal()
    try:
        q = db.query(PuntoValidacion).order_by(PuntoValidacion.id.asc()).all()
        return [_db_row_to_api_row(p) for p in q]
    finally:
        db.close()


def append_registro(r: Registro) -> None:
    mode = _resolved_mode()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    row = _row_from_registro(r, timestamp)

    if mode == "database":
        _append_db(r, timestamp)
        return
    if mode == "json":
        _json_append_row(PUNTOS_JSON_PATH, row)
        return
    if mode == "sheets":
        ws = sheets_client.require_worksheet()
        ws.append_row([str(x) if x is not None else "" for x in row])
        return

    ws = sheets_client.get_worksheet()
    if ws is not None:
        try:
            ws.append_row([str(x) if x is not None else "" for x in row])
            return
        except Exception:
            logger.exception("Escritura Sheets fallo; registrando en JSON.")
    _json_append_row(PUNTOS_JSON_PATH, row)
    logger.warning("Registro almacenado solo en JSON fallback.")


def _append_db(r: Registro, timestamp: str) -> None:
    if SessionLocal is None:
        raise RuntimeError("SessionLocal no inicializado.")
    db: Session = SessionLocal()
    try:
        created = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M")
        p = PuntoValidacion(
            created_at=created,
            lat=r.lat,
            lon=r.lon,
            comentario=r.comentario or "",
            nombre=r.nombre or "",
            clasificacion=r.clasificacion,
            anio_contexto=str(r.anio_contexto) if r.anio_contexto is not None else "",
            clase_col3=_opt(r.clase_col3),
            clase_col4=_opt(r.clase_col4),
            bioma=r.bioma or "",
            clase_sugerida=_opt(r.clase_sugerida),
        )
        db.add(p)
        db.commit()
    finally:
        db.close()


def readiness_info() -> dict:
    mode = _resolved_mode()
    info: dict = {
        "puntos_backend_resolved": mode,
        "database_configured": bool(DATABASE_URL),
    }
    info["sheets"] = sheets_client.circuit_state()
    if mode == "database" and SessionLocal is None:
        info["ready"] = False
        info["detail"] = "DATABASE_URL no disponible para modo database"
        return info
    if mode == "database":
        try:
            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))
                info["ready"] = True
            finally:
                db.close()
        except Exception as e:
            info["ready"] = False
            info["detail"] = str(e)
        return info

    info["ready"] = True
    info["json_fallback_path"] = PUNTOS_JSON_PATH
    return info


def validate_startup_settings() -> None:
    if PUNTOS_BACKEND == "database" and not DATABASE_URL:
        raise RuntimeError(
            "PUNTOS_BACKEND=database requiere la variable de entorno DATABASE_URL."
        )
    if PUNTOS_BACKEND == "sheets" and not SHEET_ID:
        raise RuntimeError(
            "PUNTOS_BACKEND=sheets requiere GOOGLE_SHEET_ID propio de TEAM "
            "(no uses la hoja de Validation)."
        )
    logger.info(
        "Comentarios TEAM → backend=%s json=%s sheet=%s",
        _resolved_mode(),
        PUNTOS_JSON_PATH,
        "configurado" if SHEET_ID else "ninguno (aislado de Validation)",
    )
