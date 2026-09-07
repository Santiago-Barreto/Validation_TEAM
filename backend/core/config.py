from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2 import service_account

from backend.core.runtime_paths import get_backend_dir, get_install_root

load_dotenv(get_backend_dir() / ".env")

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/earthengine",
    "https://www.googleapis.com/auth/cloud-platform",
]

PUNTOS_BACKEND = os.environ.get("PUNTOS_BACKEND", "json").strip().lower()

_install_root = get_install_root()
_base_backend = get_backend_dir()
_default_json = str(_base_backend / "data" / "comentarios_team.json")
PUNTOS_JSON_PATH = os.environ.get("PUNTOS_JSON_PATH", _default_json)

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

    for credentials_path in (
        _base_backend / "credentials.json",
        _install_root / "credentials.json",
    ):
        if credentials_path.is_file():
            return service_account.Credentials.from_service_account_file(
                str(credentials_path),
                scopes=SCOPE,
            )
    raise FileNotFoundError(
        "credentials.json not found under backend/ or install root."
    )


CREDS = obtener_creds()

_default_stats_db = str(_install_root / "data" / "mapbiomas.db")
STATISTICS_DB_PATH = os.path.normpath(
    os.environ.get("STATISTICS_DB_PATH", _default_stats_db)
)

_default_avance_xlsx = str(
    _install_root / "data" / "COLOMBIA_COL_4_Formatos de avance detallado Colombia.xlsx"
)
AVANCE_COLOMBIA_XLSX = os.path.normpath(
    os.environ.get("AVANCE_COLOMBIA_XLSX", _default_avance_xlsx)
)
AVANCE_SHEET = os.environ.get("AVANCE_SHEET", "MAPA GENERAL COLOMBIA")
# Optional: read interpreter map from Google Sheets instead of local Excel.
AVANCE_SHEET_ID = (os.environ.get("AVANCE_SHEET_ID") or "").strip() or None
_avance_gid = (os.environ.get("AVANCE_SHEET_GID") or "").strip()
AVANCE_SHEET_GID = int(_avance_gid) if _avance_gid.isdigit() else None

GOOGLE_OAUTH_CLIENT_ID = (os.environ.get("GOOGLE_OAUTH_CLIENT_ID") or "").strip()
_raw_domains = os.environ.get("AUTH_ALLOWED_DOMAINS", "gaiaamazonas.org")
AUTH_ALLOWED_DOMAINS = {
    d.strip().lower().lstrip("@")
    for d in _raw_domains.split(",")
    if d.strip()
}
