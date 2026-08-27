/**
 * Panel flotante de estadísticas de bioma / región.
 * Optimizado: Plotly lazy, heatmap bajo demanda, sin texto en celdas.
 */

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence, useDragControls, useMotionValue } from "framer-motion";
import LazyPlot from "./LazyPlot";
import { API_URL } from "../config/api";

function formatHa(ha) {
  if (ha == null || Number.isNaN(Number(ha))) return "—";
  return Number(ha).toLocaleString("es-CO", { maximumFractionDigits: 0 });
}

const HEAT_COLORSCALE = [
  [0, "#b71c1c"],
  [0.35, "#ef9a9a"],
  [0.5, "#f5f5f5"],
  [0.65, "#a5d6a7"],
  [1, "#1b5e20"],
];

const plotConfig = {
  displayModeBar: true,
  displaylogo: false,
  modeBarButtonsToRemove: [
    "lasso2d",
    "select2d",
    "autoScale2d",
    "zoomIn2d",
    "zoomOut2d",
  ],
  responsive: false,
  staticPlot: false,
};

const PLOT_FONT = { family: "inherit", size: 11, color: "#e8eef2" };
const AXIS_DARK = {
  gridcolor: "#2a333c",
  zerolinecolor: "#3d4a55",
  linecolor: "#4a5560",
  tickfont: { color: "#c5d0da" },
  title: { font: { color: "#c5d0da" } },
};

export default function StatsFloatingPanel({
  open,
  biomeStats,
  loadingStats,
  executedBiomas = [],
  onMapFocus,
}) {
  const [minimized, setMinimized] = useState(true);
  const [showTable, setShowTable] = useState(false);
  const [scope, setScope] = useState("bioma");
  const [regionStats, setRegionStats] = useState(null);
  const [loadingRegion, setLoadingRegion] = useState(false);
  const [heatClass, setHeatClass] = useState("");
  const [heat, setHeat] = useState(null);
  const [loadingHeat, setLoadingHeat] = useState(false);
  const focusRequestRef = useRef(0);
  const dragControls = useDragControls();
  const panelX = useMotionValue(0);
  const panelY = useMotionValue(0);

  const executedKey = useMemo(
    () => executedBiomas.slice().sort().join("|"),
    [executedBiomas],
  );

  const snapPanelCorner = useCallback(() => {
    panelX.set(0);
    panelY.set(0);
  }, [panelX, panelY]);

  const regiones = biomeStats?.regiones || [];

  useEffect(() => {
    if (open) {
      setMinimized(true);
      snapPanelCorner();
    }
  }, [open, executedKey, snapPanelCorner]);

  useEffect(() => {
    if (!open) onMapFocus?.(null);
  }, [open, onMapFocus]);

  useEffect(() => {
    setScope("bioma");
    setRegionStats(null);
    onMapFocus?.(null);
  }, [executedKey, onMapFocus]);

  useEffect(() => {
    const first = biomeStats?.class_ids?.[0] || "";
    if (first) setHeatClass(first);
  }, [executedKey, biomeStats?.class_ids]);

  useEffect(() => {
    if (!open || !onMapFocus) return undefined;

    if (scope === "bioma") {
      onMapFocus(null);
      return undefined;
    }

    const requestId = ++focusRequestRef.current;

    fetch(`${API_URL}/stats/bounds?region_id=${encodeURIComponent(scope)}`)
      .then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => {
        if (requestId !== focusRequestRef.current || !data?.leaflet) return;
        onMapFocus({
          key: `region-${data.region_id || scope}`,
          kind: "region",
          leaflet: data.leaflet,
          geojson: data.geojson || null,
          maxZoom: 11,
          paddingBottomRight: [48, 360],
        });
      })
      .catch((err) => {
        console.warn("Zoom región:", err);
        if (requestId === focusRequestRef.current) onMapFocus(null);
      });

    return undefined;
  }, [scope, open, onMapFocus]);

  useEffect(() => {
    if (scope === "bioma") {
      setRegionStats(null);
      return undefined;
    }
    let cancelled = false;
    setLoadingRegion(true);
    fetch(`${API_URL}/stats/region?region_id=${encodeURIComponent(scope)}`)
      .then(async (r) => {
        if (!r.ok) {
          const err = await r.json().catch(() => ({}));
          throw new Error(err.detail || `HTTP ${r.status}`);
        }
        return r.json();
      })
      .then((data) => {
        if (!cancelled) setRegionStats(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setRegionStats({
            disponible: false,
            mensaje: err.message || "No se pudieron cargar stats de región",
          });
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingRegion(false);
      });
    return () => {
      cancelled = true;
    };
  }, [scope]);

  // Heatmap bajo demanda (no viaja en /stats/bioma)
  useEffect(() => {
    if (
      !open ||
      scope !== "bioma" ||
      !heatClass ||
      !biomeStats?.has_heatmap ||
      !executedBiomas.length
    ) {
      setHeat(null);
      return undefined;
    }
    let cancelled = false;
    setLoadingHeat(true);
    const bq = executedBiomas
      .map((b) => `biomas=${encodeURIComponent(b)}`)
      .join("&");
    fetch(
      `${API_URL}/stats/bioma/heatmap?${bq}&class_id=${encodeURIComponent(heatClass)}`,
    )
      .then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => {
        if (!cancelled) setHeat(data);
      })
      .catch((err) => {
        console.warn("Heatmap:", err);
        if (!cancelled) setHeat(null);
      })
      .finally(() => {
        if (!cancelled) setLoadingHeat(false);
      });
    return () => {
      cancelled = true;
    };
  }, [
    open,
    scope,
    heatClass,
    biomeStats?.has_heatmap,
    executedBiomas,
  ]);

  const activeStats = scope === "bioma" ? biomeStats : regionStats;
  const loading = scope === "bioma" ? loadingStats : loadingRegion || loadingStats;

  const plotTraces = useMemo(() => {
    if (!activeStats?.disponible || !activeStats.rows?.length) return [];
    const { rows, class_ids: classIds, leyenda } = activeStats;
    return classIds.map((ck) => {
      const info = leyenda?.[ck] || {};
      return {
        type: "scatter",
        mode: "lines",
        name: info.label || ck,
        x: rows.map((r) => r.year),
        y: rows.map((r) => r[ck] ?? 0),
        line: { color: info.color || "#888", width: 2 },
        hovertemplate: `%{x}: %{y:,.0f} ha<extra>${info.label || ck}</extra>`,
      };
    });
  }, [activeStats]);

  const tableRows = useMemo(() => {
    if (!activeStats?.rows?.length) return [];
    return [...activeStats.rows].sort((a, b) => b.year - a.year);
  }, [activeStats]);

  const m = activeStats?.metrics || {};
  const plotKey = `${scope}-${activeStats?.titulo || "x"}`;
  const heatHeight = Math.min(420, 48 + (heat?.regions?.length || 0) * 22);
  const heatWidth = Math.max(960, (heat?.periods?.length || 0) * 28);

  return (
    <AnimatePresence>
      {open && (
        <motion.aside
          className={`stats-float ${minimized ? "is-min" : ""}`}
          style={{ x: panelX, y: panelY }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          drag
          dragControls={dragControls}
          dragListener={false}
          dragMomentum={false}
          dragElastic={0.08}
        >
          <header
            className="stats-float-head stats-float-drag-handle"
            onPointerDown={(event) => dragControls.start(event)}
          >
            <div>
              <h2>{activeStats?.titulo || biomeStats?.titulo || "Estadísticas"}</h2>
              <p className="stats-float-sub">
                Colección 4 · Panel analítico (Statistics)
              </p>
            </div>
            <div className="stats-float-actions">
              <button
                type="button"
                className="stats-icon-btn"
                onPointerDown={(event) => event.stopPropagation()}
                onClick={() => {
                  setMinimized((wasMin) => {
                    if (!wasMin) snapPanelCorner();
                    return !wasMin;
                  });
                }}
                title={minimized ? "Expandir" : "Minimizar"}
              >
                {minimized ? "▢" : "—"}
              </button>
            </div>
          </header>

          {!minimized && (
            <div className="stats-float-body">
              {regiones.length > 0 && (
                <label className="stats-scope">
                  <span>Ámbito</span>
                  <select
                    value={scope}
                    onChange={(e) => setScope(e.target.value)}
                    disabled={loadingStats}
                  >
                    <option value="bioma">
                      Bioma completo
                      {biomeStats?.n_regiones
                        ? ` (${biomeStats.n_regiones} regiones)`
                        : ""}
                    </option>
                    {regiones.map((r) => (
                      <option key={r.region_id} value={r.region_id}>
                        {r.label}
                        {r.bioma ? ` · ${r.bioma}` : ""}
                      </option>
                    ))}
                  </select>
                </label>
              )}

              {loading ? (
                <p className="muted">Cargando datos…</p>
              ) : !activeStats?.disponible ? (
                <p className="muted">
                  {activeStats?.mensaje || "Sin estadísticas para este ámbito."}
                </p>
              ) : (
                <>
                  <div className="stats-metrics">
                    <div className="stats-metric">
                      <span className="stats-metric-label">Años</span>
                      <strong>
                        {m.year_min} – {m.year_max}
                      </strong>
                    </div>
                    <div className="stats-metric">
                      <span className="stats-metric-label">Versiones</span>
                      <strong>{m.n_versiones ?? 1}</strong>
                    </div>
                    <div className="stats-metric">
                      <span className="stats-metric-label">Coberturas</span>
                      <strong>{m.n_coberturas ?? 0}</strong>
                    </div>
                    <div className="stats-metric">
                      <span className="stats-metric-label">Regiones</span>
                      <strong>
                        {scope === "bioma"
                          ? (biomeStats?.n_regiones ?? 0)
                          : 1}
                      </strong>
                    </div>
                  </div>

                  <h3 className="stats-section-title">
                    Tendencia: {activeStats.titulo}
                  </h3>
                  <div className="stats-plot-wrap">
                    <LazyPlot
                      key={plotKey}
                      data={plotTraces}
                      layout={{
                        margin: { t: 8, r: 16, b: 72, l: 56 },
                        height: 380,
                        autosize: true,
                        uirevision: plotKey,
                        paper_bgcolor: "#000000",
                        plot_bgcolor: "#000000",
                        xaxis: { ...AXIS_DARK, title: { ...AXIS_DARK.title, text: "Año" }, dtick: 5 },
                        yaxis: {
                          ...AXIS_DARK,
                          title: { ...AXIS_DARK.title, text: "Hectáreas" },
                          separatethousands: true,
                        },
                        legend: {
                          orientation: "h",
                          yanchor: "top",
                          y: -0.22,
                          x: 0,
                          xanchor: "left",
                          font: { size: 10, color: "#e8eef2" },
                          bgcolor: "rgba(0,0,0,0.75)",
                          bordercolor: "#2a333c",
                        },
                        font: PLOT_FONT,
                        hovermode: "closest",
                        hoverlabel: {
                          bgcolor: "#111",
                          font: { color: "#fff" },
                          bordercolor: "#444",
                        },
                      }}
                      config={plotConfig}
                      style={{ width: "100%", height: "100%" }}
                    />
                  </div>

                  <button
                    type="button"
                    className="stats-table-toggle"
                    onClick={() => setShowTable((v) => !v)}
                  >
                    {showTable ? "▾" : "▸"} Datos consolidados
                  </button>

                  {showTable && (
                    <div className="stats-table-wrap">
                      <table className="stats-table">
                        <thead>
                          <tr>
                            <th>year</th>
                            {(activeStats.class_ids || []).map((ck) => (
                              <th
                                key={ck}
                                title={activeStats.leyenda?.[ck]?.label}
                              >
                                {ck}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {tableRows.map((row) => (
                            <tr key={row.year}>
                              <td className="num">{row.year}</td>
                              {(activeStats.class_ids || []).map((ck) => (
                                <td key={ck} className="num">
                                  {formatHa(row[ck])}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {scope === "bioma" && biomeStats?.has_heatmap && (
                    <section className="stats-heat-section">
                      <h3 className="stats-section-title">
                        Aportes regionales · ganancias y pérdidas
                      </h3>
                      <p className="stats-heat-caption">
                        Δ ha por región y periodo (valores al pasar el cursor).
                      </p>
                      <label className="stats-scope">
                        <span>Cobertura</span>
                        <select
                          value={heatClass}
                          onChange={(e) => setHeatClass(e.target.value)}
                        >
                          {(biomeStats.class_ids || []).map((ck) => (
                            <option key={ck} value={ck}>
                              {biomeStats.leyenda?.[ck]?.label || ck}
                            </option>
                          ))}
                        </select>
                      </label>

                      {loadingHeat ? (
                        <p className="muted">Cargando heatmap…</p>
                      ) : !heat?.periods?.length ? (
                        <p className="muted">
                          Se requieren al menos dos años para el heatmap.
                        </p>
                      ) : (
                        <div className="stats-heat-scroll">
                          <div
                            className="stats-plot-wrap stats-heat-wrap"
                            style={{ height: heatHeight, width: heatWidth }}
                          >
                            <LazyPlot
                              key={`heat-${heatClass}`}
                              data={[
                                {
                                  type: "heatmap",
                                  z: heat.z,
                                  x: heat.periods,
                                  y: heat.regions,
                                  colorscale: HEAT_COLORSCALE,
                                  zmid: 0,
                                  zmin: -heat.zmax,
                                  zmax: heat.zmax,
                                  colorbar: {
                                    title: { text: "Δ ha", side: "right", font: { color: "#e8eef2" } },
                                    thickness: 12,
                                    tickfont: { size: 9, color: "#c5d0da" },
                                    bgcolor: "#000000",
                                  },
                                  hovertemplate:
                                    "%{y}<br>%{x}: %{z:,.0f} ha<extra></extra>",
                                },
                              ]}
                              layout={{
                                margin: { t: 8, r: 48, b: 56, l: 64 },
                                height: heatHeight,
                                width: heatWidth,
                                uirevision: `heat-${heatClass}`,
                                paper_bgcolor: "#000000",
                                plot_bgcolor: "#000000",
                                xaxis: {
                                  ...AXIS_DARK,
                                  title: { ...AXIS_DARK.title, text: "Periodo" },
                                  tickangle: -45,
                                  tickfont: { size: 8, color: "#c5d0da" },
                                  nticks: 20,
                                },
                                yaxis: {
                                  ...AXIS_DARK,
                                  title: { ...AXIS_DARK.title, text: "Región" },
                                  autorange: "reversed",
                                  tickfont: { size: 10, color: "#c5d0da" },
                                },
                                font: PLOT_FONT,
                                hoverlabel: {
                                  bgcolor: "#111",
                                  font: { color: "#fff" },
                                  bordercolor: "#444",
                                },
                              }}
                              config={plotConfig}
                              style={{ width: "100%", height: "100%" }}
                            />
                          </div>
                        </div>
                      )}
                    </section>
                  )}

                  {(
                    (activeStats.faltantes || []).length > 0 ||
                    (biomeStats?.faltantes || []).length > 0
                  ) && (
                    <section className="stats-missing">
                      <h3 className="stats-section-title">
                        Assets sin estadísticas en BD
                      </h3>
                      <ul className="stats-missing-list">
                        {(
                          activeStats.faltantes?.length
                            ? activeStats.faltantes
                            : biomeStats?.faltantes || []
                        ).map((tag) => (
                          <li key={tag}>
                            <code>{tag}</code>
                          </li>
                        ))}
                      </ul>
                    </section>
                  )}
                </>
              )}
            </div>
          )}
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
