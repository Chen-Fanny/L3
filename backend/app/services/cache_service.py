import time
from typing import Optional, Dict, Any

class CacheService:
    def __init__(self, default_ttl: int = 600):
        self.default_ttl = default_ttl
        self._data: Optional[Dict[str, Any]] = None
        self._cached_at: float = 0.0

    def get(self) -> Optional[Dict[str, Any]]:
        return self._data

    def set(self, data: Dict[str, Any]):
        self._data = data
        self._cached_at = time.time()

    def is_fresh(self) -> bool:
        if self._data is None:
            return False
        return (time.time() - self._cached_at) < self.default_ttl

    def status(self) -> str:
        if self._data is None:
            return "empty"
        if self.is_fresh():
            return "fresh"
        return "stale"

    @property
    def cached_at(self) -> float:
        return self._cached_at

cache_service = CacheService()
