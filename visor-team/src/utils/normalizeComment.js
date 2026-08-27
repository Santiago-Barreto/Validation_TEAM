import { CATEGORY_META, CAT_NOTE } from "../config/commentCategories";

/**
 * Normaliza fila API → marcador.
 * Formato TEAM:
 * timestamp | lat | lon | comentario | nombre | clasificacion | anio |
 * clase_col3 | clase_col4 | bioma | clase_sugerida
 */
export function normalizeCommentRow(row) {
  if (!row || row.length < 5) return null;
  const lat = parseFloat(row[1]);
  const lng = parseFloat(row[2]);
  if (Number.isNaN(lat) || Number.isNaN(lng)) return null;

  const clasificacion = String(row[5] ?? "").trim();
  const meta = CATEGORY_META[clasificacion] ? clasificacion : CAT_NOTE;

  const ts = row[0] != null ? String(row[0]) : "";
  const id = `c-${ts}-${row[1]}-${row[2]}`.replace(/\s+/g, "");

  const parseOptInt = (v) => {
    if (v === null || v === undefined || v === "") return null;
    const n = parseInt(String(v), 10);
    return Number.isNaN(n) ? null : n;
  };

  return {
    id,
    lat,
    lng,
    comment: row[3] ?? "",
    nombre: row[4] ?? "",
    clasificacion: meta,
    anioContexto: parseOptInt(row[6]),
    claseCol3: parseOptInt(row[7]),
    claseCol4: parseOptInt(row[8]),
    bioma: row[9] ? String(row[9]) : "",
    claseSugerida: parseOptInt(row[10]),
    rawRow: row,
  };
}
