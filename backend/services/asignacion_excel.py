"""
Intérprete responsable desde Excel local (columna A × regionId en B).

Hoja: MAPA GENERAL COLOMBIA del avance Col4 en Validation_TEAM.
Independiente del vector EE (propiedad Asignacion) y del proyecto Statistics.
"""

from __future__ import annotations

import logging
import os
import re
from functools import lru_cache
from typing import Optional

from openpyxl import load_workbook

logger = logging.getLogger(__name__)

_HEADER_SKIP = re.compile(
    r"^(int[eé]rprete|responsable|asignaci[oó]n)",
    re.IGNORECASE,
)


def _default_xlsx_path() -> str:
    try:
        from backend.core.config import AVANCE_COLOMBIA_XLSX

        return AVANCE_COLOMBIA_XLSX
    except Exception:
        root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        return os.path.join(
            root,
            "data",
            "COLOMBIA_COL_4_Formatos de avance detallado Colombia.xlsx",
        )


@lru_cache(maxsize=2)
def mapa_interprete_por_region(ruta: Optional[str] = None) -> dict[str, str]:
    """
    Lee columna A (intérprete) y B (regionId) → { '30205': 'Janner', ... }.
    """
    path = ruta or os.environ.get("AVANCE_COLOMBIA_XLSX") or _default_xlsx_path()
    path = os.path.normpath(path)
    if not os.path.isfile(path):
        logger.warning("Excel de avance no encontrado: %s", path)
        return {}

    try:
        from backend.core.config import AVANCE_SHEET as hoja_cfg
    except Exception:
        hoja_cfg = "MAPA GENERAL COLOMBIA"
    hoja = os.environ.get("AVANCE_SHEET", hoja_cfg)
    out: dict[str, str] = {}
    try:
        wb = load_workbook(path, read_only=True, data_only=True)
        if hoja not in wb.sheetnames:
            logger.warning("Hoja %s no existe en %s", hoja, path)
            wb.close()
            return {}
        ws = wb[hoja]
        for row in ws.iter_rows(min_row=1, min_col=1, max_col=2, values_only=True):
            nombre, rid = row[0], row[1]
            if nombre is None or rid is None:
                continue
            nombre_s = str(nombre).strip()
            if not nombre_s or _HEADER_SKIP.match(nombre_s):
                continue
            try:
                rid_s = str(int(float(rid)))
            except (TypeError, ValueError):
                continue
            # Primera aparición gana (filas de detalle del Excel)
            if rid_s not in out:
                out[rid_s] = nombre_s
        wb.close()
    except Exception:
        logger.exception("Error leyendo intérpretes desde Excel")
        return {}

    logger.info("Intérpretes cargados desde Excel: %s regiones", len(out))
    return out


def interprete_de_region(region_id) -> Optional[str]:
    if region_id is None:
        return None
    try:
        key = str(int(float(region_id)))
    except (TypeError, ValueError):
        key = str(region_id).strip()
    return mapa_interprete_por_region().get(key)
