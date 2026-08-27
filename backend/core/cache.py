"""Cache TTL para URLs de mosaicos EE."""

from cachetools import TTLCache

cache = TTLCache(maxsize=64, ttl=3600)
