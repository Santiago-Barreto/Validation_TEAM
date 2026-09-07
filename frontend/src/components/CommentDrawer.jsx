import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { API_URL } from "../config/api";
import { DEFAULT_CATEGORY } from "../config/commentCategories";
import { useAuth } from "../auth/AuthContext";
import { authHeaders } from "../services/authStorage";
import { enqueueOfflineComment, getQueuedCount } from "../services/offlineQueue";
import { newGrupoId } from "../utils/normalizeComment";

export default function CommentDrawer({
  draftPoints,
  year,
  biomas,
  onClose,
  onSaved,
  onQueueChanged,
  onClearDrafts,
  editingComment = null,
}) {
  const { user } = useAuth();
  const [comentario, setComentario] = useState("");
  const [claseSugerida, setClaseSugerida] = useState("");
  const [enviando, setEnviando] = useState(false);
  const isEdit = Boolean(editingComment);

  useEffect(() => {
    if (!editingComment) return;
    setComentario(editingComment.comment || "");
    setClaseSugerida(
      editingComment.claseSugerida != null
        ? String(editingComment.claseSugerida)
        : "",
    );
  }, [editingComment]);

  const n = draftPoints?.length || 0;
  if (!isEdit && !n) return null;

  const handleEdit = async () => {
    if (!comentario.trim()) {
      window.alert("El comentario es obligatorio.");
      return;
    }
    if (!user?.email) {
      window.alert("Debes iniciar sesión con tu correo Gaia Amazonas.");
      return;
    }
    const body = editingComment.grupoId
      ? {
          grupo_id: editingComment.grupoId,
          comentario: comentario.trim(),
          clase_sugerida: claseSugerida ? Number(claseSugerida) : null,
        }
      : {
          timestamp: editingComment.timestamp,
          lat: editingComment.lat,
          lon: editingComment.lng,
          comentario: comentario.trim(),
          clase_sugerida: claseSugerida ? Number(claseSugerida) : null,
        };
    setEnviando(true);
    try {
      const res = await fetch(`${API_URL}/editar`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        window.alert(err.detail || "No se pudo guardar el cambio");
        return;
      }
      onSaved?.();
      onClose();
    } catch {
      window.alert("Error de red al editar el comentario");
    } finally {
      setEnviando(false);
    }
  };

  const handleSave = async () => {
    if (isEdit) {
      await handleEdit();
      return;
    }
    if (!comentario.trim()) {
      window.alert("El comentario es obligatorio.");
      return;
    }
    if (!user?.email) {
      window.alert("Debes iniciar sesión con tu correo Gaia Amazonas.");
      return;
    }
    if (!biomas?.length) {
      window.alert("Ejecuta al menos un bioma antes de crear comentarios.");
      return;
    }

    const grupoId = newGrupoId();
    const biomasQuery = biomas
      .map((b) => `biomas=${encodeURIComponent(b)}`)
      .join("&");
    const lote = {
      puntos: draftPoints.map((p) => ({ lat: p.lat, lon: p.lng })),
      nombre: (user.name || user.email || "").trim(),
      comentario: comentario.trim(),
      clasificacion: DEFAULT_CATEGORY,
      anio_contexto: year,
      bioma: biomas?.[0] || "",
      clase_sugerida: claseSugerida ? Number(claseSugerida) : null,
      creado_por: user.email,
      grupo_id: grupoId,
    };

    setEnviando(true);
    try {
      if (!navigator.onLine) {
        for (const p of draftPoints) {
          enqueueOfflineComment(
            {
              lat: p.lat,
              lon: p.lng,
              nombre: lote.nombre,
              comentario: lote.comentario,
              clasificacion: DEFAULT_CATEGORY,
              anio_contexto: year,
              bioma: lote.bioma,
              clase_sugerida: lote.clase_sugerida,
              creado_por: user.email,
              grupo_id: grupoId,
            },
            biomas,
          );
        }
        onQueueChanged?.(getQueuedCount());
        window.alert(
          `Sin conexión: ${n} punto(s) guardados en cola local (mismo grupo).`,
        );
        onClearDrafts?.();
        onSaved?.();
        onClose();
        return;
      }

      const res = await fetch(`${API_URL}/guardar-lote?${biomasQuery}`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify(lote),
      });

      if (res.ok) {
        const body = await res.json().catch(() => ({}));
        if (body.rechazados > 0) {
          window.alert(
            `Se guardaron ${body.guardados} de ${n} puntos. ` +
              `${body.rechazados} fuera de Colombia.`,
          );
        }
        onClearDrafts?.();
        onSaved?.();
        onClose();
        return;
      }

      if (res.status === 401 || res.status === 403) {
        const err = await res.json().catch(() => ({}));
        window.alert(err.detail || "Sesión inválida. Vuelve a iniciar sesión.");
        return;
      }

      const err = await res.json().catch(() => ({}));
      const detail = Array.isArray(err.detail)
        ? err.detail.map((d) => d.msg || d).join("\n")
        : err.detail;
      window.alert(detail || "Error al guardar");
    } catch {
      for (const p of draftPoints) {
        enqueueOfflineComment(
          {
            lat: p.lat,
            lon: p.lng,
            nombre: lote.nombre,
            comentario: lote.comentario,
            clasificacion: DEFAULT_CATEGORY,
            anio_contexto: year,
            bioma: lote.bioma,
            clase_sugerida: lote.clase_sugerida,
            creado_por: user.email,
            grupo_id: grupoId,
          },
          biomas,
        );
      }
      onQueueChanged?.(getQueuedCount());
      window.alert(
        `Sin conexión: ${n} punto(s) guardados en cola local (mismo grupo).`,
      );
      onClearDrafts?.();
      onSaved?.();
      onClose();
    } finally {
      setEnviando(false);
    }
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
        <h2 id="comment-drawer-title">
          {isEdit ? "Editar comentario" : "Comentario de corrección"}
        </h2>
        <button type="button" className="btn-close" onClick={onClose}>
          Cerrar
        </button>
      </div>

      <p className="drawer-meta">
        {isEdit
          ? editingComment.grupoId
            ? "Se actualiza el texto en todos los puntos del grupo."
            : "Solo se actualiza este comentario."
          : `${n} punto${n === 1 ? "" : "s"} en el mapa`}
        {year != null ? ` · año ${year}` : ""}
      </p>
      <p className="drawer-meta auth-meta">
        Sesión: {user?.email || "sin autenticar"}
      </p>
      {!isEdit && (
        <>
          <p className="drawer-meta auth-meta">
            Sigue haciendo clic para agregar más punteros. Clic en uno ya
            colocado para quitarlo.
          </p>

          <div className="draft-point-actions">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={onClearDrafts}
              disabled={enviando}
            >
              Limpiar puntos
            </button>
          </div>
        </>
      )}

      <label className="field-label" htmlFor="comentario">
        Comentario corrección
      </label>
      <textarea
        id="comentario"
        rows={4}
        value={comentario}
        onChange={(e) => setComentario(e.target.value)}
        placeholder="Describe la corrección…"
      />

      <label className="field-label" htmlFor="sugerida">
        Clase sugerida
      </label>
      <input
        id="sugerida"
        type="number"
        value={claseSugerida}
        onChange={(e) => setClaseSugerida(e.target.value)}
        placeholder="ej. 21"
      />

      <button
        type="button"
        className="btn btn-primary drawer-submit"
        disabled={enviando || (!isEdit && n < 1)}
        onClick={handleSave}
      >
        {enviando
          ? "Guardando…"
          : isEdit
            ? "Guardar cambios"
            : `Enviar ${n} punto${n === 1 ? "" : "s"}`}
      </button>
    </motion.div>
  );
}
