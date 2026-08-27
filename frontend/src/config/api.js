/**
 * URL del API:
 * - Vite dev (5173): backend en :8000
 * - Build estático (.exe o producción): mismo origen (ruta relativa)
 */
export const API_URL = import.meta.env.DEV ? "http://127.0.0.1:8000" : "";
