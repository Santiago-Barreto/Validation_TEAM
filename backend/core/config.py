"""
Configuración global Validation TEAM.

Autenticación EE/Sheets, almacenamiento de comentarios y constantes de proyecto.
"""

from __future__ import annotations

import json
import os

from google.oauth2 import service_account

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/earthengine",
    "https://www.googleapis.com/auth/cloud-platform",
]

# Persistencia de comentarios TEAM — NUNCA reutilizar la hoja de Validation.
# Por defecto: JSON local (backend/data/comentarios_team.json).
# auto | database | sheets | json
PUNTOS_BACKEND = os.environ.get("PUNTOS_BACKEND", "json").strip().lower()

_base_backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_default_json = os.path.join(_base_backend, "data", "comentarios_team.json")
PUNTOS_JSON_PATH = os.environ.get("PUNTOS_JSON_PATH", _default_json)

# Solo si se configura explícitamente una hoja PROPIA de TEAM (no la de Validation).
SHEET_ID = (os.environ.get("GOOGLE_SHEET_ID") or "").strip() or None
PROJECT_ID = "mapbiomas-colombia"


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


_raw_db_url = os.environ.get("DATABASE_URL")
DATABASE_URL = _normalize_database_url(_raw_db_url) if _raw_db_url else None


def obtener_creds():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if creds_json:
        return service_account.Credentials.from_service_account_info(
            json.loads(creds_json),
            scopes=SCOPE,
        )

    credentials_path = os.path.join(_base_backend, "credentials.json")
    return service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=SCOPE,
    )


CREDS = obtener_creds()

# SQLite de estadísticas Col4 — copia LOCAL en Validation_TEAM (independiente de Statistics).
# Validation_TEAM/backend → ../data/mapbiomas.db
_default_stats_db = os.path.normpath(
    os.path.join(_base_backend, "..", "data", "mapbiomas.db")
)
STATISTICS_DB_PATH = os.path.normpath(
    os.environ.get("STATISTICS_DB_PATH", _default_stats_db)
)

# Excel de avance Col4 (intérprete col. A × regionId col. B)
_default_avance_xlsx = os.path.normpath(
    os.path.join(
        _base_backend,
        "..",
        "COLOMBIA_COL_4_Formatos de avance detallado Colombia.xlsx",
    )
)
AVANCE_COLOMBIA_XLSX = os.path.normpath(
    os.environ.get("AVANCE_COLOMBIA_XLSX", _default_avance_xlsx)
)
AVANCE_SHEET = os.environ.get("AVANCE_SHEET", "MAPA GENERAL COLOMBIA")
