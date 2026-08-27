import React from "react";

function formatInspector(identify, clickPos, year, loading) {
  if (loading) return "Consultando…";
  if (!clickPos) return "Haz clic en el mapa para comparar";
  if (identify?.error) return identify.message || "Error al consultar";
  if (identify?.fuera_de_area) {
    const reg = identify.region;
    const regLine = reg?.id_regionC
      ? `\nRegión: ${reg.id_regionC} · ${reg.bioma || "—"}`
      : "";
    return `Fuera de área${regLine}`;
  }
  if (!identify) return "Sin datos";

  const v3 = identify.col3?.id;
  const v4 = identify.col4?.id;
  const nombreV3 =
    v3 == null ? "N/A" : identify.col3?.nombre || `Clase ${v3}`;
  const nombreV4 =
    v4 == null ? "N/A" : identify.col4?.nombre || `Clase ${v4}`;
  const v3Text = v3 == null ? "N/A" : String(v3);

  let cambio = "— Solo Col 4";
  if (identify.cambio === "sin_cambios") cambio = "Sin cambios";
  else if (identify.cambio === "detectado") cambio = "Detectado";
  else if (v3 != null) cambio = "Detectado";

  const reg = identify.region;
  const regionBlock = reg
    ? `REGIÓN\n` +
      `id_regionC: ${reg.id_regionC ?? "N/A"}\n` +
      `Bioma: ${reg.bioma ?? "N/A"}\n` +
      (reg.tag_col4 ? `Asset Col4: ${reg.tag_col4}\n` : "") +
      (reg.interprete_responsable
        ? `Intérprete responsable: ${reg.interprete_responsable}\n`
        : "") +
      `\n`
    : "";

  return (
    `COORDENADAS\n` +
    `Lat: ${clickPos.lat.toFixed(5)} Lon: ${clickPos.lng.toFixed(5)}\n\n` +
    regionBlock +
    `RESULTADOS ${year}\n` +
    `Col 3: ${v3Text} - ${nombreV3}\n` +
    `Col 4: ${v4 ?? "N/A"} - ${nombreV4}\n` +
    `Cambio: ${cambio}`
  );
}

export default function ControlPanel({
  config,
  selectedBiomas,
  onToggleBioma,
  onEjecutar,
  executed,
  inventario,
  loadingTiles,
  year,
  onYearChange,
  yearMin,
  yearMax,
  showCoberturas,
  onToggleCoberturasPanel,
  selectedClasses,
  onToggleClass,
  onClearClasses,
  commentMode,
  onToggleCommentMode,
  queuedOfflineCount,
  clickPos,
  identify,
  loadingIdentify,
  identifyYear,
}) {
  const leyenda = config?.leyenda || [];
  const inspectorText = formatInspector(
    identify,
    clickPos,
    identifyYear ?? year,
    loadingIdentify,
  );

  return (
    <aside className="control-panel">
      <header className="control-header">
        <h1>MapBiomas Colombia</h1>
        <p className="control-sub">Validation TEAM · Col3 vs Col4</p>
      </header>

      <section className="panel-block">
        <h2>Selección de biomas</h2>
        <div className="checkbox-list">
          {(config?.biomasVisibles || []).map((b) => (
            <label key={b} className="check-row">
              <input
                type="checkbox"
                checked={selectedBiomas.includes(b)}
                onChange={() => onToggleBioma(b)}
              />
              <span>{b}</span>
            </label>
          ))}
        </div>
        <button
          type="button"
          className="btn btn-primary"
          onClick={onEjecutar}
          disabled={!selectedBiomas.length || loadingTiles}
        >
          {loadingTiles ? "Cargando…" : "Ejecutar"}
        </button>
      </section>

      {inventario && (
        <section className="panel-block inventario">
          <h2>Assets Col4</h2>
          <p className="muted">
            Encontrados: {inventario.total_encontrados} · Faltantes:{" "}
            {inventario.total_faltantes}
          </p>
          {(inventario.encontrados || []).length > 0 && (
            <details className="inventario-details">
              <summary>Encontrados ({inventario.encontrados.length})</summary>
              <pre className="inventario-pre">
                {inventario.encontrados.join("\n")}
              </pre>
            </details>
          )}
          {(inventario.faltantes || []).length > 0 && (
            <details className="inventario-details is-warn" open>
              <summary>
                Faltantes en GEE ({inventario.faltantes.length})
              </summary>
              <pre className="inventario-pre warn-list">
                {inventario.faltantes.join("\n")}
              </pre>
            </details>
          )}
        </section>
      )}

      <section className="panel-block">
        <h2>Año: {year}</h2>
        <input
          type="range"
          className="year-slider"
          min={yearMin}
          max={yearMax}
          step={1}
          value={year}
          disabled={!executed}
          onChange={(e) => onYearChange(Number(e.target.value))}
        />
        <div className="year-ends">
          <span>{yearMin}</span>
          <span>{yearMax}</span>
        </div>
      </section>

      <section className="panel-block">
        <h2>Inspector</h2>
        <pre className="inspector-pre">{inspectorText}</pre>
      </section>

      <section className="panel-block">
        <button
          type="button"
          className="btn btn-ghost"
          onClick={onToggleCoberturasPanel}
          disabled={!executed}
        >
          {showCoberturas
            ? "Ocultar filtro de coberturas"
            : "Mostrar filtro de coberturas"}
        </button>
        {showCoberturas && (
          <div className="coberturas-scroll">
            <p className="muted">
              Sin selección = mapa completo. Con selección = solo esas clases.
            </p>
            <button
              type="button"
              className="btn btn-small"
              onClick={onClearClasses}
            >
              Mostrar todas
            </button>
            {leyenda.map((grupo) => (
              <div key={grupo.titulo} className="cobertura-grupo">
                <strong>{grupo.titulo}</strong>
                {grupo.clases.map((c) => (
                  <label key={c.id} className="check-row">
                    <input
                      type="checkbox"
                      checked={selectedClasses.includes(c.id)}
                      onChange={() => onToggleClass(c.id)}
                    />
                    <span
                      className="leyenda-swatch"
                      style={{ background: c.color || "#ccc" }}
                      title={c.color}
                    />
                    <span>
                      [{c.id}] {c.label}
                    </span>
                  </label>
                ))}
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="panel-block">
        <h2>Comentarios</h2>
        <button
          type="button"
          className={`btn ${commentMode ? "btn-accent" : "btn-ghost"}`}
          onClick={onToggleCommentMode}
          disabled={!executed}
        >
          {commentMode
            ? "Modo comentario activo — clic abre formulario"
            : "Activar modo comentario (guardar)"}
        </button>
        {queuedOfflineCount > 0 && (
          <p className="offline-badge">
            {queuedOfflineCount} pendiente(s) offline
          </p>
        )}
      </section>
    </aside>
  );
}
