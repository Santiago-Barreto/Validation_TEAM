# Backend runtime data

| File | Versioned | Purpose |
|------|-----------|---------|
| `comentarios_team.example.json` | Yes | Empty template for local JSON comment store |
| `comentarios_team.json` | No (gitignored) | Live comments when `PUNTOS_BACKEND=json` |

To use local JSON mode:

```powershell
Copy-Item backend\data\comentarios_team.example.json backend\data\comentarios_team.json
```

Set in `backend/.env`:

```
PUNTOS_BACKEND=json
```

Default deployment uses Google Sheets (`PUNTOS_BACKEND=sheets`).
