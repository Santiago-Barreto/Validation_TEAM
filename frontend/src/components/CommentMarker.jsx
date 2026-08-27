import React, { useCallback, useMemo, useState } from "react";
import { Marker, Popup, Tooltip, useMap } from "react-leaflet";
import L from "leaflet";
import { COMMENT_META } from "../config/commentCategories";
import { API_URL } from "../config/api";
import { authHeaders } from "../services/authStorage";
import { useAuth } from "../auth/AuthContext";

function escapeAttr(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function commentIcon(fotoUrl, label) {
  const initial = escapeAttr(
    ((label || "?").trim().charAt(0) || "?").toUpperCase(),
  );
  const photo = fotoUrl ? escapeAttr(fotoUrl) : "";
  const photoHtml = photo
    ? `<img class="team-pin-photo" src="${photo}" alt="" referrerpolicy="no-referrer" onerror="this.style.display='none'" />`
    : "";

  return L.divIcon({
    className: "team-marker-icon",
    html: `<div class="team-pin team-pin-avatar" style="--pin:${COMMENT_META.color}"><span class="team-pin-initial">${initial}</span>${photoHtml}</div>`,
    iconSize: [36, 36],
    iconAnchor: [18, 36],
    popupAnchor: [0, -34],
  });
}

function CommentMarker({ punto, onResolved }) {
  const map = useMap();
  const { isAuthenticated } = useAuth();
  const [busy, setBusy] = useState(false);
  const [imgFailed, setImgFailed] = useState(false);

  const autor =
    (punto.nombre || "").trim() ||
    (punto.creadoPor || "").trim() ||
    "Sin nombre";

  const icon = useMemo(
    () => commentIcon(punto.fotoUrl, autor),
    [punto.fotoUrl, autor],
  );

  const onClick = useCallback(() => {
    map.flyTo([punto.lat, punto.lng], Math.max(map.getZoom(), 14), {
      duration: 0.7,
    });
  }, [map, punto.lat, punto.lng]);

  const resolve = async () => {
    if (busy) return;
    if (!isAuthenticated) {
      window.alert("Inicia sesión con tu correo Gaia Amazonas para resolver.");
      return;
    }
    if (!punto.grupoId && !punto.timestamp) return;

    const nGrupo = punto.grupoId
      ? " Se ocultarán todos los puntos del mismo comentario."
      : "";
    if (
      !window.confirm(
        `¿Resolver este comentario?${nGrupo}`,
      )
    ) {
      return;
    }

    setBusy(true);
    try {
      const body = punto.grupoId
        ? { grupo_id: punto.grupoId, resuelto: "check" }
        : {
            timestamp: punto.timestamp,
            lat: punto.lat,
            lon: punto.lng,
            resuelto: "check",
          };
      const res = await fetch(`${API_URL}/resolver`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        window.alert(err.detail || "No se pudo resolver el comentario");
        return;
      }
      onResolved?.(punto.grupoId || punto.id);
    } catch {
      window.alert("Error de red al resolver el comentario");
    } finally {
      setBusy(false);
    }
  };

  const showPhoto = Boolean(punto.fotoUrl) && !imgFailed;
  const initial = (autor.charAt(0) || "?").toUpperCase();

  return (
    <Marker
      position={[punto.lat, punto.lng]}
      icon={icon}
      eventHandlers={{ click: onClick }}
    >
      <Tooltip direction="top" offset={[0, -28]} opacity={1}>
        <strong>{autor}</strong>
        <br />
        {punto.comment?.slice(0, 80) || "—"}
      </Tooltip>
      <Popup>
        <div className="comment-popup">
          <div className="comment-popup-head">
            {showPhoto ? (
              <img
                className="comment-popup-avatar"
                src={punto.fotoUrl}
                alt=""
                referrerPolicy="no-referrer"
                onError={() => setImgFailed(true)}
              />
            ) : (
              <span className="comment-popup-avatar fallback" aria-hidden="true">
                {initial}
              </span>
            )}
            <div>
              <strong className="comment-popup-email-main">{autor}</strong>
            </div>
          </div>
          <p>{punto.comment || "—"}</p>
          <small>
            {punto.claseSugerida != null
              ? `Clase sugerida: ${punto.claseSugerida}`
              : "Sin clase sugerida"}
            {punto.anioContexto != null ? ` · ${punto.anioContexto}` : ""}
            {punto.bioma ? ` · ${punto.bioma}` : ""}
            {punto.grupoId ? " · grupo" : ""}
          </small>
          <div className="comment-resolve-actions">
            <button
              type="button"
              className="resolve-btn resolve-ok"
              disabled={busy}
              title={
                punto.grupoId
                  ? "Resolver todo el grupo"
                  : "Marcar resuelto"
              }
              onClick={resolve}
            >
              ✓ Resolver{punto.grupoId ? " grupo" : ""}
            </button>
          </div>
        </div>
      </Popup>
    </Marker>
  );
}

export default React.memo(CommentMarker);
