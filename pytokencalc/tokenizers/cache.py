"""
Token counter cache for optimization.
Caches token counts to avoid repeated API calls for same text.

Phases:
- Phase 1: In-memory cache (current)
- Phase 2+: Persistent file-based cache + TTL management
"""

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from .base import TokenCountResult


class TokenCounterCache:
    """In-memory token counter cache with LRU eviction"""

    def __init__(self, max_size: int = 10_000, ttl_hours: int = 24):
        self.cache: Dict[str, Tuple[TokenCountResult, datetime]] = {}
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
        self.hits = 0
        self.misses = 0

    def _get_key(self, model: str, text: str, provider: str = "") -> str:
        """Generate cache key from provider + model + text hash."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"{provider.lower()}:{model.lower()}:{text_hash}"

    def _lookup(self, model: str, text: str, provider: str = "") -> Optional[TokenCountResult]:
        key = self._get_key(model, text, provider)
        entry = self.cache.get(key)
        if entry is None:
            self.misses += 1
            return None

        result, timestamp = entry
        if datetime.now() - timestamp > self.ttl:
            del self.cache[key]
            self.misses += 1
            return None

        self.hits += 1
        return replace(
            result,
            cached=True,
            latency_ms=0.0,
            timestamp=datetime.utcnow(),
        )

    def get_result(
        self, model: str, text: str, provider: str = ""
    ) -> Optional[TokenCountResult]:
        """Get the cached result, preserving original provider/source metadata."""
        return self._lookup(model, text, provider)

    def get(self, model: str, text: str, provider: str = "") -> Optional[int]:
        """Get cached token count (None if not found or expired)."""
        result = self._lookup(model, text, provider)
        return result.input_tokens if result is not None else None

    def _store(self, model: str, text: str, result: TokenCountResult, provider: str = ""):
        key = self._get_key(model, text, provider)

        # Simple LRU: if at capacity, clear 10% of oldest entries
        if len(self.cache) >= self.max_size:
            sorted_keys = sorted(self.cache.keys(), key=lambda k: self.cache[k][1])
            remove_count = max(1, len(sorted_keys) // 10)
            for k in sorted_keys[:remove_count]:
                del self.cache[k]

        self.cache[key] = (replace(result), datetime.now())

    def set_result(
        self,
        model: str,
        text: str,
        result: TokenCountResult,
        provider: str = "",
    ):
        """Cache a full token-count result."""
        self._store(model, text, result, provider or result.provider)

    def set(self, model: str, text: str, token_count: int, provider: str = ""):
        """Cache a token count (compatibility helper)."""
        self._store(
            model,
            text,
            TokenCountResult(input_tokens=token_count, model=model, provider=provider),
            provider,
        )

    def clear(self):
        """Clear all cached entries"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
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
            k: (v[0].input_tokens, v[1].isoformat())
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
                    self.cache[k] = (
                        TokenCountResult(input_tokens=token_count),
                        datetime.fromisoformat(timestamp_str),
                    )
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
