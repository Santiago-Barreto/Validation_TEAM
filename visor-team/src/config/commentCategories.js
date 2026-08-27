/** Categorías de comentario para correcciones del equipo. */

export const CAT_CORRECTION = "correction";
export const CAT_CONFIRMED = "confirmed";
export const CAT_DOUBT = "doubt";
export const CAT_NOTE = "note";

export const COMMENT_CATEGORIES = [
  {
    key: CAT_CORRECTION,
    label: "Corrección",
    shortLabel: "Corr.",
    color: "#c0392b",
    description: "Propuesta de cambio de clase",
  },
  {
    key: CAT_CONFIRMED,
    label: "Confirmado",
    shortLabel: "OK",
    color: "#27ae60",
    description: "Clase Col4 correcta",
  },
  {
    key: CAT_DOUBT,
    label: "Duda",
    shortLabel: "?",
    color: "#f39c12",
    description: "Requiere revisión adicional",
  },
  {
    key: CAT_NOTE,
    label: "Nota",
    shortLabel: "Nota",
    color: "#2980b9",
    description: "Observación general",
  },
];

export const CATEGORY_META = Object.fromEntries(
  COMMENT_CATEGORIES.map((c) => [c.key, c]),
);

export const DEFAULT_CATEGORY = CAT_CORRECTION;
