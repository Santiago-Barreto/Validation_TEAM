# Performance — Validation TEAM

Mediciones reales (2026-08-27, bioma **Caribe**, año **2025**, backend local + Earth Engine + Google Sheets).

Script reproducible:

```powershell
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --app-dir .
python scripts/benchmark_perf.py --http --direct
```

## Resultados medidos

| Operación | Mediana | P95 | Notas |
|-----------|---------|-----|-------|
| `GET /health` | 21 ms | 21 ms | OK |
| `GET /configuracion` | 1 ms | 1 ms | Sin caché, payload pequeño |
| `GET /puntos` (Sheets) | 201 ms | 424 ms | Descarga hoja completa + sync JSON |
| `GET /tiles/col4` (caché caliente) | 2 ms | 4 ms | TTL 2 h, max 256 entradas |
| `GET /tiles/col4` (caché fría / EE) | ~2.2 s | ~3.1 s | `getMapId()` en Earth Engine |
| `GET /inventario` | 2.7 s | 3.1 s | **Sin caché** — `aggregate_array().getInfo()` |
| `GET /stats/bioma` | 42 ms | 53 ms | SQLite local (~23 KB JSON) |
| `GET /identificar-clase` | **5.0 s** | **5.1 s** | Hasta 4× `getInfo()` secuenciales |
| `identificar_punto` (directo) | **10.7 s** | **12.0 s** | Mismo cuello, peor bajo carga |
| `bounds_region` (directo, frío) | **12.6 s** | **25.2 s** | Geometría EE + simplificación |
| `obtener_tile_col3` (frío) | 1.6 s | 1.6 s | Doble mosaico + máscara |
| `obtener_tile_bordes` (frío) | 244 ms | 488 ms | Más liviano |
| `list_registros` Sheets (directo) | 1.3 s | — | 8 filas; escala con tamaño hoja |

### Flujo típico de usuario

**Al pulsar Ejecutar** (Col4 visible, sin Landsat/Col3):

| Paralelo | Tiempo dominante |
|----------|------------------|
| `/tiles/col4` (frío) | ~2 s |
| `/inventario` | ~2.7 s |
| `/stats/bioma` | ~50 ms |
| `/puntos` (ya en mount) | ~200 ms |

**Tiempo percibido hasta mapa listo: ~3–5 s** (limitado por inventario + tile EE en frío).

**Clic en mapa (inspector): 5–12 s** — principal cuello de botella UX.

**Cambio de año** (slider): debounce 350 ms + refetch tiles visibles. Con caché caliente ~2–4 ms por capa; sin caché ~2 s por capa.

**Filtro leyenda** (clase): refetch inmediato sin debounce → cada clic puede disparar ~2 s si la combinación bioma×año×clase no está en caché.

## Cuellos de botella (por impacto)

### 1. Earth Engine `getInfo()` — inspector (`identificar_punto`)

**Archivo:** `backend/services/comparacion_service.py` → `identificar_punto()`

Secuencia actual (hasta 4 round-trips síncronos a EE):

1. `hit.size().getInfo()`
2. `Feature.toDictionary().getInfo()`
3. `aggregate_array("tag").getInfo()` (por región)
4. `reduceRegion(...).getInfo()` (clase Col4/Col3)

**Alternativas:**

| Opción | Esfuerzo | Impacto |
|--------|----------|---------|
| Caché TTL por celda (~100 m) `(lat, lon, year, biomas)` | Bajo | Repetir clic ~instantáneo |
| Fusionar consultas en un solo `getInfo()` con `ee.Dictionary` | Medio | −50–70 % latencia |
| Precalcular región bajo punto con `SampleRegions` server-side | Medio | Menos round-trips |
| Mostrar spinner + resultado parcial (región primero, clase después) | Bajo | Mejor percepción UX |

### 2. Inventario sin caché (`inventario_assets`)

**Archivo:** `backend/services/comparacion_service.py` → `inventario_assets()`

Se ejecuta en cada **Ejecutar** aunque los assets no cambian entre sesiones.

**Alternativas:**

| Opción | Esfuerzo | Impacto |
|--------|----------|---------|
| Misma `TTLCache` que tiles, clave `inventario_{biomas}` | Bajo | −2.7 s en Ejecutar repetido |
| Incluir inventario en respuesta de `/tiles/col4` (una sola petición) | Medio | −1 RTT HTTP |
| Precalcular inventario en build/deploy (JSON estático) | Bajo | Casi instantáneo |

### 3. Tiles EE — `getMapId()` en frío

**Archivos:** `comparacion_service.py`, `landsat_service.py`

Ya cacheados 2 h / 256 entradas (`backend/core/cache.py`). Problema: muchas combinaciones bioma×año×filtro evictan entradas.

**Alternativas:**

| Opción | Esfuerzo | Impacto |
|--------|----------|---------|
| Cache check **antes** de construir grafo EE (como `obtener_tile_bordes`) | Bajo | Hits más baratos |
| Aumentar `maxsize` a 512–1024 | Trivial | Menos misses |
| Prefetch al Ejecutar: tile año actual + ±1 | Medio | Slider más fluido |
| **Earth Engine Assets exportados** (GeoTIFF/COG en GCS) + tiles locales | Alto | Sin `getMapId` en runtime |
| **TiTiler / Cloud Optimized GeoTIFF** para capas estáticas | Alto | Escalable, costo storage |

### 4. Google Sheets — lectura completa

**Archivo:** `backend/services/puntos_storage.py` → `list_registros()` / `_resolver_sheets()`

Cada `GET /puntos` = `get_all_values()` + reescritura JSON fallback. Resolver = N× `update_cell`.

**Alternativas:**

| Opción | Esfuerzo | Impacto |
|--------|----------|---------|
| Caché in-memory 30–60 s + invalidar en POST/resolve | Bajo | −200 ms–1.3 s en refresh |
| `batch_update` en lugar de `update_cell` por fila | Bajo | Resolver 10× más rápido |
| PostgreSQL / SQLite como source of truth, Sheets solo export | Medio | Lecturas locales <10 ms |
| Paginación `GET /puntos?since=timestamp` | Medio | Menos payload con muchos comentarios |

### 5. Frontend — re-renders y peticiones extra

**Archivos:** `App.jsx`, `useTeamLayers.js`, `MapView.jsx`

| Problema | Efecto |
|----------|--------|
| `MapView` recibe `year={tempYear}` (sin debounce) | Remonta Landsat en cada tick del slider (`key={landsat-${year}}`) |
| Filtro leyenda sin debounce | Refetch EE por cada clic |
| Col3 se pide si capa visible pero no siempre se renderiza | Trabajo EE desperdiciado |
| Handlers inline en `MapView` | Rompe `memo()`, re-renders de marcadores |

**Alternativas:**

| Opción | Esfuerzo | Impacto |
|--------|----------|---------|
| Pasar `year` debounced a `MapView` / quitar `key` en Landsat | Bajo | Slider fluido |
| Debounce 300 ms en `classIds` antes de refetch tiles | Bajo | Menos misses al filtrar |
| No fetch Col3 si no hay componente que lo muestre | Bajo | −1.6 s si capa activa sin uso |
| `useCallback` en handlers de `App` → `MapView` | Bajo | Menos re-render marcadores |

### 6. Bounds de región (panel estadísticas)

**Archivo:** `backend/services/region_bounds_service.py`

Primera visita a región: **12–25 s** (geometría + simplificación iterativa).

Ya cacheado tras primer hit. Alternativa: simplificar agresivamente en primer fetch o servir bbox rectangular primero y geometría detallada en background.

### 7. Arquitectura — handlers síncronos

FastAPI usa `def` sync → EE/Sheets bloquean el worker uvicorn.

**Alternativas:**

| Opción | Esfuerzo | Impacto |
|--------|----------|---------|
| `async def` + `run_in_executor` para EE/Sheets | Medio | Mejor concurrencia multi-usuario |
| Cola de trabajos (Redis/RQ) para `getMapId` pesados | Alto | UI no bloqueada |
| Segundo worker uvicorn (`--workers 2`) | Bajo | Paralelismo limitado (GIL + EE) |

## Prioridad recomendada (quick wins)

1. **Caché inventario** (TTL 2 h) — ~2.7 s menos en Ejecutar repetido  
2. **Caché identify** por celda — inspector usable  
3. **Debounce filtros leyenda** + **year debounced en MapView** — frontend  
4. **batch_update Sheets** en resolve  
5. **Cache check temprano** en `obtener_tile_col4/col3`  
6. **Prefetch** tile año±1 al Ejecutar  

## Lo que ya funciona bien

- Tiles EE cacheados: **2–4 ms** en caliente  
- Stats SQLite: **~50 ms**, payload razonable  
- Debounce año 350 ms en capas de tiles  
- Excel intérpretes: `@lru_cache`  
- Landsat prefetch estilos alternos en background  

## Monitoreo continuo

```powershell
python scripts/benchmark_perf.py --http
```

Registrar mediana/p95 tras cada cambio en EE o storage. Objetivo UX:

| Métrica | Objetivo |
|---------|----------|
| Ejecutar (frío) | < 4 s |
| Ejecutar (caliente) | < 500 ms |
| Inspector clic | < 1.5 s |
| GET /puntos | < 300 ms |
