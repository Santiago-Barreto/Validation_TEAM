"""Biomas visibles / internos y colores (script GEE base)."""

BIOMAS_VISIBLES = ["Amazonía", "Andes", "Caribe", "Orinoquía", "Pacífico"]

BIOMAS_INTERNOS = {
    "Amazonía": ["Amazonía"],
    "Andes": ["Andes"],
    "Caribe": ["Caribe", "Caribe Insular"],
    "Orinoquía": ["Orinoquía"],
    "Pacífico": ["Pacifico", "Pacifico insular"],
}

COLOR_POR_BIOMA = {
    "Amazonía": "#3498db",
    "Andes": "#2ecc71",
    "Caribe": "#e74c3c",
    "Caribe Insular": "#e74c3c",
    "Orinoquía": "#9b59b6",
    "Pacifico": "#f1c40f",
    "Pacifico insular": "#f1c40f",
}


def expandir_biomas(nombres_visibles: list[str]) -> list[str]:
    """Convierte checkboxes de UI a nombres internos del FeatureCollection."""
    out: list[str] = []
    for nombre in nombres_visibles:
        internos = BIOMAS_INTERNOS.get(nombre)
        if internos:
            out.extend(internos)
        else:
            out.append(nombre)
    # dedupe preservando orden
    seen = set()
    unique = []
    for b in out:
        if b not in seen:
            seen.add(b)
            unique.append(b)
    return unique
