"""Cache TTL para URLs de mosaicos EE."""

from cachetools import TTLCache

# Tile map IDs / URLs from Earth Engine (warmed in background for Landsat styles).
cache = TTLCache(maxsize=256, ttl=7200)
