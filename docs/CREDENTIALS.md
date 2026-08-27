# Credenciales y secretos

## Archivos locales

| Archivo | Uso |
|---------|-----|
| `backend/credentials.json` | Service account Google (solo EE). Misma cuenta que Validation está bien. |
| `backend/data/comentarios_team.json` | **Almacén por defecto** de comentarios TEAM (aislado de Validation). |

## Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `GOOGLE_CREDENTIALS` | JSON de la service account (producción Render). |
| `PUNTOS_BACKEND` | Default `json`. También: `sheets` \| `database` \| `auto` |
| `PUNTOS_JSON_PATH` | Ruta del JSON TEAM (default `backend/data/comentarios_team.json`) |
| `GOOGLE_SHEET_ID` | Solo si usas Sheets: ID de una hoja **propia de TEAM**. Vacío = no Sheets. |
| `DATABASE_URL` | PostgreSQL (opcional) |

## Buenas prácticas

- **No** reutilizar la hoja Google de Validation; los comentarios de ambos proyectos no deben mezclarse.
- No subir `credentials.json` a repositorios públicos.
- Desarrollo local: deja `PUNTOS_BACKEND=json` (ya es el default).
