#!/usr/bin/env python3
"""
Benchmark de rendimiento Validation TEAM.
Uso: python scripts/benchmark_perf.py [--base http://127.0.0.1:8000] [--direct]
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

BIOMA = "Caribe"
YEAR = 2025
LAT, LON = 10.42, -75.52  # Caribe interior


@dataclass
class BenchResult:
    name: str
    samples_ms: list[float] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def median_ms(self) -> float:
        return statistics.median(self.samples_ms) if self.samples_ms else 0.0

    @property
    def p95_ms(self) -> float:
        if not self.samples_ms:
            return 0.0
        s = sorted(self.samples_ms)
        idx = min(len(s) - 1, int(len(s) * 0.95))
        return s[idx]


def _http_get(url: str, timeout: float = 120.0) -> tuple[float, int, dict]:
    t0 = time.perf_counter()
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
        elapsed = (time.perf_counter() - t0) * 1000
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {"raw_len": len(body)}
        return elapsed, resp.status, data


def _run_http(name: str, url: str, repeats: int = 3) -> BenchResult:
    res = BenchResult(name=name)
    for i in range(repeats):
        try:
            ms, status, data = _http_get(url)
            res.samples_ms.append(ms)
            if i == 0:
                res.extra["status"] = status
                if isinstance(data, dict):
                    for k in ("cached", "url", "disponible", "total_encontrados"):
                        if k in data:
                            res.extra[k] = data[k]
                    if isinstance(data.get("registros"), list):
                        res.extra["rows"] = len(data["registros"])
                    elif isinstance(data, list):
                        res.extra["rows"] = len(data)
        except urllib.error.HTTPError as e:
            res.extra["error"] = f"HTTP {e.code}: {e.read()[:200]}"
            break
        except Exception as e:
            res.extra["error"] = str(e)
            break
    return res


def _run_direct(fn: Callable[[], Any], name: str, repeats: int = 2) -> BenchResult:
    res = BenchResult(name=name)
    for i in range(repeats):
        t0 = time.perf_counter()
        out = fn()
        ms = (time.perf_counter() - t0) * 1000
        res.samples_ms.append(ms)
        if i == 0 and isinstance(out, dict):
            for k in ("cached", "url", "disponible", "total_encontrados"):
                if k in out:
                    res.extra[k] = out[k]
    return res


def bench_http(base: str) -> list[BenchResult]:
    bq = urllib.parse.urlencode([("biomas", BIOMA)])
    results: list[BenchResult] = []

    endpoints = [
        ("health", f"{base}/health", 1),
        ("configuracion", f"{base}/configuracion", 3),
        ("puntos", f"{base}/puntos", 3),
        ("tiles/col4 (cold-ish)", f"{base}/tiles/col4?year={YEAR}&{bq}", 2),
        ("tiles/col4 (warm)", f"{base}/tiles/col4?year={YEAR}&{bq}", 3),
        ("inventario", f"{base}/inventario?{bq}", 2),
        ("stats/bioma", f"{base}/stats/bioma?{bq}", 2),
        (
            "identificar-clase",
            f"{base}/identificar-clase?lat={LAT}&lon={LON}&year={YEAR}&{bq}",
            3,
        ),
        ("tiles/col3", f"{base}/tiles/col3?year=2020&{bq}", 2),
        ("tiles/bordes", f"{base}/tiles/bordes?{bq}", 2),
        ("stats/bounds/region", f"{base}/stats/bounds/region?id_regionC=30407", 2),
    ]

    for name, url, reps in endpoints:
        results.append(_run_http(name, url, reps))

    # Class filter refetch simulation
    results.append(
        _run_http(
            "tiles/col4 + filter class 3",
            f"{base}/tiles/col4?year={YEAR}&{bq}&class_id=3",
            2,
        )
    )
    return results


def bench_direct() -> list[BenchResult]:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if root not in sys.path:
        sys.path.insert(0, root)
    from backend.services.comparacion_service import (
        identificar_punto,
        inventario_assets,
        obtener_tile_col4,
        obtener_tile_col3,
        obtener_tile_bordes,
    )
    from backend.services.stats_service import estadisticas_bioma, heatmap_bioma
    from backend.services.region_bounds_service import bounds_region, bounds_biomas

    biomas = [BIOMA]
    results: list[BenchResult] = []

    results.append(_run_direct(lambda: inventario_assets(biomas), "direct inventario_assets"))
    results.append(
        _run_direct(
            lambda: obtener_tile_col4(biomas, YEAR),
            "direct obtener_tile_col4 (1st)",
            1,
        )
    )
    results.append(
        _run_direct(
            lambda: obtener_tile_col4(biomas, YEAR),
            "direct obtener_tile_col4 (cached)",
            3,
        )
    )
    results.append(
        _run_direct(
            lambda: identificar_punto(LAT, LON, YEAR, biomas),
            "direct identificar_punto",
            2,
        )
    )
    results.append(
        _run_direct(lambda: estadisticas_bioma(biomas), "direct estadisticas_bioma")
    )
    results.append(
        _run_direct(
            lambda: heatmap_bioma(biomas, "ID03"),
            "direct heatmap_bioma ID03",
        )
    )
    results.append(
        _run_direct(lambda: bounds_biomas(biomas), "direct bounds_biomas (cached after 1st)")
    )
    results.append(
        _run_direct(lambda: bounds_region("30407"), "direct bounds_region")
    )
    results.append(
        _run_direct(
            lambda: obtener_tile_col3(biomas, 2020),
            "direct obtener_tile_col3",
            1,
        )
    )
    results.append(
        _run_direct(lambda: obtener_tile_bordes(biomas), "direct obtener_tile_bordes", 2)
    )
    return results


def print_report(results: list[BenchResult]) -> None:
    print("\n" + "=" * 72)
    print(f"{'Endpoint':<36} {'median':>8} {'p95':>8}  notes")
    print("-" * 72)
    for r in results:
        notes = []
        if "error" in r.extra:
            notes.append(f"ERR: {r.extra['error'][:40]}")
        if "cached" in r.extra:
            notes.append(f"cached={r.extra['cached']}")
        if "rows" in r.extra:
            notes.append(f"rows={r.extra['rows']}")
        if "total_encontrados" in r.extra:
            notes.append(f"assets={r.extra['total_encontrados']}")
        note = ", ".join(notes) if notes else ""
        print(f"{r.name:<36} {r.median_ms:7.0f}ms {r.p95_ms:7.0f}ms  {note}")
    print("=" * 72)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--direct", action="store_true", help="Benchmark Python services directly")
    parser.add_argument("--http", action="store_true", help="Benchmark via HTTP")
    args = parser.parse_args()

    if not args.direct and not args.http:
        args.direct = True
        args.http = True

    all_results: list[BenchResult] = []

    if args.http:
        print(f"HTTP benchmarks -> {args.base}")
        try:
            _http_get(f"{args.base}/health", timeout=5)
        except Exception as e:
            print(f"Backend unreachable: {e}", file=sys.stderr)
            if not args.direct:
                return 1
        else:
            all_results.extend(bench_http(args.base))

    if args.direct:
        print("Direct service benchmarks (EE + SQLite + Sheets)...")
        all_results.extend(bench_direct())

    print_report(all_results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
