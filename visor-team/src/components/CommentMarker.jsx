import React, { useCallback } from "react";
import { Marker, Popup, Tooltip, useMap } from "react-leaflet";
import L from "leaflet";
import { CATEGORY_META } from "../config/commentCategories";

function iconFor(clasificacion) {
  const meta = CATEGORY_META[clasificacion] || CATEGORY_META.note;
  const color = meta.color;
  const label = meta.shortLabel;
  return L.divIcon({
    className: "team-marker-icon",
    html: `<div class="team-pin" style="--pin:${color}"><span>${label}</span></div>`,
    iconSize: [36, 36],
    iconAnchor: [18, 36],
    popupAnchor: [0, -34],
  });
}

function CommentMarker({ punto }) {
  const map = useMap();
  const onClick = useCallback(() => {
    map.flyTo([punto.lat, punto.lng], Math.max(map.getZoom(), 14), {
      duration: 0.7,
    });
  }, [map, punto.lat, punto.lng]);

  return (
    <Marker
      position={[punto.lat, punto.lng]}
      icon={iconFor(punto.clasificacion)}
      eventHandlers={{ click: onClick }}
    >
      <Tooltip direction="top" offset={[0, -28]} opacity={1}>
        <strong>{punto.nombre || "Sin nombre"}</strong>
        <br />
        {punto.comment?.slice(0, 80) || "—"}
      </Tooltip>
      <Popup>
        <div className="comment-popup">
          <strong>{punto.nombre || "Sin nombre"}</strong>
          <p>{punto.comment || "—"}</p>
          <small>
            {punto.clasificacion}
            {punto.anioContexto != null ? ` · ${punto.anioContexto}` : ""}
            {punto.bioma ? ` · ${punto.bioma}` : ""}
          </small>
          {(punto.claseCol3 != null || punto.claseCol4 != null) && (
            <p className="comment-popup-classes">
              Col3: {punto.claseCol3 ?? "—"} → Col4: {punto.claseCol4 ?? "—"}
              {punto.claseSugerida != null
                ? ` · sugerida: ${punto.claseSugerida}`
                : ""}
            </p>
          )}
        </div>
      </Popup>
    </Marker>
  );
}

export default React.memo(CommentMarker);
