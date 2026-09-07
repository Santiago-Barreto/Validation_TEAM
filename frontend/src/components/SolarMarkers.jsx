import React, { memo, useMemo } from "react";
import { Marker, Popup, Tooltip } from "react-leaflet";
import L from "leaflet";

const ICONS = {
  operating: L.divIcon({
    className: "solar-marker-icon",
    html: '<div class="solar-pin is-operating" title="Operating">☀</div>',
    iconSize: [22, 22],
    iconAnchor: [11, 11],
    popupAnchor: [0, -10],
  }),
  construction: L.divIcon({
    className: "solar-marker-icon",
    html: '<div class="solar-pin is-construction" title="Construction">☀</div>',
    iconSize: [22, 22],
    iconAnchor: [11, 11],
    popupAnchor: [0, -10],
  }),
};

function statusLabel(status) {
  if (status === "operating") return "Operating";
  if (status === "construction") return "Construction";
  return status || "—";
}

function SolarMarkers({ plants }) {
  const items = useMemo(() => plants || [], [plants]);
  if (!items.length) return null;

  return (
    <>
      {items.map((p) => (
        <Marker
          key={p.id}
          position={[p.lat, p.lon]}
          icon={ICONS[p.status] || ICONS.operating}
        >
          <Tooltip direction="top" offset={[0, -8]} opacity={1}>
            <strong>{p.name}</strong>
            <br />
            {statusLabel(p.status)}
            {p.mw != null ? ` · ${p.mw} MW` : ""}
          </Tooltip>
          <Popup>
            <div className="solar-popup">
              <strong>{p.name}</strong>
              {p.phase ? <p className="solar-popup-phase">{p.phase}</p> : null}
              <p>
                {statusLabel(p.status)}
                {p.mw != null ? ` · ${p.mw} MW` : ""}
                {p.tech ? ` · ${p.tech}` : ""}
              </p>
              <small>
                {p.province || "—"}
                {p.bioma ? ` · ${p.bioma}` : ""}
              </small>
              {p.wiki ? (
                <p>
                  <a href={p.wiki} target="_blank" rel="noreferrer">
                    GEM wiki
                  </a>
                </p>
              ) : null}
            </div>
          </Popup>
        </Marker>
      ))}
    </>
  );
}

export default memo(SolarMarkers);
