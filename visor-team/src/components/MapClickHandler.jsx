import { useMapEvents } from "react-leaflet";

export default function MapClickHandler({ enabled, onClick }) {
  useMapEvents({
    click(e) {
      if (!enabled) return;
      onClick?.(e.latlng);
    },
  });
  return null;
}
