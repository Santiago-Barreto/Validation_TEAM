"""
Estadísticas agregadas por bioma / región — misma lógica que Statistics
(`cargar_datos_bioma` / dashboard por región: métricas, serie Plotly, tabla).

Fuente: SQLite Statistics/mapbiomas.db × VERSIONES_DESEADAS.
"""

from __future__ import annotations

import logging
import os
import re
import sqlite3
from collections import defaultdict
from typing import Any, Optional

from fastapi import HTTPException

from backend.core.biomas import expandir_biomas
from backend.core.config import STATISTICS_DB_PATH
from backend.core.leyenda import leyenda_stats_entry
from backend.core.versiones_col4 import VERSIONES_DESEADAS

logger = logging.getLogger(__name__)

_RE_TAG = re.compile(r"^COLOMBIA-(\d+)-(\d+)$", re.IGNORECASE)
_STATS_PREFIX = "projects/mapbiomas-colombia/assets/LULC/COLECCION4/ESTADISTICAS/"


def _score_leaf(leaf: str) -> tuple[int, int]:
    low = leaf.lower().replace("-", "_")
    if "mapageneral" in low or "mapa_general" in low:
        prio = 0
    elif "espacial" in low:
        prio = 1
    elif re.match(r"^r\d+_v\d+$", low):
        prio = 2
    else:
        prio = 3
    return (prio, len(leaf))


def _versiones_por_region() -> dict[str, int]:
    out: dict[str, int] = {}
    for tag in VERSIONES_DESEADAS:
        m = _RE_TAG.match(tag.strip())
        if not m:
            continue
        rid, ver = m.group(1), int(m.group(2))
        prev = out.get(rid)
        if prev is None or ver > prev:
            out[rid] = ver
    return out


def _connect() -> sqlite3.Connection:
    if not STATISTICS_DB_PATH or not os.path.isfile(STATISTICS_DB_PATH):
        raise HTTPException(
            status_code=503,
            detail=(
                "Base de estadísticas no encontrada. "
                f"Esperada en: {STATISTICS_DB_PATH}."
            ),
        )
    conn = sqlite3.connect(f"file:{STATISTICS_DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _class_key(raw: str) -> str:
    s = str(raw).strip().upper()
    if s.startswith("ID"):
        return s
    try:
        return f"ID{int(s):02d}"
    except ValueError:
        return s


def _leyenda_entry(class_key: str) -> dict[str, Any]:
    return leyenda_stats_entry(class_key)


def _pick_asset_for_region(
    candidatos: list[sqlite3.Row], rid: str, ver: int
) -> Optional[sqlite3.Row]:
    pat = re.compile(
        rf"^R0*{re.escape(rid)}[_-]V0*{ver}(?:$|[_-].*)$",
        re.IGNORECASE,
    )
    hits = [r for r in candidatos if pat.match(r["asset_id"].rsplit("/", 1)[-1])]
    if not hits:
        return None
    hits.sort(key=lambda r: _score_leaf(r["asset_id"].rsplit("/", 1)[-1]))
    return hits[0]


def _resolver_assets(
    conn: sqlite3.Connection, biomas_internos: list[str]
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    """
    Devuelve (asset_ids, faltantes, regiones_ok).
    regiones_ok: [{region_id, version, bioma, asset_id}, ...] ordenado.
    """
    versiones = _versiones_por_region()
    placeholders = ",".join("?" * len(biomas_internos))
    rows = conn.execute(
        f"""
        SELECT asset_id, region_id, bioma
        FROM assets
        WHERE bioma IN ({placeholders})
          AND asset_id LIKE ?
        """,
        [*biomas_internos, f"{_STATS_PREFIX}%"],
    ).fetchall()

    by_region: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        by_region.setdefault(str(row["region_id"]), []).append(row)

    asset_ids: list[str] = []
    faltantes: list[str] = []
    regiones: list[dict[str, Any]] = []

    for rid, ver in sorted(
        versiones.items(),
        key=lambda x: int(x[0]) if x[0].isdigit() else x[0],
    ):
        tag = f"COLOMBIA-{rid}-{ver}"
        candidatos = by_region.get(rid) or []
        if not candidatos:
            continue
        hit = _pick_asset_for_region(candidatos, rid, ver)
        if not hit:
            faltantes.append(tag)
            continue
        asset_ids.append(hit["asset_id"])
        regiones.append(
            {
                "region_id": rid,
                "version": ver,
                "bioma": hit["bioma"],
                "asset_id": hit["asset_id"],
                "label": f"R{rid} · v{ver}",
            }
        )

    return asset_ids, faltantes, regiones


def _resolver_asset_region(
    conn: sqlite3.Connection, region_id: str
) -> tuple[Optional[str], Optional[int], Optional[str]]:
    """Asset de la versión deseada para una región. (asset_id, version, bioma)."""
    rid = str(region_id).strip()
    versiones = _versiones_por_region()
    ver = versiones.get(rid)
    if ver is None:
        return None, None, None

    rows = conn.execute(
        """
        SELECT asset_id, region_id, bioma
        FROM assets
        WHERE CAST(region_id AS TEXT) = ?
          AND asset_id LIKE ?
        """,
        [rid, f"{_STATS_PREFIX}%"],
    ).fetchall()
    if not rows:
        return None, ver, None

    hit = _pick_asset_for_region(list(rows), rid, ver)
    if not hit:
        return None, ver, rows[0]["bioma"]
    return hit["asset_id"], ver, hit["bioma"]


def _extraer_region_asset(asset_id: str) -> str:
    """Extrae R##### del leaf del asset (misma lógica Statistics)."""
    leaf = asset_id.rsplit("/", 1)[-1].replace("-", "_")
    match = re.search(r"(R\d+)", leaf, flags=re.IGNORECASE)
    return match.group(1).upper() if match else leaf


def _pivot_series(
    raw_rows: list[sqlite3.Row],
    *,
    version_label: str,
    exclude_2026: bool = True,
) -> tuple[list[dict[str, Any]], list[str], list[int]]:
    """Pivot year × class_id → (rows, class_ids, years)."""
    by_year: dict[int, dict[str, float]] = defaultdict(dict)
    class_ids: set[str] = set()
    for row in raw_rows:
        try:
            y = int(row["year"])
        except (TypeError, ValueError):
            continue
        if exclude_2026 and y == 2026:
            continue
        ck = _class_key(row["class_id"])
        class_ids.add(ck)
        by_year[y][ck] = round(float(row["area_ha"] or 0.0), 4)

    if not by_year:
        return [], [], []

    sorted_classes = sorted(
        class_ids,
        key=lambda k: (
            _leyenda_entry(k)["id"]
            if _leyenda_entry(k)["id"] is not None
            else 999
        ),
    )
    years = sorted(by_year.keys())
    rows: list[dict[str, Any]] = []
    for y in years:
        item: dict[str, Any] = {"year": y, "version": version_label}
        for ck in sorted_classes:
            item[ck] = by_year[y].get(ck, 0.0)
        rows.append(item)
    return rows, sorted_classes, years


def _aportes_regionales(
    raw_rows: list[sqlite3.Row], *, exclude_2026: bool = True
) -> list[dict[str, Any]]:
    """
    Detalle por región para heatmap (Statistics.cargar_aportes_regionales_bioma).
    """
    out: list[dict[str, Any]] = []
    for row in raw_rows:
        try:
            y = int(row["year"])
        except (TypeError, ValueError):
            continue
        if exclude_2026 and y == 2026:
            continue
        out.append(
            {
                "region": _extraer_region_asset(str(row["asset_id"])),
                "year": y,
                "class_id": _class_key(row["class_id"]),
                "area_ha": round(float(row["area_ha"] or 0.0), 4),
            }
        )
    return out


def construir_heatmap_cambios(
    aportes: list[dict[str, Any]], class_id: str
) -> dict[str, Any]:
    """
    Matriz región × periodo con Δha interanual (Statistics.construir_heatmap_cambios).
    """
    ck = _class_key(class_id)
    by_reg_year: dict[str, dict[int, float]] = defaultdict(lambda: defaultdict(float))
    years: set[int] = set()
    for row in aportes:
        if row["class_id"] != ck:
            continue
        by_reg_year[row["region"]][row["year"]] += float(row["area_ha"] or 0.0)
        years.add(row["year"])

    years_sorted = sorted(years)
    if len(years_sorted) < 2:
        return {
            "regions": sorted(by_reg_year.keys()),
            "periods": [],
            "z": [],
            "zmax": 1.0,
        }

    regions = sorted(by_reg_year.keys())
    periods = [f"{y0}→{y1}" for y0, y1 in zip(years_sorted, years_sorted[1:])]
    z: list[list[float]] = []
    abs_max = 0.0
    for reg in regions:
        series = [by_reg_year[reg].get(y, 0.0) for y in years_sorted]
        deltas = [round(series[i] - series[i - 1], 4) for i in range(1, len(series))]
        z.append(deltas)
        for d in deltas:
            abs_max = max(abs_max, abs(d))

    return {
        "regions": regions,
        "periods": periods,
        "z": z,
        "zmax": abs_max if abs_max > 0 else 1.0,
        "class_id": ck,
    }


def construir_tabla_linea_temporal(
    aportes: list[dict[str, Any]], class_id: str
) -> list[dict[str, Any]]:
    """Línea temporal por región con ganancia/pérdida anual."""
    ck = _class_key(class_id)
    by_key: dict[tuple[str, int], float] = defaultdict(float)
    for row in aportes:
        if row["class_id"] != ck:
            continue
        by_key[(row["region"], row["year"])] += float(row["area_ha"] or 0.0)

    rows_out: list[dict[str, Any]] = []
    prev_by_reg: dict[str, float] = {}
    for region, year in sorted(by_key.keys(), key=lambda t: (t[0], t[1])):
        area = round(by_key[(region, year)], 4)
        if region not in prev_by_reg:
            delta = None
            sentido = "Base"
        else:
            delta = round(area - prev_by_reg[region], 4)
            sentido = "Ganancia" if delta >= 0 else "Pérdida"
        prev_by_reg[region] = area
        rows_out.append(
            {
                "region": region,
                "year": year,
                "area_ha": area,
                "delta_ha": delta,
                "sentido": sentido,
            }
        )
    return rows_out


def _payload_ok(
    *,
    ambito: str,
    titulo: str,
    version_label: str,
    rows: list[dict[str, Any]],
    class_ids: list[str],
    years: list[int],
    n_regiones: int,
    n_assets: int,
    faltantes: list[str],
    biomas: list[str] | None = None,
    biomas_internos: list[str] | None = None,
    regiones: list[dict[str, Any]] | None = None,
    region_id: str | None = None,
    version_num: int | None = None,
    aportes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    leyenda = {ck: _leyenda_entry(ck) for ck in class_ids}
    out: dict[str, Any] = {
        "disponible": True,
        "ambito": ambito,
        "titulo": titulo,
        "version": version_label,
        "n_regiones": n_regiones,
        "n_assets": n_assets,
        "faltantes": faltantes,
        "years": years,
        "class_ids": class_ids,
        "leyenda": leyenda,
        "rows": rows,
        "metrics": {
            "year_min": years[0],
            "year_max": years[-1],
            "n_versiones": 1,
            "n_coberturas": len(class_ids),
        },
        "fuente": "Statistics/mapbiomas.db + VERSIONES_DESEADAS",
    }
    if biomas is not None:
        out["biomas"] = biomas
    if biomas_internos is not None:
        out["biomas_internos"] = biomas_internos
    if regiones is not None:
        out["regiones"] = regiones
    if region_id is not None:
        out["region_id"] = region_id
    if version_num is not None:
        out["version_num"] = version_num
    if aportes is not None:
        out["aportes"] = aportes
    return out


def estadisticas_bioma(biomas: list[str]) -> dict[str, Any]:
    """
    Serie temporal agregada del bioma (equivalente a Statistics.cargar_datos_bioma).
    Incluye lista de regiones con la versión deseada para selector en UI.
    """
    if not biomas:
        raise HTTPException(status_code=400, detail="Selecciona al menos un bioma.")

    internos = expandir_biomas(biomas)
    titulo = (
        f"Bioma {biomas[0]}" if len(biomas) == 1 else f"Biomas: {', '.join(biomas)}"
    )
    version_label = f"BIOMA_{'_'.join(biomas)}".upper().replace(" ", "_")

    conn = _connect()
    try:
        asset_ids, faltantes, regiones = _resolver_assets(conn, internos)
        if not asset_ids:
            return {
                "disponible": False,
                "ambito": "bioma",
                "biomas": biomas,
                "biomas_internos": internos,
                "titulo": titulo,
                "mensaje": "No hay estadísticas en BD para estos biomas/versiones.",
                "faltantes": faltantes,
                "regiones": [],
                "n_regiones": 0,
                "n_assets": 0,
                "rows": [],
                "class_ids": [],
                "leyenda": {},
                "metrics": {},
            }

        placeholders = ",".join("?" * len(asset_ids))
        raw = conn.execute(
            f"""
            SELECT year, class_id, SUM(area_ha) AS area_ha
            FROM stats
            WHERE asset_id IN ({placeholders})
            GROUP BY year, class_id
            ORDER BY year
            """,
            asset_ids,
        ).fetchall()
    finally:
        conn.close()

    rows, sorted_classes, years = _pivot_series(raw, version_label=version_label)
    if not rows:
        return {
            "disponible": False,
            "ambito": "bioma",
            "biomas": biomas,
            "titulo": titulo,
            "mensaje": "Sin filas de stats (¿solo 2026?).",
            "faltantes": faltantes,
            "regiones": regiones,
            "n_regiones": len(regiones),
            "n_assets": len(asset_ids),
            "rows": [],
            "class_ids": [],
            "leyenda": {},
            "metrics": {},
            "has_heatmap": False,
        }

    payload = _payload_ok(
        ambito="bioma",
        titulo=titulo,
        version_label=version_label,
        rows=rows,
        class_ids=sorted_classes,
        years=years,
        n_regiones=len(regiones),
        n_assets=len(asset_ids),
        faltantes=faltantes,
        biomas=biomas,
        biomas_internos=internos,
        regiones=regiones,
    )
    # Heatmap se carga bajo demanda (/stats/bioma/heatmap) — payload liviano.
    payload["has_heatmap"] = len(regiones) > 0 and len(years) >= 2
    return payload


def heatmap_bioma(biomas: list[str], class_id: str) -> dict[str, Any]:
    """
    Matriz región × periodo (Δ ha) para una cobertura — sin mandar aportes crudos.
    """
    if not biomas:
        raise HTTPException(status_code=400, detail="Selecciona al menos un bioma.")
    ck = _class_key(class_id)
    internos = expandir_biomas(biomas)

    conn = _connect()
    try:
        asset_ids, faltantes, regiones = _resolver_assets(conn, internos)
        if not asset_ids:
            return {
                "disponible": False,
                "class_id": ck,
                "mensaje": "Sin assets para heatmap.",
                "faltantes": faltantes,
                "regions": [],
                "periods": [],
                "z": [],
                "zmax": 1.0,
            }
        placeholders = ",".join("?" * len(asset_ids))
        raw = conn.execute(
            f"""
            SELECT asset_id, year, class_id, area_ha
            FROM stats
            WHERE asset_id IN ({placeholders})
              AND class_id = ?
            ORDER BY asset_id, year
            """,
            [*asset_ids, ck],
        ).fetchall()
    finally:
        conn.close()

    aportes = _aportes_regionales(raw)
    heat = construir_heatmap_cambios(aportes, ck)
    return {
        "disponible": bool(heat.get("periods")),
        "class_id": ck,
        "leyenda": _leyenda_entry(ck),
        "n_regiones": len(regiones),
        "faltantes": faltantes,
        **heat,
    }


def estadisticas_region(region_id: str) -> dict[str, Any]:
    """
    Serie temporal de una región con la versión de VERSIONES_DESEADAS
    (misma resolución de asset que el bioma: preferir MapaGeneral).
    """
    rid = str(region_id).strip()
    if not rid:
        raise HTTPException(status_code=400, detail="region_id requerido.")

    conn = _connect()
    try:
        asset_id, ver, bioma = _resolver_asset_region(conn, rid)
        if ver is None:
            raise HTTPException(
                status_code=404,
                detail=f"Región {rid} no está en VERSIONES_DESEADAS.",
            )
        if not asset_id:
            return {
                "disponible": False,
                "ambito": "region",
                "region_id": rid,
                "version_num": ver,
                "bioma": bioma,
                "titulo": f"Región {rid}",
                "mensaje": (
                    f"No hay stats en BD para COLOMBIA-{rid}-{ver} "
                    "(versión deseada del bioma)."
                ),
                "faltantes": [f"COLOMBIA-{rid}-{ver}"],
                "n_regiones": 0,
                "n_assets": 0,
                "rows": [],
                "class_ids": [],
                "leyenda": {},
                "metrics": {},
            }

        raw = conn.execute(
            """
            SELECT year, class_id, area_ha
            FROM stats
            WHERE asset_id = ?
            ORDER BY year
            """,
            [asset_id],
        ).fetchall()
    finally:
        conn.close()

    version_label = f"R{rid}_V{ver}"
    titulo = f"Región {rid}" + (f" · {bioma}" if bioma else "") + f" · v{ver}"
    rows, sorted_classes, years = _pivot_series(raw, version_label=version_label)
    if not rows:
        return {
            "disponible": False,
            "ambito": "region",
            "region_id": rid,
            "version_num": ver,
            "bioma": bioma,
            "titulo": titulo,
            "mensaje": "Sin filas de stats para esta región.",
            "faltantes": [],
            "n_regiones": 1,
            "n_assets": 1,
            "rows": [],
            "class_ids": [],
            "leyenda": {},
            "metrics": {},
        }

    return _payload_ok(
        ambito="region",
        titulo=titulo,
        version_label=version_label,
        rows=rows,
        class_ids=sorted_classes,
        years=years,
        n_regiones=1,
        n_assets=1,
        faltantes=[],
        region_id=rid,
        version_num=ver,
        biomas=[bioma] if bioma else [],
    )
