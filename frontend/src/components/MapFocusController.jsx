import { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";

const FOCUS_PANE = "regionFocusPane";
const FOCUS_PANE_Z = 520;

const OUTLINE_STYLE = {
  color: "#ffffff",
  weight: 3,
  opacity: 0.95,
  fillOpacity: 0,
  fill: false,
  interactive: false,
  className: "region-focus-outline",
};

function ensureFocusPane(map) {
  if (!map.getPane(FOCUS_PANE)) {
    map.createPane(FOCUS_PANE);
    const pane = map.getPane(FOCUS_PANE);
    pane.style.zIndex = String(FOCUS_PANE_Z);
    pane.style.pointerEvents = "none";
  }
}

function addOutlineLayer(map, focus) {
  ensureFocusPane(map);
  const bounds = L.latLngBounds(focus.leaflet);
  const geojson = focus.geojson;
  const paneOpts = { pane: FOCUS_PANE };

  if (geojson?.geometry) {
    try {
      const layer = L.geoJSON(geojson, {
        ...paneOpts,
        style: () => OUTLINE_STYLE,
      });
      if (layer.getLayers().length > 0) {
        layer.addTo(map);
        return layer;
      }
    } catch {
      /* fallback bbox */
    }
  }

  const layer = L.rectangle(bounds, { ...OUTLINE_STYLE, ...paneOpts });
  layer.addTo(map);
  return layer;
}

/**
 * Encuadra el mapa y dibuja contorno de región (estable, sin máscara SVG).
 */
export default function MapFocusController({ focus }) {
  const map = useMap();
  const layerRef = useRef(null);
  const lastKeyRef = useRef(null);
  const focusKey = focus?.key ?? null;

  useEffect(() => {
    if (layerRef.current) {
      map.removeLayer(layerRef.current);
      layerRef.current = null;
    }

    if (!focus?.leaflet || focus.leaflet.length !== 2) {
      lastKeyRef.current = null;
      return undefined;
    }

    const bounds = L.latLngBounds(focus.leaflet);
    if (!bounds.isValid()) return undefined;

    layerRef.current = addOutlineLayer(map, focus);

    if (lastKeyRef.current !== focusKey) {
      lastKeyRef.current = focusKey;
      map.fitBounds(bounds, {
        paddingTopLeft: [40, 40],
        paddingBottomRight: focus.paddingBottomRight || [40, 320],
        maxZoom: focus.maxZoom ?? 11,
        animate: true,
        duration: 0.35,
      });
    }

    return () => {
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
        layerRef.current = null;
      }
    };
  }, [map, focusKey]);

  return null;
}
