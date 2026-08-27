import { useState } from "react";
import { motion } from "framer-motion";
import { API_URL } from "../config/api";
import {
  COMMENT_CATEGORIES,
  DEFAULT_CATEGORY,
} from "../config/commentCategories";
import { enqueueOfflineComment, getQueuedCount } from "../services/offlineQueue";

export default function CommentDrawer({
  clickPos,
  identify,
  loadingIdentify,
  year,
  biomas,
  onClose,
  onSaved,
  onQueueChanged,
}) {
  const [nombre, setNombre] = useState("");
  const [comentario, setComentario] = useState("");
  const [clasificacion, setClasificacion] = useState(DEFAULT_CATEGORY);
  const [claseSugerida, setClaseSugerida] = useState("");
  const [enviando, setEnviando] = useState(false);

  if (!clickPos) return null;

  const handleSave = async () => {
    if (!nombre.trim() || !comentario.trim()) {
      window.alert("Nombre y comentario son obligatorios.");
      return;
    }

    const payload = {
      lat: clickPos.lat,
      lon: clickPos.lng,
      nombre: nombre.trim(),
      comentario: comentario.trim(),
      clasificacion,
      anio_contexto: year,
      clase_col3: identify?.col3?.id ?? null,
      clase_col4: identify?.col4?.id ?? null,
      bioma: identify?.region?.bioma || biomas?.[0] || "",
      clase_sugerida: claseSugerida ? Number(claseSugerida) : null,
    };

    const persistOffline = () => {
      enqueueOfflineComment(payload);
      onQueueChanged?.(getQueuedCount());
      window.alert("Sin conexión: comentario guardado en cola local.");
      onClose();
    };

    setEnviando(true);
    try {
      if (!navigator.onLine) {
        persistOffline();
        return;
      }
      const res = await fetch(`${API_URL}/guardar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        onSaved?.();
        onClose();
      } else {
        const err = await res.json().catch(() => ({}));
        window.alert(err.detail || "Error al guardar");
      }
    } catch {
      persistOffline();
    } finally {
      setEnviando(false);
    }
  };

  const cambioLabel = {
    sin_cambios: "Sin cambios",
    detectado: "Detectado",
    solo_col4: "— Solo Col 4",
  };

  return (
    <motion.div
      className="comment-drawer"
      initial={{ x: 48, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ type: "spring", damping: 26, stiffness: 300 }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="comment-drawer-title"
    >
      <div className="drawer-header">
        <h2 id="comment-drawer-title">Comentario de validación</h2>
        <button type="button" className="btn-close" onClick={onClose}>
          Cerrar
        </button>
      </div>

      <p className="drawer-meta">
        {clickPos.lat.toFixed(5)}, {clickPos.lng.toFixed(5)} · año {year}
      </p>

      <section className="drawer-identify">
        <h3>Comparación {year}</h3>
        {loadingIdentify ? (
          <div className="shimmer" />
        ) : identify?.fuera_de_area ? (
          <p className="warn">Fuera de área</p>
        ) : identify ? (
          <ul>
            {identify.region && (
              <li>
                <span>Región</span>
                <strong>
                  {identify.region.id_regionC ?? "N/A"}
                  {identify.region.bioma ? ` · ${identify.region.bioma}` : ""}
                  {identify.region.tag_col4
                    ? ` · ${identify.region.tag_col4}`
                    : ""}
                </strong>
              </li>
            )}
            <li>
              <span>Col 3</span>
              <strong>
                {identify.col3?.id ?? "N/A"} — {identify.col3?.nombre ?? "N/A"}
              </strong>
            </li>
            <li>
              <span>Col 4</span>
              <strong>
                {identify.col4?.id ?? "N/A"} — {identify.col4?.nombre ?? "N/A"}
              </strong>
            </li>
            <li>
              <span>Cambio</span>
              <strong>{cambioLabel[identify.cambio] || identify.cambio}</strong>
            </li>
          </ul>
        ) : (
          <p className="muted">Sin datos</p>
        )}
      </section>

      <label className="field-label">Tipo</label>
      <div className="cat-grid">
        {COMMENT_CATEGORIES.map((c) => (
          <button
            key={c.key}
            type="button"
            className={`cat-chip ${clasificacion === c.key ? "active" : ""}`}
            style={{ "--chip": c.color }}
            onClick={() => setClasificacion(c.key)}
            title={c.description}
          >
            {c.label}
          </button>
        ))}
      </div>

      <label className="field-label" htmlFor="nombre">
        Nombre / validador
      </label>
      <input
        id="nombre"
        value={nombre}
        onChange={(e) => setNombre(e.target.value)}
        placeholder="Tu nombre o iniciales"
      />

      <label className="field-label" htmlFor="comentario">
        Comentario / corrección
      </label>
      <textarea
        id="comentario"
        rows={4}
        value={comentario}
        onChange={(e) => setComentario(e.target.value)}
        placeholder="Describe la observación o la clase esperada…"
      />

      {clasificacion === "correction" && (
        <>
          <label className="field-label" htmlFor="sugerida">
            Clase sugerida (opcional)
          </label>
          <input
            id="sugerida"
            type="number"
            value={claseSugerida}
            onChange={(e) => setClaseSugerida(e.target.value)}
            placeholder="ej. 21"
          />
        </>
      )}

      <button
        type="button"
        className="btn btn-primary drawer-submit"
        disabled={enviando}
        onClick={handleSave}
      >
        {enviando ? "Enviando…" : "Guardar comentario"}
      </button>
    </motion.div>
  );
}
