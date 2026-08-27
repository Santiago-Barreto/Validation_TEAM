import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          plotly: ["plotly.js-cartesian-dist", "react-plotly.js"],
          leaflet: ["leaflet", "react-leaflet", "react-leaflet-cluster"],
        },
      },
    },
    chunkSizeWarningLimit: 1200,
  },
});
