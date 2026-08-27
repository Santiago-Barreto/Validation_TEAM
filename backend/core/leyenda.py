"""
Leyenda MapBiomas Colombia — fuente: Codigo-de-la-Leyenda-coleccion-3.pdf
(Validation_TEAM/Codigo-de-la-Leyenda-coleccion-3.pdf).

IDs, etiquetas ES y colores hexadecimales del documento oficial.
"""

from __future__ import annotations

from typing import Any

# (id, label_es, hex sin #) — hojas + nodos padre del PDF
_LEYENDA_PDF: list[tuple[int, str, str]] = [
    # 1. Formación boscosa
    (1, "1. Formación boscosa", "1F8D49"),
    (3, "1.1. Bosque", "1F8D49"),
    (5, "1.2. Manglar", "04381D"),
    (6, "1.3. Bosque inundable", "026975"),
    (49, "1.4. Vegetación leñosa sobre arena", "02D659"),
    # 2. Formación natural no boscosa
    (10, "2. Formación natural no boscosa", "D6BC74"),
    (11, "2.1. Formación natural no forestal inundable", "519799"),
    (12, "2.2. Formación herbácea", "D6BC74"),
    (32, "2.3. Planicie de marea hipersalina", "FC8114"),
    (29, "2.4. Afloramiento rocoso", "FFAA5F"),
    (50, "2.5. Vegetación herbácea sobre arena", "AD5100"),
    (13, "2.6. Otra formación natural no forestal", "D89F5C"),
    (81, "2.7. Herbazales o arbustales andinos", "DFEB62"),
    (82, "2.8. Herbazales o arbustales andinos inundables", "6FC179"),
    # 3. Área agropecuaria
    (14, "3. Área agropecuaria", "FFEFC3"),
    (9, "3.1. Silvicultura", "7A5900"),
    (35, "3.2. Palma aceitera", "9065D0"),
    (40, "3.2.2. Arroz", "C71585"),
    (74, "3.3. Plátano y banano (beta)", "BE83F7"),
    (21, "3.4. Mosaico de agricultura o pasto", "FFEFC3"),
    # 4. Área sin vegetación
    (22, "4. Área sin vegetación", "D4271E"),
    (23, "4.1. Playas, dunas y bancos de arena", "FFA07A"),
    (24, "4.2. Infraestructura urbana", "D4271E"),
    (30, "4.3. Minería", "9C0027"),
    (68, "4.4. Otra área natural sin vegetación", "E97A7A"),
    (25, "4.5. Otra área sin vegetación", "DB4D4F"),
    (75, "4.6. Parques solares", "C12100"),
    # 5. Cuerpo de agua
    (26, "5. Cuerpo de agua", "2532E4"),
    (33, "5.1. Río, lago u océano", "2532E4"),
    (31, "5.2. Acuicultura", "091077"),
    (34, "5.3. Glaciar y nival", "93DFE6"),
    # 6. No observado (PDF: FFFFFF)
    (27, "6. No observado", "FFFFFF"),
]

LEYENDA: dict[int, dict[str, str]] = {
    cid: {"label": label, "color": f"#{hex_code.upper()}"}
    for cid, label, hex_code in _LEYENDA_PDF
}

COBERTURAS_GRUPOS = [
    {
        "titulo": "1. Formación boscosa",
        "clases": {
            cid: LEYENDA[cid]["label"]
            for cid in (3, 5, 6, 49)
            if cid in LEYENDA
        },
    },
    {
        "titulo": "2. Formación natural no boscosa",
        "clases": {
            cid: LEYENDA[cid]["label"]
            for cid in (11, 12, 32, 29, 50, 13, 81, 82)
            if cid in LEYENDA
        },
    },
    {
        "titulo": "3. Área agropecuaria",
        "clases": {
            cid: LEYENDA[cid]["label"]
            for cid in (9, 35, 40, 74, 21)
            if cid in LEYENDA
        },
    },
    {
        "titulo": "4. Área sin vegetación",
        "clases": {
            cid: LEYENDA[cid]["label"]
            for cid in (23, 24, 30, 68, 25, 75)
            if cid in LEYENDA
        },
    },
    {
        "titulo": "5. Cuerpo de agua",
        "clases": {
            cid: LEYENDA[cid]["label"]
            for cid in (33, 31, 34)
            if cid in LEYENDA
        },
    },
    {
        "titulo": "6. No observado",
        "clases": {27: LEYENDA[27]["label"]},
    },
]

COBERTURAS: dict[int, str] = {
    int(cid): label
    for grupo in COBERTURAS_GRUPOS
    for cid, label in grupo["clases"].items()
}

# Paleta GEE original (índice = valor de clase 0..62). No rellenar huecos con
# negro: EE pinta clase 0 / IDs vacíos y el mapa se ve negro.
_PALETTE_GEE_BASE = [
    "#ffffff",
    "#32a65e",
    "#32a65e",
    "#1f8d49",
    "#7dc975",
    "#04381d",
    "#026975",
    "#000000",
    "#000000",
    "#7a6c00",
    "#ad975a",
    "#519799",
    "#d6bc74",
    "#d89f5c",
    "#ffffb2",
    "#edde8e",
    "#000000",
    "#000000",
    "#f5b3c8",
    "#c27ba0",
    "#db7093",
    "#ffefc3",
    "#db4d4f",
    "#ffa07a",
    "#d4271e",
    "#db4d4f",
    "#0000ff",
    "#000000",
    "#000000",
    "#ffaa5f",
    "#9c0027",
    "#091077",
    "#fc8114",
    "#2532e4",
    "#93dfe6",
    "#9065d0",
    "#d082de",
    "#000000",
    "#000000",
    "#f5b3c8",
    "#c71585",
    "#f54ca9",
    "#cca0d4",
    "#dbd26b",
    "#807a40",
    "#e04cfa",
    "#d68fe2",
    "#9932cc",
    "#e6ccff",
    "#02d659",
    "#ad5100",
    "#000000",
    "#000000",
    "#000000",
    "#000000",
    "#000000",
    "#000000",
    "#cc66ff",
    "#ff6666",
    "#006400",
    "#8d9e8b",
    "#f5d5d5",
    "#ff69b4",
]

VIS_MIN = 0
VIS_MAX = max(LEYENDA.keys())  # 82 incluye 74, 75, 81, 82
PALETTE: list[str] = ["#ffffff"] * (VIS_MAX + 1)
for i, color in enumerate(_PALETTE_GEE_BASE):
    if i < len(PALETTE):
        PALETTE[i] = color
for _cid, info in LEYENDA.items():
    PALETTE[_cid] = info["color"].lower()
# Clase 0 y huecos no definidos: nunca negro (tapan el mapa).
PALETTE[0] = "#ffffff"
for i, color in enumerate(PALETTE):
    if color == "#000000" and i not in LEYENDA:
        PALETTE[i] = "#ffffff"


def color_clase(class_id) -> str:
    try:
        cid = int(class_id)
    except (TypeError, ValueError):
        return "#cccccc"
    return LEYENDA.get(cid, {}).get("color", "#cccccc")


def nombre_clase(class_id) -> str:
    if class_id is None:
        return "N/A"
    try:
        cid = int(class_id)
    except (TypeError, ValueError):
        return f"Clase {class_id}"
    if cid in LEYENDA:
        return LEYENDA[cid]["label"]
    return COBERTURAS.get(cid, f"Clase {cid}")


def leyenda_frontend() -> list[dict[str, Any]]:
    """Estructura para panel de filtro / drawer (con color del PDF)."""
    out: list[dict[str, Any]] = []
    for grupo in COBERTURAS_GRUPOS:
        out.append(
            {
                "titulo": grupo["titulo"],
                "clases": [
                    {
                        "id": int(cid),
                        "label": label,
                        "color": color_clase(cid),
                    }
                    for cid, label in grupo["clases"].items()
                ],
            }
        )
    return out


def leyenda_stats_entry(class_key: str) -> dict[str, Any]:
    """Entrada para series Plotly / tabla de estadísticas (IDxx)."""
    try:
        cid = int(str(class_key).replace("ID", "").strip())
    except ValueError:
        return {"id": None, "label": class_key, "color": "#cccccc"}
    info = LEYENDA.get(cid)
    if not info:
        return {"id": cid, "label": f"Clase {cid}", "color": "#cccccc"}
    return {"id": cid, "label": info["label"], "color": info["color"]}
