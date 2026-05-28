import time
from typing import Dict, Optional, Tuple

class InMemoryCache:
    def __init__(self):
        # Maps key -> (value, expiry_timestamp)
        self._store: Dict[str, Tuple[str, Optional[float]]] = {}

    def _is_expired(self, expiry: Optional[float]) -> bool:
        if expiry is None:
            return False
        return time.time() > expiry

    def _clean_expired(self):
        now = time.time()
        expired_keys = [k for k, (_, exp) in self._store.items() if exp is not None and now > exp]
        for k in expired_keys:
            self._store.pop(k, None)

    async def get(self, key: str) -> Optional[str]:
        self._clean_expired()
        item = self._store.get(key)
        if item is None:
            return None
        val, expiry = item
        if self._is_expired(expiry):
            self._store.pop(key, None)
            return None
        return val

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        self._clean_expired()
        expiry_ts = time.time() + ex if ex is not None else None
        self._store[key] = (str(value), expiry_ts)
        return True

    async def delete(self, *keys: str) -> int:
        count = 0
        for key in keys:
            if self._store.pop(key, None) is not None:
                count += 1
        return count

    async def incr(self, key: str) -> int:
        self._clean_expired()
        item = self._store.get(key)
        if item is None:
            # Initialize with 1 and no expiry by default; rate limiter should set expiry using expire()
            self._store[key] = ("1", None)
            return 1
        
        val, expiry = item
        try:
            new_val = int(val) + 1
        except ValueError:
            new_val = 1
        
        self._store[key] = (str(new_val), expiry)
        return new_val

    async def expire(self, key: str, seconds: int) -> bool:
        item = self._store.get(key)
        if item is None:
            return False
        val, _ = item
        self._store[key] = (val, time.time() + seconds)
        return True

    async def flushall(self) -> bool:
        self._store.clear()
        return True

# Global cache instance
cache = InMemoryCache()
