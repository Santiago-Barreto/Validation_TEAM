"""Rutas de assets Earth Engine (misma lógica que el script GEE base)."""

YEAR_MIN = 1985
YEAR_MAX = 2025
COL3_MAX_YEAR = 2024

PATHS = {
    "region_vector": (
        "projects/mapbiomas-colombia/assets/DATOS_AUXILIARES/VECTORES/"
        "col-clasificacion-regiones-c3"
    ),
    "col3": (
        "projects/mapbiomas-colombia/assets/LULC/COLECCION3/INTEGRACION/"
        "integracion-regiones"
    ),
    "col4_folder": (
        "projects/mapbiomas-colombia/assets/LULC/COLECCION4/clasificacion-ft"
    ),
}

BANDAS_COL4 = [f"classification_{y}" for y in range(YEAR_MIN, YEAR_MAX + 1)]
