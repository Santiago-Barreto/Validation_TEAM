import React from "react";

function formatInspector(identify, clickPos, year, loading) {
  if (loading) return "Consultando…";
  if (!clickPos) return "Haz clic en el mapa para consultar";
  if (identify?.error) return identify.message || "Error al consultar";
  if (identify?.fuera_de_area) {
    const reg = identify.region;
    const regLine = reg?.id_regionC
      ? `\nRegión: ${reg.id_regionC} · ${reg.bioma || "—"}`
      : "";
    return `Fuera de área${regLine}`;
  }
  if (!identify) return "Sin datos";

  const v4 = identify.col4?.id;
  const nombreV4 =
    v4 == null ? "N/A" : identify.col4?.nombre || `Clase ${v4}`;

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
    `COLECCIÓN 4 · ${year}\n` +
    `Clase: ${v4 ?? "N/A"} - ${nombreV4}`
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
  commentMode,
  onToggleCommentMode,
  commentsVisible = true,
  onToggleCommentsVisible,
  queuedOfflineCount,
  clickPos,
  identify,
  loadingIdentify,
  identifyYear,
}) {
  const inspectorText = formatInspector(
    identify,
    clickPos,
    identifyYear ?? year,
    loadingIdentify,
  );

  return (
    <aside className="control-panel">
      <header className="control-header">
        <p className="brand-kicker">GAIA · MapBiomas Colombia</p>
        <h1>LULC TEAM</h1>
        <p className="control-sub">Colección 4 · Colombia</p>
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
        <h2>Comentarios</h2>
        <button
          type="button"
          className={`btn ${commentMode ? "btn-accent" : "btn-ghost"}`}
          onClick={onToggleCommentMode}
          disabled={!executed}
          aria-pressed={commentMode}
          title={
            commentMode
              ? "Desactivar modo comentarios"
              : "Activar modo comentarios (Colombia / bioma ejecutado)"
          }
        >
          {commentMode
            ? "Desactivar modo comentarios"
            : "Activar modo comentarios"}
        </button>
        <button
          type="button"
          className={`btn ${commentsVisible ? "btn-accent" : "btn-ghost"}`}
          onClick={onToggleCommentsVisible}
          disabled={!executed}
          aria-pressed={commentsVisible}
          title={
            commentsVisible
              ? "Ocultar comentarios en el mapa"
              : "Mostrar comentarios en el mapa"
          }
          style={{ marginTop: "0.45rem" }}
        >
          {commentsVisible ? "Ocultar comentarios" : "Mostrar comentarios"}
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
