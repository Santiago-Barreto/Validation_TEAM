"""
Conexion diferida a Google Sheets (gspread).

Evita llamadas de red en tiempo de importacion para que Uvicorn pueda arrancar
aunque la API de Google devuelva 503 u otros errores transitorios.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING, Optional

import gspread
from gspread.exceptions import APIError
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from backend.core.config import CREDS, SHEET_ID

if TYPE_CHECKING:
    from gspread import Worksheet

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_worksheet: Optional["Worksheet"] = None

# Circuit breaker simple: tras varios fallos seguidos, dejar de golpear Sheets un tiempo.
_failure_count = 0
_circuit_open_until = 0.0
_FAILURE_THRESHOLD = 5
_COOLDOWN_SEC = 120


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, APIError):
        # 429 rate limit, 500-599 errores de servidor / disponibilidad
        code = getattr(exc, "response", None)
        status = getattr(code, "status_code", None) if code is not None else None
        if status is not None:
            return status == 429 or status >= 500
        # Mensaje tipico de gspread ante 503
        msg = str(exc).lower()
        return "503" in msg or "unavailable" in msg or "timeout" in msg
    return isinstance(exc, (ConnectionError, TimeoutError, OSError))


@retry(
    retry=retry_if_exception(_is_retryable),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
    before_sleep=lambda retry_state: logger.warning(
        "Reintentando apertura de Google Sheets (intento %s): %s",
        retry_state.attempt_number,
        retry_state.outcome.exception() if retry_state.outcome else "",
    ),
)
def _open_worksheet() -> "Worksheet":
    if not SHEET_ID:
        raise RuntimeError(
            "GOOGLE_SHEET_ID no configurado. Validation TEAM no usa la hoja de Validation."
        )
    client = gspread.authorize(CREDS)
    return client.open_by_key(SHEET_ID).sheet1


def invalidate_cache() -> None:
    """Fuerza nueva conexion en la proxima peticion (p. ej. tras error permanente)."""
    global _worksheet
    with _lock:
        _worksheet = None


def circuit_state() -> dict:
    """Estado para health/detailed (sin exponer secretos)."""
    now = time.monotonic()
    return {
        "circuit_open": now < _circuit_open_until,
        "cooldown_until_sec": max(0.0, _circuit_open_until - now),
        "failures_recorded": _failure_count,
        "worksheet_cached": _worksheet is not None,
        "sheet_configured": bool(SHEET_ID),
    }


def get_worksheet() -> Optional["Worksheet"]:
    """
    Devuelve la hoja de trabajo si la conexion tiene exito; None si el circuito
    esta abierto o tras fallo (para permitir fallback sin tumbar el proceso).
    """
    global _worksheet, _failure_count, _circuit_open_until

    if not SHEET_ID:
        return None

    now = time.monotonic()
    if now < _circuit_open_until:
        logger.warning("Circuito Sheets abierto; omitiendo llamada hasta cooldown.")
        return None

    with _lock:
        if _worksheet is not None:
            return _worksheet

    try:
        ws = _open_worksheet()
        with _lock:
            _worksheet = ws
            _failure_count = 0
        return ws
    except Exception as e:
        with _lock:
            _failure_count += 1
            if _failure_count >= _FAILURE_THRESHOLD:
                _circuit_open_until = time.monotonic() + _COOLDOWN_SEC
                logger.error(
                    "Circuito Sheets abierto tras %s fallos; cooldown %ss. Ultimo error: %s",
                    _failure_count,
                    _COOLDOWN_SEC,
                    e,
                )
                _failure_count = 0
        logger.exception("No se pudo abrir Google Sheets: %s", e)
        return None


def require_worksheet() -> "Worksheet":
    """Usar solo cuando Sheets sea obligatorio (sin fallback)."""
    if not SHEET_ID:
        raise RuntimeError(
            "GOOGLE_SHEET_ID no configurado para Validation TEAM. "
            "Crea una hoja propia; no reutilices la de Validation."
        )
    ws = get_worksheet()
    if ws is None:
        raise RuntimeError(
            "Google Sheets no disponible (circuito abierto o error de red/API)."
        )
    return ws
