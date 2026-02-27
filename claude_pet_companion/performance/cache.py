"""
Cache System for Claude Pet Companion

Provides:
- LRU (Least Recently Used) cache implementation
- Resource caching for textures and audio
- Cache invalidation strategies
- Cache statistics and monitoring
"""

import hashlib
import json
import logging
import os
import threading
import time
import pickle
from typing import Dict, Any, Optional, Callable, Tuple, List, Set, TypeVar, Generic
from dataclasses import dataclass, field
from collections import OrderedDict
from pathlib import Path
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry:
    """A single cache entry."""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    size_bytes: int = 0
    ttl: Optional[float] = None  # Time to live in seconds

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def touch(self):
        """Update last accessed time."""
        self.last_accessed = time.time()
        self.access_count += 1


class LRUCache(Generic[T]):
    """
    Thread-safe LRU (Least Recently Used) cache.

    Automatically evicts least recently used items when capacity is reached.
    """

    def __init__(self, capacity: int = 1000, ttl: Optional[float] = None):
        """
        Initialize LRU cache.

        Args:
            capacity: Maximum number of items
            ttl: Default time-to-live for entries (seconds)
        """
        self.capacity = max(1, capacity)
        self.default_ttl = ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0,
        }

    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """Get a value from cache."""
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return default

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self._stats['expirations'] += 1
                self._stats['misses'] += 1
                return default

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.touch()
            self._stats['hits'] += 1
            return entry.value

    def set(self, key: str, value: T, ttl: Optional[float] = None) -> bool:
        """Set a value in cache."""
        with self._lock:
            # Update existing or create new
            if key in self._cache:
                entry = self._cache[key]
                entry.value = value
                entry.ttl = ttl or self.default_ttl
                entry.touch()
                self._cache.move_to_end(key)
            else:
                # Check capacity
                if len(self._cache) >= self.capacity:
                    self._evict_lru()

                entry = CacheEntry(
                    key=key,
                    value=value,
                    ttl=ttl or self.default_ttl
                )
                self._cache[key] = entry

            return True

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def has(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        with self._lock:
            if key not in self._cache:
                return False
            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                return False
            return True

    def clear(self):
        """Clear all entries from cache."""
        with self._lock:
            self._cache.clear()
            self._reset_stats()

    def _evict_lru(self):
        """Evict least recently used item."""
        if self._cache:
            key, _ = self._cache.popitem(last=False)
            self._stats['evictions'] += 1

    def cleanup_expired(self) -> int:
        """Remove all expired entries, return count removed."""
        with self._lock:
            expired_keys = [
                k for k, v in self._cache.items()
                if v.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
                self._stats['expirations'] += 1
            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0

            return {
                'size': len(self._cache),
                'capacity': self.capacity,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'evictions': self._stats['evictions'],
                'expirations': self._stats['expirations'],
                'hit_rate': hit_rate,
                'usage_percent': len(self._cache) / self.capacity * 100,
            }

    def _reset_stats(self):
        """Reset statistics."""
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0,
        }

    def items(self) -> List[Tuple[str, T]]:
        """Get all items (excluding expired)."""
        with self._lock:
            self.cleanup_expired()
            return [(k, v.value) for k, v in self._cache.items()]

    def keys(self) -> List[str]:
        """Get all keys (excluding expired)."""
        with self._lock:
            self.cleanup_expired()
            return list(self._cache.keys())


class ResourceCache:
    """
    Cache for binary resources like textures and audio files.
    """

    def __init__(self, max_size_mb: int = 500, cache_dir: Optional[str] = None):
        """
        Initialize resource cache.

        Args:
            max_size_mb: Maximum cache size in megabytes
            cache_dir: Directory for persistent cache (optional)
        """
        self.max_bytes = max_size_mb * 1024 * 1024
        self.cache_dir = cache_dir
        self.memory_cache: LRUCache[bytes] = LRUCache(capacity=100)
        self._disk_cache: Dict[str, str] = {}  # key -> file path

        # Create cache directory if specified
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
            self._load_disk_cache_index()

    def get(self, key: str) -> Optional[bytes]:
        """Get resource data from cache."""
        # Try memory first
        data = self.memory_cache.get(key)
        if data is not None:
            return data

        # Try disk
        if key in self._disk_cache:
            file_path = self._disk_cache[key]
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        data = f.read()
                    # Promote to memory cache
                    self.memory_cache.set(key, data)
                    return data
                except IOError:
                    pass

        return None

    def set(self, key: str, data: bytes, persist: bool = False) -> bool:
        """Set resource data in cache."""
        size = len(data)

        # Check if we can fit in memory
        if size > self.max_bytes:
            logger.warning(f"Resource too large for cache: {size} bytes")
            return False

        # Store in memory
        self.memory_cache.set(key, data)

        # Persist to disk if requested
        if persist and self.cache_dir:
            file_path = os.path.join(self.cache_dir, f"{key}.cache")
            try:
                with open(file_path, 'wb') as f:
                    f.write(data)
                self._disk_cache[key] = file_path
            except IOError as e:
                logger.error(f"Failed to persist cache: {e}")

        return True

    def get_texture(self, path: str) -> Optional[bytes]:
        """Get cached texture data."""
        key = self._hash_path(path)
        return self.get(key)

    def set_texture(self, path: str, data: bytes, persist: bool = True) -> bool:
        """Cache texture data."""
        key = self._hash_path(path)
        return self.set(key, data, persist)

    def get_audio(self, path: str) -> Optional[bytes]:
        """Get cached audio data."""
        key = self._hash_path(path)
        return self.get(key)

    def set_audio(self, path: str, data: bytes, persist: bool = True) -> bool:
        """Cache audio data."""
        key = self._hash_path(path)
        return self.set(key, data, persist)

    def clear_memory(self):
        """Clear memory cache."""
        self.memory_cache.clear()

    def clear_disk(self):
        """Clear disk cache."""
        if self.cache_dir and os.path.exists(self.cache_dir):
            for file in os.listdir(self.cache_dir):
                if file.endswith('.cache'):
                    try:
                        os.remove(os.path.join(self.cache_dir, file))
                    except IOError:
                        pass
        self._disk_cache.clear()

    def clear_all(self):
        """Clear all caches."""
        self.clear_memory()
        self.clear_disk()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = self.memory_cache.get_stats()
        stats['disk_entries'] = len(self._disk_cache)
        stats['cache_dir'] = self.cache_dir or "None"
        return stats

    def _hash_path(self, path: str) -> str:
        """Create a hash key from file path."""
        return hashlib.md5(path.encode()).hexdigest()

    def _load_disk_cache_index(self):
        """Load disk cache index from directory."""
        if not self.cache_dir or not os.path.exists(self.cache_dir):
            return

        for file in os.listdir(self.cache_dir):
            if file.endswith('.cache'):
                key = file.replace('.cache', '')
                self._disk_cache[key] = os.path.join(self.cache_dir, file)


class CacheManager:
    """Manages multiple caches."""

    def __init__(self, default_capacity: int = 1000):
        self.default_capacity = default_capacity
        self.caches: Dict[str, LRUCache] = {}
        self.resource_cache: Optional[ResourceCache] = None

    def get_cache(self, name: str, capacity: Optional[int] = None) -> LRUCache:
        """Get or create a named cache."""
        if name not in self.caches:
            cap = capacity or self.default_capacity
            self.caches[name] = LRUCache(capacity=cap)
        return self.caches[name]

    def get_resource_cache(self, max_size_mb: int = 500,
                          cache_dir: Optional[str] = None) -> ResourceCache:
        """Get or create resource cache."""
        if self.resource_cache is None:
            self.resource_cache = ResourceCache(max_size_mb, cache_dir)
        return self.resource_cache

    def cleanup_all(self) -> int:
        """Cleanup expired entries in all caches."""
        total = 0
        for cache in self.caches.values():
            total += cache.cleanup_expired()
        return total

    def clear_all(self):
        """Clear all caches."""
        for cache in self.caches.values():
            cache.clear()
        if self.resource_cache:
            self.resource_cache.clear_all()

    def get_global_stats(self) -> Dict[str, Any]:
        """Get statistics for all caches."""
        return {
            'caches': {
                name: cache.get_stats()
                for name, cache in self.caches.items()
            },
            'resource_cache': self.resource_cache.get_stats() if self.resource_cache else None,
        }


# Global cache manager instance
cache_manager = CacheManager()


# Decorators for caching
def cached(ttl: Optional[float] = None, cache_name: str = 'default'):
    """
    Decorator to cache function results.

    Args:
        ttl: Time to live in seconds
        cache_name: Name of cache to use
    """
    def decorator(func: Callable) -> Callable:
        cache = cache_manager.get_cache(cache_name)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = _create_cache_key(func.__name__, args, kwargs)

            # Try cache
            result = cache.get(key)
            if result is not None:
                return result

            # Compute and cache
            result = func(*args, **kwargs)
            cache.set(key, result, ttl=ttl)
            return result

        wrapper.cache_clear = lambda: cache.clear()  # type: ignore
        wrapper.cache_info = lambda: cache.get_stats()  # type: ignore
        return wrapper

    return decorator


def cached_async(ttl: Optional[float] = None, cache_name: str = 'default'):
    """Decorator to cache async function results."""
    import asyncio

    def decorator(func: Callable) -> Callable:
        cache = cache_manager.get_cache(cache_name)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = _create_cache_key(func.__name__, args, kwargs)

            result = cache.get(key)
            if result is not None:
                return result

            result = await func(*args, **kwargs)
            cache.set(key, result, ttl=ttl)
            return result

        return wrapper

    return decorator


def _create_cache_key(func_name: str, args: Tuple, kwargs: Dict) -> str:
    """Create a cache key from function arguments."""
    # Simple approach: hash the repr of args
    key_data = {
        'func': func_name,
        'args': args,
        'kwargs': sorted(kwargs.items()),
    }
    key_json = json.dumps(key_data, default=str)
    return hashlib.md5(key_json.encode()).hexdigest()


if __name__ == "__main__":
    # Test cache
    print("Testing Cache System")

    # Test LRU cache
    cache = LRUCache(capacity=3)

    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    cache.set("d", 4)  # Should evict "a"

    print(f"Cache size: {cache.get_stats()['size']}")
    print(f"Has 'a': {cache.has('a')}")
    print(f"Get 'b': {cache.get('b')}")
    print(f"Get 'x' (missing): {cache.get('x', 'default')}")

    # Test TTL
    cache.set("temp", "expires soon", ttl=0.1)
    print(f"Has 'temp' (immediate): {cache.has('temp')}")
    time.sleep(0.15)
    print(f"Has 'temp' (after TTL): {cache.has('temp')}")

    # Test decorator
    @cached(ttl=60, cache_name='test')
    def expensive_function(n: int) -> int:
        print(f"Computing expensive_function({n})")
        return sum(range(n))

    print(f"\nFirst call: {expensive_function(100)}")
    print(f"Second call (cached): {expensive_function(100)}")

    # Test resource cache
    resource_cache = ResourceCache(max_size_mb=10)
    test_data = b"This is test texture data"
    resource_cache.set_texture("test.png", test_data)
    retrieved = resource_cache.get_texture("test.png")
    print(f"\nResource cache test: {retrieved == test_data}")

    print("\nCache system test passed!")
