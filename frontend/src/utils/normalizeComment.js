import { COMMENT_META } from "../config/commentCategories";

/**
 * timestamp | lat | lon | nombre | comentario | clase_sugerida | anio | bioma | resuelto | creado_por | resuelto_por | foto_url | grupo_id
 */
export function normalizeCommentRow(row) {
  if (!row || row.length < 5) return null;
  const lat = parseFloat(row[1]);
  const lng = parseFloat(row[2]);
  if (Number.isNaN(lat) || Number.isNaN(lng)) return null;

  const timestamp = row[0] != null ? String(row[0]) : "";
  const grupoId = row[12] ? String(row[12]).trim() : "";
  const id =
    grupoId ||
    `c-${timestamp}-${row[1]}-${row[2]}`.replace(/\s+/g, "");

  const parseOptInt = (v) => {
    if (v === null || v === undefined || v === "") return null;
    const n = parseInt(String(v), 10);
    return Number.isNaN(n) ? null : n;
  };

  const resuelto = String(row[8] ?? "")
    .trim()
    .toLowerCase();

  return {
    id: `${id}-${lat}-${lng}`,
    grupoId,
    timestamp,
    lat,
    lng,
    nombre: row[3] ?? "",
    comment: row[4] ?? "",
    clasificacion: COMMENT_META.key,
    claseSugerida: parseOptInt(row[5]),
    anioContexto: parseOptInt(row[6]),
    bioma: row[7] ? String(row[7]) : "",
    resuelto: resuelto === "check" || resuelto === "x" ? resuelto : "",
    creadoPor: row[9] ? String(row[9]) : "",
    resueltoPor: row[10] ? String(row[10]) : "",
    fotoUrl: row[11] ? String(row[11]).trim() : "",
    rawRow: row,
  };
}

export function newGrupoId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `g-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}
