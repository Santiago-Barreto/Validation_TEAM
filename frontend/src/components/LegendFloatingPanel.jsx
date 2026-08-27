import React, { useState } from "react";

export default function LegendFloatingPanel({
  executed,
  leyenda = [],
  selectedClasses = [],
  onToggleClass,
  onClearClasses,
}) {
  const [open, setOpen] = useState(true);
  const hasFilter = selectedClasses.length > 0;

  if (!executed || !leyenda.length) return null;

  return (
    <aside
      className={`legend-float${open ? " is-open" : " is-collapsed"}${hasFilter ? " has-filter" : ""}`}
      role="region"
      aria-label="Leyenda Colección 4"
    >
      <header className="legend-float-head">
        <div className="legend-float-head-main">
          <strong>Leyenda Col4</strong>
          {hasFilter && (
            <span className="legend-float-filter-badge">
              {selectedClasses.length} filtro
              {selectedClasses.length === 1 ? "" : "s"}
            </span>
          )}
        </div>
        <button
          type="button"
          className="stats-icon-btn"
          onClick={() => setOpen((v) => !v)}
          title={open ? "Minimizar leyenda" : "Mostrar leyenda"}
          aria-expanded={open}
        >
          {open ? "—" : "▢"}
        </button>
      </header>
      {open && (
        <div className="legend-float-body">
          <p className="legend-float-hint muted">
            Clic en una clase para filtrar el mapa. Sin selección = mapa
            completo.
          </p>
          {hasFilter && (
            <button
              type="button"
              className="btn btn-small legend-float-clear"
              onClick={onClearClasses}
            >
              Mostrar todas
            </button>
          )}
          {leyenda.map((grupo) => (
            <section key={grupo.titulo} className="legend-float-grupo">
              <h3>{grupo.titulo}</h3>
              <ul className="legend-float-list">
                {grupo.clases.map((c) => {
                  const selected = selectedClasses.includes(c.id);
                  return (
                    <li key={c.id}>
                      <button
                        type="button"
                        className={`legend-float-item${selected ? " is-selected" : ""}`}
                        onClick={() => onToggleClass(c.id)}
                        aria-pressed={selected}
                        title={
                          selected
                            ? "Quitar filtro de esta clase"
                            : "Filtrar mapa por esta clase"
                        }
                      >
                        <span
                          className="leyenda-swatch legend-float-swatch"
                          style={{ background: c.color || "#ccc" }}
                          aria-hidden="true"
                        />
                        <span className="legend-float-label">
                          <span className="legend-float-id">{c.id}</span>
                          {c.label}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </section>
          ))}
        </div>
      )}
    </aside>
  );
}
