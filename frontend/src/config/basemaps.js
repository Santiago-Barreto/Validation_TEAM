export const BASEMAPS = {
  satelite: {
    label: "Google Maps",
    // Teselas satelitales actuales de Google Maps (misma fuente que maps.google.com).
    url: "https://mt{s}.google.com/vt/lyrs=s&hl=es-419&gl=co&x={x}&y={y}&z={z}",
    subdomains: ["0", "1", "2", "3"],
    maxZoom: 21,
    maxNativeZoom: 21,
    attribution: "Google",
  },
  osm: {
    label: "OSM",
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: "© OpenStreetMap",
    maxZoom: 19,
  },
};

export const COLOMBIA_CENTER = [4.5, -73.0];
export const COLOMBIA_ZOOM = 6;
