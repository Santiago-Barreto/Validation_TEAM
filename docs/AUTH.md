# Authentication (Gaia Amazonas)

Validation TEAM uses **Google Sign-In** restricted to `@gaiaamazonas.org`.

## What is tracked

| Action | Sheet columns |
|--------|----------------|
| Create comment | `nombre`, `creado_por` (email), `foto_url` (Google picture) |
| Resolve ✓ / ✗ | `resuelto`, `resuelto_por` (email) |

## One-time Google Cloud setup

1. Open [Google Cloud Console](https://console.cloud.google.com/) (same project as EE is fine).
2. **APIs & Services → Credentials → Create credentials → OAuth client ID**.
3. Application type: **Web application**.
4. Authorized JavaScript origins:
   - `http://localhost:5173`
   - `http://127.0.0.1:5173`
   - `http://127.0.0.1:8000`
5. Copy the **Client ID** into `backend/.env`:

```env
GOOGLE_OAUTH_CLIENT_ID=xxxxx.apps.googleusercontent.com
AUTH_ALLOWED_DOMAINS=gaiaamazonas.org
```

6. Restart uvicorn.

## OAuth consent screen

- User type: **Internal** (if the Workspace is Gaia Amazonas), or External with test users.
- App name: Validation TEAM.

Only emails ending in `@gaiaamazonas.org` can sign in. Others receive HTTP 403.

Any signed-in user can create and resolve comments. `creado_por` / `resuelto_por` record their email.

## Sheet row

```
timestamp | lat | lon | nombre | comentario | clase_sugerida | anio_contexto | bioma | resuelto | creado_por | resuelto_por | foto_url | grupo_id
```
