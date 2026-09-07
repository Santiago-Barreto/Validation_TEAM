# Data assets

| File | Purpose |
|------|---------|
| `mapbiomas.db` | SQLite statistics database (Col4 metrics). Not versioned. |
| `COLOMBIA_COL_4_Formatos de avance detallado Colombia.xlsx` | Interpreter lookup (column A × region id in B). |
| `reference/` | Non-runtime reference material (legend PDF source notes). |
| `Global-Solar-Power-Tracker-February-2026.xlsx` | GEM Global Solar Power Tracker. Utility-Scale only. |
| `solar_colombia_utility.json` | Extract: Colombia + operating/construction. Regenerated if the xlsx is newer. |

## Refreshing the statistics database

Copy from the Statistics project when metrics are updated:

```powershell
Copy-Item D:\GAIA2026_desarrollo\Statistics\data\mapbiomas.db `
  D:\GAIA2026_desarrollo\Validation_TEAM\data\mapbiomas.db -Force
```

Adjust the source path to match your Statistics checkout.
