import { useEffect } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";

/**
 * Anima el mapa hacia un bbox Leaflet [[s,w],[n,e]] y opcionalmente
 * dibuja el contorno de la región enfocada.
 */
export default function MapFocusController({ focus }) {
  const map = useMap();
  const focusKey = focus?.key;

  useEffect(() => {
    if (!focus?.leaflet || focus.leaflet.length !== 2) return undefined;

    const bounds = L.latLngBounds(focus.leaflet);
    if (!bounds.isValid()) return undefined;

    map.flyToBounds(bounds, {
      paddingTopLeft: [40, 40],
      paddingBottomRight: focus.paddingBottomRight || [40, 320],
      maxZoom: focus.maxZoom ?? 11,
      duration: focus.duration ?? 1.15,
      easeLinearity: 0.2,
    });

    let layer = null;
    if (focus.geojson?.geometry) {
      layer = L.geoJSON(focus.geojson, {
        style: {
          color: "#fff8e1",
          weight: 3,
          opacity: 0.95,
          fillColor: "#ffca28",
          fillOpacity: 0.14,
          dashArray: "7 5",
          className: "region-focus-outline",
        },
      }).addTo(map);
    }

    return () => {
      if (layer) map.removeLayer(layer);
    };
    // Solo reaccionar al cambio de ámbito (key), no a re-renders del objeto.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, focusKey]);

  return null;
}
