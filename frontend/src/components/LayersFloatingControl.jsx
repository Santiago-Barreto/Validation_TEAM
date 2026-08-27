import React from "react";

const LAYER_META = [
  { key: "col4", label: "Colección 4" },
  { key: "landsat", label: "Landsat mosaico" },
  { key: "bordes", label: "Bordes biomas" },
];

export default function LayersFloatingControl({
  executed,
  layersVisible,
  onToggleLayer,
  landsatStyle,
  landsatStyles,
  onLandsatStyleChange,
  swipeMode,
  onToggleSwipe,
}) {
  if (!executed) return null;

  const styles =
    landsatStyles?.length > 0
      ? landsatStyles
      : [
          { id: "green", label: "Mosaic Green" },
          { id: "red", label: "Mosaic Red" },
          { id: "gamma", label: "Mosaic Gamma" },
        ];

  return (
    <div className="layers-float" role="region" aria-label="Capas del mapa">
      <header className="layers-float-head">
        <strong>Capas</strong>
      </header>

      <button
        type="button"
        className={`btn layers-swipe-toggle${swipeMode ? " is-active" : ""}`}
        aria-pressed={swipeMode}
        onClick={onToggleSwipe}
        title="Swipe vertical: Landsat (izq.) vs Colección 4 (der.)"
      >
        Swipe Col4 / Landsat
      </button>

      <ul className="layers-float-list">
        {LAYER_META.map(({ key, label }) => {
          const on = !!layersVisible[key];
          return (
            <li key={key} className={`layers-float-item ${on ? "is-on" : ""}`}>
              <label className="layers-float-check">
                <input
                  type="checkbox"
                  checked={on}
                  onChange={() => onToggleLayer(key)}
                />
                <span>{label}</span>
              </label>
              {key === "landsat" && on && (
                <label className="layers-float-style">
                  <span>Combinación</span>
                  <select
                    value={landsatStyle || "green"}
                    onChange={(e) => onLandsatStyleChange?.(e.target.value)}
                  >
                    {styles.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </label>
              )}
            </li>
          );
        })}
      </ul>
      {swipeMode && (
        <p className="layers-swipe-hint">
          Modo swipe activo: arrastra la barra vertical. Landsat a la izquierda,
          Col4 a la derecha. Si apagas una capa, se ve el basemap.
        </p>
      )}
    </div>
  );
}
