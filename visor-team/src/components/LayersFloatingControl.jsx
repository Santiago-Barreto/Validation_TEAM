import React, { useEffect, useRef, useState } from "react";

const LAYER_META = [
  { key: "col4", label: "Colección 4", hasOpacity: true },
  { key: "col3", label: "Colección 3", hasOpacity: true },
  { key: "landsat", label: "Landsat mosaico", hasOpacity: true },
  { key: "bordes", label: "Bordes biomas", hasOpacity: false },
];

/**
 * Capas flotantes. El slider se ve al instante; el mapa actualiza opacidad
 * al soltar (evita re-render en cada tick).
 */
export default function LayersFloatingControl({
  executed,
  layersVisible,
  onToggleLayer,
  opacities,
  onOpacityChange,
}) {
  const [draft, setDraft] = useState(opacities);
  const dragging = useRef(false);

  useEffect(() => {
    if (!dragging.current) setDraft(opacities);
  }, [opacities]);

  const commit = (key, value) => {
    dragging.current = false;
    onOpacityChange(key, value);
  };

  if (!executed) return null;

  return (
    <div className="layers-float" role="region" aria-label="Capas del mapa">
      <header className="layers-float-head">
        <strong>Capas</strong>
      </header>
      <ul className="layers-float-list">
        {LAYER_META.map(({ key, label, hasOpacity }) => {
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
              {hasOpacity && (
                <input
                  type="range"
                  className="layers-float-opacity"
                  min="0"
                  max="1"
                  step="0.05"
                  value={draft[key] ?? 1}
                  disabled={!on}
                  title={`Opacidad ${Math.round((draft[key] ?? 1) * 100)}%`}
                  onPointerDown={() => {
                    dragging.current = true;
                  }}
                  onChange={(e) => {
                    const v = parseFloat(e.target.value);
                    setDraft((prev) => ({ ...prev, [key]: v }));
                  }}
                  onPointerUp={(e) =>
                    commit(key, parseFloat(e.currentTarget.value))
                  }
                  onKeyUp={(e) =>
                    commit(key, parseFloat(e.currentTarget.value))
                  }
                />
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
