"""
Performance Module for Claude Pet Companion

Provides performance optimization tools:
- Profiling and performance monitoring
- Caching system for resources and function results
- Lazy loading for on-demand resource loading
"""

from .profiler import (
    profiler,
    profile,
    profile_async,
    measure,
    Profiler,
    ProfileContext,
    FunctionStats,
)

from .cache import (
    cache_manager,
    cached,
    cached_async,
    LRUCache,
    ResourceCache,
    CacheManager,
    CacheEntry,
)

from .lazy_loader import (
    lazy_loader,
    LazyLoader,
    ResourceLoader,
    FileResourceLoader,
    ImageLoader,
    AudioLoader,
    LoadPriority,
    LoadStatus,
    LoadRequest,
    LoadProgress,
)

# Version info
__version__ = "2.3.4"

# Public API
__all__ = [
    # Profiler
    "profiler",
    "profile",
    "profile_async",
    "measure",
    "Profiler",
    "ProfileContext",
    "FunctionStats",
    # Cache
    "cache_manager",
    "cached",
    "cached_async",
    "LRUCache",
    "ResourceCache",
    "CacheManager",
    "CacheEntry",
    # Lazy Loader
    "lazy_loader",
    "LazyLoader",
    "ResourceLoader",
    "FileResourceLoader",
    "ImageLoader",
    "AudioLoader",
    "LoadPriority",
    "LoadStatus",
    "LoadRequest",
    "LoadProgress",
]

# Module-level convenience functions
def start_profiling():
    """Start performance profiling."""
    profiler.enable()
    if not lazy_loader._running:
        lazy_loader.start()


def stop_profiling():
    """Stop performance profiling."""
    profiler.disable()
    lazy_loader.stop()


def get_performance_report() -> str:
    """Get comprehensive performance report."""
    return profiler.get_report()


def clear_all_caches():
    """Clear all caches."""
    cache_manager.clear_all()
    if lazy_loader:
        lazy_loader.clear_cache()
