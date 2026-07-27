"""
Token counter cache for optimization.
Caches token counts to avoid repeated API calls for same text.

Phases:
- Phase 1: In-memory cache (current)
- Phase 2+: Persistent file-based cache + TTL management
"""

from typing import Optional, Dict, Tuple
import hashlib
from datetime import datetime, timedelta
import json


class TokenCounterCache:
    """In-memory token counter cache with LRU eviction"""

    def __init__(self, max_size: int = 10_000, ttl_hours: int = 24):
        self.cache: Dict[str, Tuple[int, datetime]] = {}
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
        self.hits = 0
        self.misses = 0

    def _get_key(self, model: str, text: str) -> str:
        """Generate cache key from model + text hash"""
        # Use first 100 chars + hash for key
        text_preview = text[:100]
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:8]
        return f"{model}:{text_preview}:{text_hash}"

    def get(self, model: str, text: str) -> Optional[int]:
        """Get cached token count (None if not found or expired)"""
        key = self._get_key(model, text)

        if key not in self.cache:
            self.misses += 1
            return None

        token_count, timestamp = self.cache[key]

        # Check TTL
        if datetime.now() - timestamp > self.ttl:
            del self.cache[key]
            self.misses += 1
            return None

        self.hits += 1
        return token_count

    def set(self, model: str, text: str, token_count: int):
        """Cache token count"""
        key = self._get_key(model, text)

        # Simple LRU: if at capacity, clear 10% of oldest entries
        if len(self.cache) >= self.max_size:
            # Sort by timestamp, remove oldest 10%
            sorted_keys = sorted(
                self.cache.keys(),
                key=lambda k: self.cache[k][1]
            )
            remove_count = max(1, len(sorted_keys) // 10)
            for k in sorted_keys[:remove_count]:
                del self.cache[k]

        self.cache[key] = (token_count, datetime.now())

    def clear(self):
        """Clear all cached entries"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_rate_percent": round(hit_rate, 2),
        }

    def save_to_file(self, filepath: str):
        """Save cache to JSON file (for persistence)"""
        # Convert timestamps to ISO format for JSON serialization
        serializable = {
            k: (v[0], v[1].isoformat())
            for k, v in self.cache.items()
        }

        with open(filepath, "w") as f:
            json.dump({
                "cache": serializable,
                "stats": self.get_stats(),
            }, f)

    def load_from_file(self, filepath: str):
        """Load cache from JSON file"""
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                cache_data = data.get("cache", {})

                # Restore with timestamps
                for k, (token_count, timestamp_str) in cache_data.items():
                    self.cache[k] = (token_count, datetime.fromisoformat(timestamp_str))
        except (FileNotFoundError, json.JSONDecodeError):
            pass  # File doesn't exist or is invalid


# Global cache instance
_global_cache: Optional[TokenCounterCache] = None


def get_global_cache() -> TokenCounterCache:
    """Get or create global token counter cache"""
    global _global_cache
    if _global_cache is None:
        _global_cache = TokenCounterCache()
    return _global_cache
