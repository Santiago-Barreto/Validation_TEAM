/**
 * URL del API: local en desarrollo; Render en producción (mismo patrón que Validation).
 */
export const API_URL =
  window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : "https://mapbiomas-colombia-validator.onrender.com";
