import React, { memo, useCallback } from "react";
import { MapContainer, TileLayer, Marker } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";

import MapClickHandler from "./MapClickHandler";
import CommentMarker from "./CommentMarker";
import MapFocusController from "./MapFocusController";
import SolarMarkers from "./SolarMarkers";
import { SwipeDivider, SwipeLayers } from "./MapSwipe";
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

const draftIcon = L.divIcon({
  className: "draft-comment-marker",
  html: '<div class="draft-pin"></div>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
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
  layersVisible,
  comentarios,
  draftPoints = [],
  onDraftPointClick,
  clickPos,
  clickEnabled,
  onMapClick,
  year,
  mapFocus,
  onCommentResolved,
  onCommentEdit,
  solarPlants = [],
  landsatStyle = "green",
  swipeMode = false,
  swipeRatio = 0.5,
  onSwipeRatioChange,
}) {
  const basemap = BASEMAPS[activeBasemap] || BASEMAPS.satelite;
  const showLandsat = Boolean(layersVisible?.landsat && tiles.landsat);
  const showCol4 = Boolean(layersVisible?.col4 && tiles.col4);
  const showBordes = Boolean(layersVisible?.bordes && tiles.bordes);

  const handleSplit = useCallback(
    (r) => onSwipeRatioChange?.(r),
    [onSwipeRatioChange],
  );

  return (
    <MapContainer
      center={COLOMBIA_CENTER}
      zoom={COLOMBIA_ZOOM}
      maxZoom={basemap.maxZoom || 21}
      className={`map-root${swipeMode ? " map-root-swipe" : ""}`}
      zoomControl
    >
      <TileLayer
        url={basemap.url}
        attribution={basemap.attribution}
        subdomains={basemap.subdomains}
        maxZoom={basemap.maxZoom || 21}
        maxNativeZoom={basemap.maxNativeZoom || basemap.maxZoom || 21}
      />

      {swipeMode ? (
        <>
          <SwipeLayers
            leftUrl={tiles.landsat}
            rightUrl={tiles.col4}
            splitRatio={swipeRatio}
            leftEnabled={showLandsat}
            rightEnabled={showCol4}
          />
          <SwipeDivider
            splitRatio={swipeRatio}
            onSplitChange={handleSplit}
            leftLabel="Landsat"
            rightLabel="Col4"
          />
        </>
      ) : (
        <>
          {showLandsat && (
            <TileLayer
              key={`landsat-${year}-${landsatStyle || "green"}`}
              url={tiles.landsat}
              opacity={1}
              zIndex={5}
            />
          )}
          {showCol4 && (
            <TileLayer url={tiles.col4} opacity={1} zIndex={400} />
          )}
        </>
      )}

      {showBordes && (
        <TileLayer url={tiles.bordes} opacity={1} zIndex={500} />
      )}

      {solarPlants.length > 0 && <SolarMarkers plants={solarPlants} />}

      <MapFocusController focus={mapFocus} />
      <MapClickHandler enabled={clickEnabled} onClick={onMapClick} />

      {draftPoints.map((p) => (
        <Marker
          key={p.id}
          position={[p.lat, p.lng]}
          icon={draftIcon}
          eventHandlers={{
            click: (e) => {
              L.DomEvent.stopPropagation(e);
              onDraftPointClick?.(p.id);
            },
          }}
        />
      ))}

      {clickPos && !draftPoints.length && (
        <Marker position={[clickPos.lat, clickPos.lng]} icon={clickIcon} />
      )}

      <MarkerClusterGroup
        chunkedLoading
        showCoverageOnHover={false}
        iconCreateFunction={clusterIcon}
      >
        {comentarios.map((p) => (
          <CommentMarker
            key={p.id}
            punto={p}
            onResolved={onCommentResolved}
            onEdit={onCommentEdit}
          />
        ))}
      </MarkerClusterGroup>
    </MapContainer>
  );
}

export default memo(MapView);
