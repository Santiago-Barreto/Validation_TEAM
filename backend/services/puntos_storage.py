"""
Persistencia de comentarios TEAM: PostgreSQL/SQLite, Google Sheets o JSON local.

Fila:
timestamp | lat | lon | nombre | comentario | clase_sugerida | anio_contexto | bioma | resuelto | creado_por | resuelto_por | foto_url | grupo_id
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import uuid
from typing import Any, List, Optional

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

# Columnas 1-based en Google Sheets
_COMENTARIO_COL = 5
_CLASE_SUGERIDA_COL = 6
_RESUELTO_COL = 9
_RESUELTO_POR_COL = 11
_CREADO_POR_COL_IDX = 9  # 0-based
_GRUPO_ID_COL_IDX = 12  # 0-based en filas
_COORD_EPS = 1e-5
_MIN_ROW_LEN = 13


class ComentarioNoAutorizadoError(PermissionError):
    """El usuario no es el autor del comentario."""


def _ensure_grupo_id(r: Registro) -> str:
    gid = (r.grupo_id or "").strip()
    if not gid:
        gid = str(uuid.uuid4())
        r.grupo_id = gid
    return gid


def _pad_row(row: List[Any], n: int = _MIN_ROW_LEN) -> List[Any]:
    while len(row) < n:
        row.append("")
    return row


def _row_grupo_id(row: List[Any]) -> str:
    if len(row) <= _GRUPO_ID_COL_IDX:
        return ""
    return str(row[_GRUPO_ID_COL_IDX] or "").strip()


def _row_creado_por(row: List[Any]) -> str:
    if len(row) <= _CREADO_POR_COL_IDX:
        return ""
    return str(row[_CREADO_POR_COL_IDX] or "").strip().lower()


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


def _json_rewrite_rows(path: str, rows: List[List[Any]]) -> None:
    """Reemplaza el JSON local para que refleje exactamente lo leído de Sheets."""
    lock_path = path + ".lock"
    _ensure_json_parent(path)
    with FileLock(lock_path, timeout=30):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"registros": rows}, f, ensure_ascii=False, indent=2)


def _sync_json_fallback(rows: List[List[Any]]) -> None:
    try:
        _json_rewrite_rows(PUNTOS_JSON_PATH, rows)
    except Exception:
        logger.exception("No se pudo sincronizar JSON fallback con Sheets.")


def _opt(v: Any) -> str:
    if v is None:
        return ""
    return str(v)


def _row_from_registro(r: Registro, timestamp: str) -> List[Any]:
    return [
        timestamp,
        r.lat,
        r.lon,
        r.nombre,
        r.comentario,
        _opt(r.clase_sugerida),
        r.anio_contexto if r.anio_contexto is not None else "",
        r.bioma or "",
        "",
        (r.creado_por or "").strip().lower(),
        "",
        (r.foto_url or "").strip(),
        (r.grupo_id or "").strip(),
    ]


def _db_row_to_api_row(p: PuntoValidacion) -> List[Any]:
    ts = p.created_at.strftime("%Y-%m-%d %H:%M")
    return [
        ts,
        p.lat,
        p.lon,
        p.nombre,
        p.comentario,
        p.clase_sugerida or "",
        p.anio_contexto or "",
        p.bioma or "",
        getattr(p, "resuelto", "") or "",
        getattr(p, "creado_por", "") or "",
        getattr(p, "resuelto_por", "") or "",
        getattr(p, "foto_url", "") or "",
        getattr(p, "grupo_id", "") or "",
    ]


def _coords_match(a: Any, b: float) -> bool:
    try:
        return abs(float(a) - float(b)) <= _COORD_EPS
    except (TypeError, ValueError):
        return False


def _row_matches(row: List[Any], timestamp: str, lat: float, lon: float) -> bool:
    if not row or len(row) < 3:
        return False
    if str(row[0]).strip() != str(timestamp).strip():
        return False
    return _coords_match(row[1], lat) and _coords_match(row[2], lon)


def list_registros() -> List[List[Any]]:
    mode = _resolved_mode()
    if mode == "database":
        return _list_db()
    if mode == "json":
        return _json_read_rows(PUNTOS_JSON_PATH)
    if mode == "sheets":
        ws = sheets_client.require_worksheet()
        datos = ws.get_all_values()
        rows = datos[1:] if len(datos) > 1 else []
        _sync_json_fallback(rows)
        return rows

    ws = sheets_client.get_worksheet()
    if ws is not None:
        try:
            datos = ws.get_all_values()
            rows = datos[1:] if len(datos) > 1 else []
            _sync_json_fallback(rows)
            return rows
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


def append_registro(r: Registro) -> str:
    """Persiste el registro. Devuelve grupo_id (generado si faltaba)."""
    return append_registros([r])


def append_registros(registros: list[Registro]) -> str:
    """Persiste varios registros (mismo grupo). Una sola escritura a Sheets/JSON."""
    if not registros:
        raise ValueError("Sin registros para guardar.")

    grupo_id = _ensure_grupo_id(registros[0])
    for r in registros:
        r.grupo_id = grupo_id

    mode = _resolved_mode()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = [_row_from_registro(r, timestamp) for r in registros]

    if mode == "database":
        for r in registros:
            _append_db(r, timestamp)
        return grupo_id
    if mode == "json":
        _json_append_rows(PUNTOS_JSON_PATH, rows)
        return grupo_id
    if mode == "sheets":
        ws = sheets_client.require_worksheet()
        ws.append_rows(
            [[str(x) if x is not None else "" for x in row] for row in rows],
            value_input_option="USER_ENTERED",
        )
        return grupo_id

    ws = sheets_client.get_worksheet()
    if ws is not None:
        try:
            ws.append_rows(
                [[str(x) if x is not None else "" for x in row] for row in rows],
                value_input_option="USER_ENTERED",
            )
            return grupo_id
        except Exception:
            logger.exception("Escritura Sheets fallo; registrando en JSON.")
    _json_append_rows(PUNTOS_JSON_PATH, rows)
    logger.warning("Registros almacenados solo en JSON fallback.")
    return grupo_id


def _json_append_rows(path: str, new_rows: List[List[Any]]) -> None:
    lock_path = path + ".lock"
    _ensure_json_parent(path)
    with FileLock(lock_path, timeout=30):
        rows: List[List[Any]] = []
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                rows = list(data.get("registros", []))
        rows.extend(new_rows)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"registros": rows}, f, ensure_ascii=False, indent=2)


def resolver_registro(
    timestamp: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    resuelto: str = "check",
    resuelto_por: str = "",
    grupo_id: Optional[str] = None,
) -> int:
    """
    Marca resuelto. Si hay grupo_id, aplica a todos los puntos del grupo.
    Devuelve cantidad de filas actualizadas.
    """
    mark = "check" if resuelto == "check" else "x"
    who = (resuelto_por or "").strip().lower()
    gid = (grupo_id or "").strip()
    mode = _resolved_mode()

    if mode == "database":
        return _resolver_db(timestamp, lat, lon, mark, who, gid)
    if mode == "json":
        return _resolver_json(PUNTOS_JSON_PATH, timestamp, lat, lon, mark, who, gid)
    if mode == "sheets":
        return _resolver_sheets(timestamp, lat, lon, mark, who, gid)

    if sheets_client.get_worksheet() is not None:
        try:
            n = _resolver_sheets(timestamp, lat, lon, mark, who, gid)
            if n:
                return n
        except Exception:
            logger.exception("Resolver en Sheets fallo; intentando JSON.")
    return _resolver_json(PUNTOS_JSON_PATH, timestamp, lat, lon, mark, who, gid)


def actualizar_comentario(
    *,
    comentario: str,
    clase_sugerida: Optional[int] = None,
    autor: str,
    timestamp: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    grupo_id: Optional[str] = None,
) -> int:
    """
    Actualiza texto/clase del comentario. Solo el autor (creado_por) puede editar.
    Si hay grupo_id, aplica a todos los puntos del grupo.
    """
    texto = (comentario or "").strip()
    if not texto:
        raise ValueError("El comentario es obligatorio.")
    who = (autor or "").strip().lower()
    if not who:
        raise ComentarioNoAutorizadoError("Sesión sin correo.")
    gid = (grupo_id or "").strip()
    clase = "" if clase_sugerida is None else str(int(clase_sugerida))
    mode = _resolved_mode()

    if mode == "database":
        return _editar_db(timestamp, lat, lon, texto, clase, who, gid)
    if mode == "json":
        return _editar_json(PUNTOS_JSON_PATH, timestamp, lat, lon, texto, clase, who, gid)
    if mode == "sheets":
        return _editar_sheets(timestamp, lat, lon, texto, clase, who, gid)

    if sheets_client.get_worksheet() is not None:
        try:
            n = _editar_sheets(timestamp, lat, lon, texto, clase, who, gid)
            if n:
                return n
        except ComentarioNoAutorizadoError:
            raise
        except Exception:
            logger.exception("Editar en Sheets fallo; intentando JSON.")
    return _editar_json(PUNTOS_JSON_PATH, timestamp, lat, lon, texto, clase, who, gid)


def _editar_sheets(
    timestamp: Optional[str],
    lat: Optional[float],
    lon: Optional[float],
    texto: str,
    clase: str,
    who: str,
    grupo_id: str = "",
) -> int:
    ws = sheets_client.require_worksheet()
    datos = ws.get_all_values()
    targets: list[int] = []
    for i, row in enumerate(datos[1:], start=2):
        match = False
        if grupo_id:
            match = _row_grupo_id(row) == grupo_id
        elif timestamp is not None and lat is not None and lon is not None:
            match = _row_matches(row, timestamp, lat, lon)
        if not match:
            continue
        owner = _row_creado_por(row)
        if owner != who:
            raise ComentarioNoAutorizadoError(
                "Solo puedes editar comentarios que creaste tú."
            )
        targets.append(i)
        if not grupo_id:
            break
    if not targets:
        return 0
    updates = []
    for row_i in targets:
        updates.append({"range": f"E{row_i}", "values": [[texto]]})
        updates.append({"range": f"F{row_i}", "values": [[clase]]})
    ws.batch_update(updates, value_input_option="USER_ENTERED")
    try:
        refreshed = ws.get_all_values()
        _sync_json_fallback(refreshed[1:] if refreshed else [])
    except Exception:
        logger.debug("No se pudo sincronizar JSON tras editar.", exc_info=True)
    return len(targets)


def _editar_json(
    path: str,
    timestamp: Optional[str],
    lat: Optional[float],
    lon: Optional[float],
    texto: str,
    clase: str,
    who: str,
    grupo_id: str = "",
) -> int:
    lock_path = path + ".lock"
    _ensure_json_parent(path)
    with FileLock(lock_path, timeout=30):
        rows: List[List[Any]] = []
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                rows = list(data.get("registros", []))
        updated = 0
        for row in rows:
            match = False
            if grupo_id:
                match = _row_grupo_id(row) == grupo_id
            elif timestamp is not None and lat is not None and lon is not None:
                match = _row_matches(row, timestamp, lat, lon)
            if not match:
                continue
            if _row_creado_por(row) != who:
                raise ComentarioNoAutorizadoError(
                    "Solo puedes editar comentarios que creaste tú."
                )
            _pad_row(row)
            row[4] = texto
            row[5] = clase
            updated += 1
            if not grupo_id:
                break
        if updated:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"registros": rows}, f, ensure_ascii=False, indent=2)
        return updated


def _editar_db(
    timestamp: Optional[str],
    lat: Optional[float],
    lon: Optional[float],
    texto: str,
    clase: str,
    who: str,
    grupo_id: str = "",
) -> int:
    if SessionLocal is None:
        raise RuntimeError("SessionLocal no inicializado.")
    db: Session = SessionLocal()
    try:
        candidates: list[Any] = []
        if grupo_id and hasattr(PuntoValidacion, "grupo_id"):
            candidates = (
                db.query(PuntoValidacion)
                .filter(PuntoValidacion.grupo_id == grupo_id)
                .all()
            )
        elif timestamp is not None and lat is not None and lon is not None:
            try:
                created = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M")
            except ValueError:
                return 0
            q = (
                db.query(PuntoValidacion)
                .filter(PuntoValidacion.created_at == created)
                .all()
            )
            candidates = [
                p
                for p in q
                if _coords_match(p.lat, lat) and _coords_match(p.lon, lon)
            ]
        if not candidates:
            return 0
        updated = 0
        for p in candidates:
            owner = str(getattr(p, "creado_por", "") or "").strip().lower()
            if owner != who:
                raise ComentarioNoAutorizadoError(
                    "Solo puedes editar comentarios que creaste tú."
                )
            p.comentario = texto
            p.clase_sugerida = clase
            updated += 1
        if updated:
            db.commit()
        return updated
    finally:
        db.close()


def _resolver_sheets(
    timestamp: Optional[str],
    lat: Optional[float],
    lon: Optional[float],
    mark: str,
    who: str,
    grupo_id: str = "",
) -> int:
    ws = sheets_client.require_worksheet()
    datos = ws.get_all_values()
    updated = 0
    for i, row in enumerate(datos[1:], start=2):
        match = False
        if grupo_id:
            match = _row_grupo_id(row) == grupo_id
        elif timestamp is not None and lat is not None and lon is not None:
            match = _row_matches(row, timestamp, lat, lon)
        if match:
            ws.update_cell(i, _RESUELTO_COL, mark)
            ws.update_cell(i, _RESUELTO_POR_COL, who)
            updated += 1
            if not grupo_id:
                break
    return updated


def _resolver_json(
    path: str,
    timestamp: Optional[str],
    lat: Optional[float],
    lon: Optional[float],
    mark: str,
    who: str,
    grupo_id: str = "",
) -> int:
    lock_path = path + ".lock"
    _ensure_json_parent(path)
    with FileLock(lock_path, timeout=30):
        rows: List[List[Any]] = []
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                rows = list(data.get("registros", []))
        updated = 0
        for row in rows:
            match = False
            if grupo_id:
                match = _row_grupo_id(row) == grupo_id
            elif timestamp is not None and lat is not None and lon is not None:
                match = _row_matches(row, timestamp, lat, lon)
            if match:
                _pad_row(row)
                row[8] = mark
                row[10] = who
                updated += 1
                if not grupo_id:
                    break
        if updated:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"registros": rows}, f, ensure_ascii=False, indent=2)
        return updated


def _resolver_db(
    timestamp: Optional[str],
    lat: Optional[float],
    lon: Optional[float],
    mark: str,
    who: str,
    grupo_id: str = "",
) -> int:
    if SessionLocal is None:
        raise RuntimeError("SessionLocal no inicializado.")
    db: Session = SessionLocal()
    try:
        updated = 0
        if grupo_id and hasattr(PuntoValidacion, "grupo_id"):
            q = (
                db.query(PuntoValidacion)
                .filter(PuntoValidacion.grupo_id == grupo_id)
                .all()
            )
            for p in q:
                if hasattr(p, "resuelto"):
                    p.resuelto = mark
                if hasattr(p, "resuelto_por"):
                    p.resuelto_por = who
                updated += 1
            if updated:
                db.commit()
            return updated

        if timestamp is None or lat is None or lon is None:
            return 0
        try:
            created = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M")
        except ValueError:
            return 0
        q = (
            db.query(PuntoValidacion)
            .filter(PuntoValidacion.created_at == created)
            .all()
        )
        for p in q:
            if _coords_match(p.lat, lat) and _coords_match(p.lon, lon):
                if hasattr(p, "resuelto"):
                    p.resuelto = mark
                if hasattr(p, "resuelto_por"):
                    p.resuelto_por = who
                db.commit()
                return 1
        return 0
    finally:
        db.close()


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
    mode = _resolved_mode()
    if mode == "sheets":
        ws = sheets_client.get_worksheet()
        if ws is not None:
            try:
                sheets_client.ensure_header_row(ws)
            except Exception:
                logger.exception("No se pudo inicializar encabezados en Google Sheets.")
    logger.info(
        "Comentarios TEAM → backend=%s json=%s sheet=%s",
        mode,
        PUNTOS_JSON_PATH,
        "configurado" if SHEET_ID else "ninguno (aislado de Validation)",
    )
