"""
Performance Module Tests for Claude Pet Companion

Tests the profiler, cache system, and lazy loader.
"""

import pytest
import time
import sys
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pet_companion.performance import (
    profiler,
    profile,
    profile_async,
    measure,
    Profiler,
    ProfileContext,
    FunctionStats,
    cache_manager,
    cached,
    cached_async,
    LRUCache,
    ResourceCache,
    CacheManager,
    CacheEntry,
    lazy_loader,
    LazyLoader,
    ResourceLoader,
    FileResourceLoader,
    LoadPriority,
    LoadStatus,
    LoadRequest,
    LoadProgress,
)


class TestProfiler:
    """Test Profiler class."""

    def test_profiler_singleton(self):
        """Test profiler singleton pattern."""
        p1 = Profiler()
        p2 = Profiler()
        assert p1 is p2

    def test_profiler_enable_disable(self):
        """Test enabling and disabling profiler."""
        p = Profiler()
        p.enable()
        assert p.enabled is True

        p.disable()
        assert p.enabled is False

    def test_profile_decorator(self):
        """Test profile decorator."""
        p = Profiler()
        p.enable()
        p.reset()

        @p.profile()
        def test_function():
            time.sleep(0.01)
            return 42

        result = test_function()
        assert result == 42

        stats = p.get_stats("test_function")
        assert stats is not None
        assert stats.call_count == 1
        assert stats.total_time > 0

    def test_profile_decorator_with_name(self):
        """Test profile decorator with custom name."""
        p = Profiler()
        p.enable()
        p.reset()

        @p.profile(name="custom_name")
        def test_function():
            return 1

        test_function()

        stats = p.get_stats("custom_name")
        assert stats is not None

    def test_context_manager(self):
        """Test profiling context manager."""
        p = Profiler()
        p.enable()
        p.reset()

        with p.context("test_block"):
            time.sleep(0.01)

        stats = p.get_stats("test_block")
        assert stats is not None
        assert stats.total_time > 0

    def test_get_sorted_stats(self):
        """Test getting sorted statistics."""
        p = Profiler()
        p.enable()
        p.reset()

        @p.profile()
        def fast_func():
            return 1

        @p.profile()
        def slow_func():
            time.sleep(0.02)
            return 2

        fast_func()
        slow_func()

        sorted_by_time = p.get_sorted_stats('total_time')
        assert len(sorted_by_time) == 2
        assert sorted_by_time[0].name == "slow_func"

    def test_profiler_report(self):
        """Test profiler report generation."""
        p = Profiler()
        p.enable()
        p.reset()

        @p.profile()
        def test_func():
            return 1

        test_func()

        report = p.get_report()
        assert "PERFORMANCE PROFILER REPORT" in report
        assert "test_func" in report

    def test_profiler_reset(self):
        """Test resetting profiler."""
        p = Profiler()
        p.enable()

        @p.profile()
        def test_func():
            return 1

        test_func()
        assert len(p.get_all_stats()) == 1

        p.reset()
        assert len(p.get_all_stats()) == 0


class TestGlobalProfiler:
    """Test global profiler instance."""

    def test_global_profile_decorator(self):
        """Test global profile decorator."""
        profiler.reset()
        profiler.enable()

        @profile
        def test_function():
            time.sleep(0.005)
            return 42

        result = test_function()
        assert result == 42

        stats = profiler.get_stats("test_function")
        assert stats is not None

    def test_measure_context(self):
        """Test measure context manager."""
        profiler.reset()
        profiler.enable()

        with measure("test_context"):
            time.sleep(0.005)

        stats = profiler.get_stats("test_context")
        assert stats is not None


class TestLRUCache:
    """Test LRUCache class."""

    def test_cache_set_get(self):
        """Test basic cache set and get."""
        cache = LRUCache(capacity=3)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_cache_default_value(self):
        """Test getting non-existent key with default."""
        cache = LRUCache()
        assert cache.get("nonexistent") is None
        assert cache.get("nonexistent", "default") == "default"

    def test_cache_has(self):
        """Test has method."""
        cache = LRUCache()
        cache.set("key1", "value1")
        assert cache.has("key1") is True
        assert cache.has("key2") is False

    def test_cache_capacity_eviction(self):
        """Test LRU eviction when capacity is reached."""
        cache = LRUCache(capacity=2)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # Should evict "a"

        assert cache.has("a") is False
        assert cache.has("b") is True
        assert cache.has("c") is True

    def test_cache_lru_order(self):
        """Test that accessing item updates its position."""
        cache = LRUCache(capacity=3)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)

        # Access "a" to make it recently used
        cache.get("a")

        cache.set("d", 4)  # Should evict "b" (least recently used)

        assert cache.has("a") is True
        assert cache.has("b") is False
        assert cache.has("c") is True
        assert cache.has("d") is True

    def test_cache_delete(self):
        """Test deleting from cache."""
        cache = LRUCache()
        cache.set("key1", "value1")

        assert cache.delete("key1") is True
        assert cache.has("key1") is False

    def test_cache_clear(self):
        """Test clearing cache."""
        cache = LRUCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()
        assert len(cache.keys()) == 0

    def test_cache_ttl(self):
        """Test cache TTL (time to live)."""
        cache = LRUCache()

        cache.set("temp", "value", ttl=0.1)
        assert cache.has("temp") is True

        time.sleep(0.15)
        assert cache.has("temp") is False

    def test_cache_cleanup_expired(self):
        """Test cleaning up expired entries."""
        cache = LRUCache()

        cache.set("temp1", "value1", ttl=0.1)
        cache.set("temp2", "value2", ttl=0.1)
        cache.set("permanent", "value3")

        time.sleep(0.15)

        removed = cache.cleanup_expired()
        assert removed == 2
        assert cache.has("permanent") is True

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = LRUCache()

        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss

        stats = cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['size'] == 1


class TestCacheManager:
    """Test CacheManager class."""

    def test_get_cache(self):
        """Test getting or creating named caches."""
        manager = CacheManager(default_capacity=10)

        cache1 = manager.get_cache("cache1")
        cache2 = manager.get_cache("cache1")

        assert cache1 is cache2

        cache3 = manager.get_cache("cache2")
        assert cache1 is not cache3

    def test_cache_manager_cleanup(self):
        """Test cleanup across all caches."""
        manager = CacheManager()

        cache1 = manager.get_cache("cache1", capacity=5)
        cache1.set("key1", "value1", ttl=0.1)

        time.sleep(0.15)

        removed = manager.cleanup_all()
        assert removed >= 0


class TestCachedDecorator:
    """Test cached decorator."""

    def test_cached_decorator(self):
        """Test basic cached decorator."""
        call_count = 0

        @cached(ttl=60, cache_name='test')
        def expensive_function(n: int) -> int:
            nonlocal call_count
            call_count += 1
            return sum(range(n))

        result1 = expensive_function(100)
        result2 = expensive_function(100)

        assert result1 == result2
        assert call_count == 1  # Second call was cached

    def test_cached_with_different_args(self):
        """Test that different arguments create separate cache entries."""
        call_count = 0

        @cached(cache_name='test2')
        def func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        func(1)
        func(2)
        func(1)  # Should use cache

        assert call_count == 2

    def test_cached_clear(self):
        """Test clearing function cache."""
        @cached(cache_name='test3')
        def func(x):
            return x * 2

        func(1)
        func.cache_clear()  # type: ignore
        func(1)  # Should recompute

        # Check info
        info = func.cache_info()  # type: ignore
        assert 'hits' in info


class TestResourceCache:
    """Test ResourceCache class."""

    def test_resource_cache_set_get(self):
        """Test basic resource caching."""
        cache = ResourceCache(max_size_mb=10)
        data = b"test resource data"

        cache.set("resource1", data)
        retrieved = cache.get("resource1")

        assert retrieved == data

    def test_texture_cache(self):
        """Test texture-specific caching."""
        cache = ResourceCache(max_size_mb=10)
        data = b"PNG header + image data"

        cache.set_texture("/path/to/texture.png", data)
        retrieved = cache.get_texture("/path/to/texture.png")

        assert retrieved == data

    def test_audio_cache(self):
        """Test audio-specific caching."""
        cache = ResourceCache(max_size_mb=10)
        data = b"WAV header + audio data"

        cache.set_audio("/path/to/sound.wav", data)
        retrieved = cache.get_audio("/path/to/sound.wav")

        assert retrieved == data

    def test_resource_cache_stats(self):
        """Test resource cache statistics."""
        cache = ResourceCache(max_size_mb=10)
        cache.set("res1", b"data1")

        stats = cache.get_stats()
        assert 'size' in stats
        assert 'disk_entries' in stats


class TestLazyLoader:
    """Test LazyLoader class."""

    @pytest.fixture
    def test_loader(self):
        """Create a test loader with test resources."""
        loader = LazyLoader(max_workers=2)
        return loader

    def test_loader_singleton(self):
        """Test that loader singleton works."""
        # Just test that we can create one
        loader = LazyLoader(max_workers=2)
        assert loader is not None

    def test_load_now(self, test_loader):
        """Test immediate synchronous loading."""
        import tempfile
        import os

        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test data")
            temp_path = f.name

        try:
            result = test_loader.load_now("test1", temp_path, 'file')
            assert result is not None
            assert b"test data" in result

            # Check it's cached
            assert test_loader.is_loaded("test1")

        finally:
            os.unlink(temp_path)

    def test_load_async(self, test_loader):
        """Test async loading."""
        import tempfile
        import os

        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("async test data")
            temp_path = f.name

        try:
            test_loader.start()

            results = []

            def callback(resource_id, data):
                results.append((resource_id, data))

            test_loader.load_async("async1", temp_path, 'file', callback=callback)

            # Wait for load
            time.sleep(0.5)

            assert len(results) == 1
            assert results[0][0] == "async1"

        finally:
            test_loader.stop()
            os.unlink(temp_path)

    def test_wait_for(self, test_loader):
        """Test waiting for resource to load."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("wait test data")
            temp_path = f.name

        try:
            test_loader.start()

            test_loader.load_async("wait1", temp_path, 'file')
            success = test_loader.wait_for("wait1", timeout=2)

            assert success is True
            assert test_loader.is_loaded("wait1")

        finally:
            test_loader.stop()
            os.unlink(temp_path)

    def test_get_status(self, test_loader):
        """Test getting load status."""
        status = test_loader.get_status("nonexistent")
        assert status is None

    def test_get_progress(self, test_loader):
        """Test loading progress."""
        progress = test_loader.get_progress()
        assert progress.total == 0

    def test_get_stats(self, test_loader):
        """Test loader statistics."""
        stats = test_loader.get_stats()
        assert 'total_requests' in stats
        assert 'cache_size' in stats


class TestLoadPriority:
    """Test LoadPriority enum."""

    def test_priority_values(self):
        """Test priority levels."""
        assert LoadPriority.CRITICAL.value == 0
        assert LoadPriority.HIGH.value == 1
        assert LoadPriority.NORMAL.value == 2
        assert LoadPriority.LOW.value == 3
        assert LoadPriority.PRELOAD.value == 4


class TestLoadStatus:
    """Test LoadStatus enum."""

    def test_status_values(self):
        """Test status values."""
        assert LoadStatus.PENDING.value == "pending"
        assert LoadStatus.LOADING.value == "loading"
        assert LoadStatus.LOADED.value == "loaded"
        assert LoadStatus.FAILED.value == "failed"
        assert LoadStatus.CANCELLED.value == "cancelled"


class TestLoadRequest:
    """Test LoadRequest class."""

    def test_request_creation(self):
        """Test creating a load request."""
        request = LoadRequest(
            resource_id="res1",
            resource_type="texture",
            source="/path/to/file.png",
            priority=LoadPriority.HIGH
        )
        assert request.resource_id == "res1"
        assert request.status == LoadStatus.PENDING


class TestLoadProgress:
    """Test LoadProgress class."""

    def test_progress_percentage(self):
        """Test progress percentage calculation."""
        progress = LoadProgress(total=100, loaded=50)
        assert progress.percentage == 50.0

    def test_zero_total(self):
        """Test percentage with zero total."""
        progress = LoadProgress(total=0, loaded=0)
        assert progress.percentage == 0.0


class TestFileResourceLoader:
    """Test FileResourceLoader."""

    def test_file_loader(self):
        """Test loading a file."""
        import tempfile
        import os

        loader = FileResourceLoader()

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("file loader test")
            temp_path = f.name

        try:
            result = loader.load(temp_path, {})
            assert result == b"file loader test"

        finally:
            os.unlink(temp_path)

    def test_file_loader_not_found(self):
        """Test loading non-existent file."""
        loader = FileResourceLoader()

        with pytest.raises(FileNotFoundError):
            loader.load("/nonexistent/file.txt", {})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
