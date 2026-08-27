import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useMap } from "react-leaflet";
import L from "leaflet";

function applyLayerClip(map, layer, side, splitRatio) {
  const container = layer?.getContainer?.();
  if (!container) return;

  const nw = map.containerPointToLayerPoint([0, 0]);
  const se = map.containerPointToLayerPoint(map.getSize());
  const clipX = nw.x + (se.x - nw.x) * splitRatio;

  if (side === "left") {
    container.style.clip = `rect(${nw.y}px, ${clipX}px, ${se.y}px, ${nw.x}px)`;
  } else {
    container.style.clip = `rect(${nw.y}px, ${se.x}px, ${se.y}px, ${clipX}px)`;
  }
}

/**
 * TileLayer Leaflet con clip horizontal (barra vertical).
 * Usa coordenadas de capa Leaflet (igual que leaflet-side-by-side).
 */
function ClippedTileLayer({ url, paneName, side, splitRatio }) {
  const map = useMap();
  const layerRef = useRef(null);
  const splitRef = useRef(splitRatio);
  splitRef.current = splitRatio;
  const sideRef = useRef(side);
  sideRef.current = side;

  useEffect(() => {
    if (!map.getPane(paneName)) {
      map.createPane(paneName);
      const pane = map.getPane(paneName);
      pane.style.zIndex = side === "left" ? "450" : "451";
      pane.style.pointerEvents = "none";
    }
  }, [map, paneName, side]);

  useEffect(() => {
    if (!url) return undefined;

    const layer = L.tileLayer(url, {
      opacity: 1,
      maxZoom: 22,
      pane: paneName,
      className: "swipe-tile-layer",
    });
    layer.addTo(map);
    layerRef.current = layer;

    const applyClip = () => {
      applyLayerClip(map, layerRef.current, sideRef.current, splitRef.current);
    };

    layer.on("load", applyClip);
    layer.on("add", applyClip);
    map.on("move zoom moveend zoomend resize viewreset", applyClip);
    requestAnimationFrame(applyClip);
    const t = window.setTimeout(applyClip, 120);

    return () => {
      window.clearTimeout(t);
      layer.off("load", applyClip);
      layer.off("add", applyClip);
      map.off("move zoom moveend zoomend resize viewreset", applyClip);
      map.removeLayer(layer);
      layerRef.current = null;
    };
  }, [map, url, paneName]);

  useEffect(() => {
    applyLayerClip(map, layerRef.current, side, splitRatio);
  }, [map, splitRatio, side]);

  return null;
}

/**
 * Barra vertical arrastrable sobre el mapa.
 */
export function SwipeDivider({ splitRatio, onSplitChange, leftLabel, rightLabel }) {
  const map = useMap();
  const dragging = useRef(false);
  const [host, setHost] = useState(null);

  useEffect(() => {
    const node = L.DomUtil.create("div", "map-swipe-host");
    map.getContainer().appendChild(node);
    L.DomEvent.disableClickPropagation(node);
    L.DomEvent.disableScrollPropagation(node);
    setHost(node);
    return () => {
      L.DomUtil.remove(node);
      setHost(null);
    };
  }, [map]);

  useEffect(() => {
    const container = map.getContainer();

    const posFromEvent = (e) => {
      const rect = container.getBoundingClientRect();
      const x = e.clientX - rect.left;
      return Math.max(0.02, Math.min(0.98, x / rect.width));
    };

    const onMove = (e) => {
      if (!dragging.current) return;
      onSplitChange(posFromEvent(e));
    };
    const onUp = () => {
      if (!dragging.current) return;
      dragging.current = false;
      map.dragging.enable();
      container.classList.remove("is-swiping");
    };

    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
  }, [map, onSplitChange]);

  if (!host) return null;

  const onPointerDown = (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragging.current = true;
    map.dragging.disable();
    map.getContainer().classList.add("is-swiping");
    const rect = map.getContainer().getBoundingClientRect();
    onSplitChange(
      Math.max(0.02, Math.min(0.98, (e.clientX - rect.left) / rect.width)),
    );
  };

  return createPortal(
    <div
      className="map-swipe-divider"
      style={{ left: `${splitRatio * 100}%` }}
      onPointerDown={onPointerDown}
      role="slider"
      aria-orientation="vertical"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(splitRatio * 100)}
      aria-label="Comparar capas con swipe"
    >
      <div className="map-swipe-line" />
      <div className="map-swipe-handle">
        <span>{leftLabel}</span>
        <span className="map-swipe-grip" aria-hidden="true">
          ⋮
        </span>
        <span>{rightLabel}</span>
      </div>
    </div>,
    host,
  );
}

export function SwipeLayers({
  leftUrl,
  rightUrl,
  splitRatio,
  leftEnabled,
  rightEnabled,
}) {
  return (
    <>
      {leftEnabled && leftUrl ? (
        <ClippedTileLayer
          url={leftUrl}
          paneName="swipeLeftPane"
          side="left"
          splitRatio={splitRatio}
        />
      ) : null}
      {rightEnabled && rightUrl ? (
        <ClippedTileLayer
          url={rightUrl}
          paneName="swipeRightPane"
          side="right"
          splitRatio={splitRatio}
        />
      ) : null}
    </>
  );
}

export default SwipeLayers;
