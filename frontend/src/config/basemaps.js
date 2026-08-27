export const BASEMAPS = {
  satelite: {
    label: "Satélite",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: "Esri",
  },
  osm: {
    label: "OSM",
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: "© OpenStreetMap",
  },
};

export const COLOMBIA_CENTER = [4.5, -73.0];
export const COLOMBIA_ZOOM = 6;
