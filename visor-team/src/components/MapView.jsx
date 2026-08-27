import React, { memo } from "react";
import { MapContainer, TileLayer, Marker } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";

import MapClickHandler from "./MapClickHandler";
import CommentMarker from "./CommentMarker";
import MapFocusController from "./MapFocusController";
import { BASEMAPS, COLOMBIA_CENTER, COLOMBIA_ZOOM } from "../config/basemaps";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

const clickIcon = L.divIcon({
  className: "pixel-highlight",
  iconSize: [14, 14],
  iconAnchor: [7, 7],
});

const clusterIcon = (cluster) => {
  const n = cluster.getChildCount();
  return L.divIcon({
    html: `<div class="cluster-disk"><span>${n}</span></div>`,
    className: "cluster-wrap",
    iconSize: L.point(40, 40),
  });
};

function MapView({
  activeBasemap,
  tiles,
  opacities,
  comentarios,
  clickPos,
  clickEnabled,
  onMapClick,
  year,
  mapFocus,
}) {
  const basemap = BASEMAPS[activeBasemap] || BASEMAPS.satelite;
  const showLandsatLayer = Boolean(tiles.landsat);

  return (
    <MapContainer
      center={COLOMBIA_CENTER}
      zoom={COLOMBIA_ZOOM}
      className="map-root"
      zoomControl
    >
      <TileLayer url={basemap.url} attribution={basemap.attribution} />

      {showLandsatLayer && (
        <TileLayer
          key={`landsat-${year}`}
          url={tiles.landsat}
          opacity={opacities.landsat !== undefined ? opacities.landsat : 1}
          zIndex={5}
        />
      )}
      {tiles.col3 && (
        <TileLayer
          url={tiles.col3}
          opacity={opacities.col3 ?? 0.85}
          zIndex={300}
        />
      )}
      {tiles.col4 && (
        <TileLayer
          url={tiles.col4}
          opacity={opacities.col4 ?? 1}
          zIndex={400}
        />
      )}
      {tiles.bordes && (
        <TileLayer url={tiles.bordes} opacity={1} zIndex={500} />
      )}

      <MapFocusController focus={mapFocus} />
      <MapClickHandler enabled={clickEnabled} onClick={onMapClick} />

      {clickPos && (
        <Marker position={[clickPos.lat, clickPos.lng]} icon={clickIcon} />
      )}

      <MarkerClusterGroup
        chunkedLoading
        showCoverageOnHover={false}
        iconCreateFunction={clusterIcon}
      >
        {comentarios.map((p) => (
          <CommentMarker key={p.id} punto={p} />
        ))}
      </MarkerClusterGroup>
    </MapContainer>
  );
}

export default memo(MapView);
