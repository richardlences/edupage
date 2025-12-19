"""
Simple in-memory cache with TTL for Edupage lunch data.
Reduces redundant calls to the external Edupage API.
"""
import time
from typing import Any, Optional

class LunchCache:
    def __init__(self, ttl_seconds: int = 60):
        self._cache: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl_seconds
    
    def _make_key(self, user_id: int, date_str: str) -> str:
        return f"{user_id}:{date_str}"
    
    def get(self, user_id: int, date_str: str) -> Optional[Any]:
        """Get cached data if it exists and is not expired."""
        key = self._make_key(user_id, date_str)
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return data
            # Expired, remove it
            del self._cache[key]
        return None
    
    def set(self, user_id: int, date_str: str, data: Any) -> None:
        """Store data in cache with current timestamp."""
        key = self._make_key(user_id, date_str)
        self._cache[key] = (data, time.time())
    
    def invalidate(self, user_id: int, date_str: str) -> None:
        """Remove specific entry from cache."""
        key = self._make_key(user_id, date_str)
        self._cache.pop(key, None)
    
    def clear_user(self, user_id: int) -> None:
        """Clear all cache entries for a specific user."""
        keys_to_remove = [k for k in self._cache if k.startswith(f"{user_id}:")]
        for k in keys_to_remove:
            del self._cache[k]

# Global cache instance
lunch_cache = LunchCache(ttl_seconds=60)
