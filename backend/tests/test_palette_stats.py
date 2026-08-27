"""Pruebas de paleta / stats (mapa negro, heatmap, bounds)."""

from backend.core.leyenda import PALETTE, VIS_MAX, VIS_MIN, color_clase, nombre_clase
from backend.services.stats_service import estadisticas_bioma, heatmap_bioma
from backend.services.region_bounds_service import bounds_biomas, bounds_region


def test_palette_not_black_at_zero():
    assert VIS_MIN == 0
    assert VIS_MAX == 82
    assert len(PALETTE) == 83
    assert PALETTE[0] == "#ffffff"
    assert PALETTE[3] == "#1f8d49"
    assert PALETTE[40] == "#c71585"
    assert PALETTE[27] == "#ffffff"
    assert PALETTE[7] == "#ffffff"
    assert color_clase(40) == "#C71585"
    assert "Arroz" in nombre_clase(40)
    assert PALETTE.count("#000000") == 0


def test_stats_and_heatmap_andes():
    b = estadisticas_bioma(["Andes"])
    assert b["disponible"] is True
    assert "aportes" not in b
    assert b.get("has_heatmap") is True
    h = heatmap_bioma(["Andes"], "ID03")
    assert h["disponible"] is True
    assert len(h["periods"]) >= 2
    assert len(h["regions"]) >= 1


def test_bounds_andes_valid():
    box = bounds_biomas(["Andes"])
    south, west = box["leaflet"][0]
    north, east = box["leaflet"][1]
    assert -90 <= south < north <= 90
    assert -180 <= west < east <= 180
    r = bounds_region("30407")
    assert r["leaflet"][0][0] < r["leaflet"][1][0]
