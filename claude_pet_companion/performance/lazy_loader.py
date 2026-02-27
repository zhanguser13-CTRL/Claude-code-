"""
Lazy Loader for Claude Pet Companion

Provides:
- On-demand resource loading
- Async loading support with threading
- Priority queue for load ordering
- Loading progress callbacks
"""

import logging
import os
import threading
import time
from typing import Dict, Any, Optional, Callable, List, Tuple, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, Future
from collections import defaultdict
import queue

logger = logging.getLogger(__name__)

T = TypeVar('T')


class LoadPriority(IntEnum):
    """Loading priority levels (lower number = higher priority)."""
    CRITICAL = 0   # Must load immediately (UI, core assets)
    HIGH = 1       # Load soon (current scene)
    NORMAL = 2     # Standard priority (next scene)
    LOW = 3        # Load when idle (background content)
    PRELOAD = 4    # Speculative loading


class LoadStatus(Enum):
    """Status of a load operation."""
    PENDING = "pending"
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class LoadRequest:
    """A request to load a resource."""
    resource_id: str
    resource_type: str  # 'texture', 'audio', 'model', etc.
    source: str  # File path or URL
    priority: LoadPriority = LoadPriority.NORMAL
    callback: Optional[Callable[[str, Any], None]] = None
    error_callback: Optional[Callable[[str, Exception], None]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: LoadStatus = LoadStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[Exception] = None

    def __lt__(self, other: 'LoadRequest') -> bool:
        """Compare for priority queue (lower priority number = higher priority)."""
        return self.priority.value < other.priority.value


@dataclass
class LoadProgress:
    """Progress information for loading."""
    total: int = 0
    loaded: int = 0
    failed: int = 0
    current: Optional[str] = None

    @property
    def percentage(self) -> float:
        """Get completion percentage."""
        if self.total == 0:
            return 0.0
        return (self.loaded / self.total) * 100


class ResourceLoader:
    """Base class for resource loaders."""

    def load(self, source: str, metadata: Dict[str, Any]) -> Any:
        """Load a resource. Override in subclasses."""
        raise NotImplementedError

    def can_load(self, source: str) -> bool:
        """Check if this loader can handle the source."""
        return True


class FileResourceLoader(ResourceLoader):
    """Loader for file-based resources."""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()

    def load(self, source: str, metadata: Dict[str, Any]) -> bytes:
        """Load file as bytes."""
        file_path = self.base_path / source if not os.path.isabs(source) else Path(source)

        if not file_path.exists():
            raise FileNotFoundError(f"Resource not found: {file_path}")

        with open(file_path, 'rb') as f:
            return f.read()

    def can_load(self, source: str) -> bool:
        """Check if source is a valid file path."""
        file_path = self.base_path / source if not os.path.isabs(source) else Path(source)
        return file_path.exists() and file_path.is_file()


class ImageLoader(FileResourceLoader):
    """Loader for image resources with PIL/Pillow."""

    def load(self, source: str, metadata: Dict[str, Any]) -> Any:
        """Load image file."""
        try:
            from PIL import Image
            file_path = self.base_path / source if not os.path.isabs(source) else Path(source)
            return Image.open(file_path)
        except ImportError:
            # Fallback to bytes
            return super().load(source, metadata)


class AudioLoader(FileResourceLoader):
    """Loader for audio resources."""

    def load(self, source: str, metadata: Dict[str, Any]) -> bytes:
        """Load audio file as bytes."""
        return super().load(source, metadata)


class LazyLoader:
    """
    Main lazy loader class for on-demand resource loading.
    """

    def __init__(self, max_workers: int = 4, default_priority: LoadPriority = LoadPriority.NORMAL):
        """
        Initialize lazy loader.

        Args:
            max_workers: Maximum concurrent loading threads
            default_priority: Default priority for requests
        """
        self.max_workers = max_workers
        self.default_priority = default_priority

        # Resource registry
        self.resources: Dict[str, Any] = {}  # Loaded resources
        self.requests: Dict[str, LoadRequest] = {}  # All requests

        # Priority queue for pending loads
        self._queue: queue.PriorityQueue = queue.PriorityQueue()
        self._queue_lock = threading.Lock()

        # Thread pool for async loading
        self._executor: Optional[ThreadPoolExecutor] = None

        # Loaders by resource type
        self.loaders: Dict[str, ResourceLoader] = {
            'file': FileResourceLoader(),
            'image': ImageLoader(),
            'audio': AudioLoader(),
        }

        # Progress tracking
        self._progress = LoadProgress()
        self._progress_callbacks: List[Callable[[LoadProgress], None]] = []

        # State
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None

    def register_loader(self, resource_type: str, loader: ResourceLoader):
        """Register a custom resource loader."""
        self.loaders[resource_type] = loader

    def get_loader(self, resource_type: str) -> Optional[ResourceLoader]:
        """Get loader for resource type."""
        return self.loaders.get(resource_type)

    def start(self):
        """Start the lazy loader background processing."""
        if self._running:
            return

        self._running = True
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)

        # Start worker thread
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

        logger.info("Lazy loader started")

    def stop(self):
        """Stop the lazy loader."""
        if not self._running:
            return

        self._running = False

        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

        if self._worker_thread:
            self._worker_thread.join(timeout=5)
            self._worker_thread = None

        logger.info("Lazy loader stopped")

    def load_now(self, resource_id: str, source: str, resource_type: str = 'file',
                 priority: LoadPriority = LoadPriority.CRITICAL,
                 **metadata) -> Any:
        """
        Load a resource immediately (synchronous).

        Returns the loaded resource or raises exception.
        """
        # Check if already loaded
        if resource_id in self.resources:
            return self.resources[resource_id]

        # Get loader
        loader = self.get_loader(resource_type)
        if not loader:
            raise ValueError(f"No loader for type: {resource_type}")

        # Load resource
        try:
            result = loader.load(source, metadata)
            self.resources[resource_id] = result

            # Create request record
            request = LoadRequest(
                resource_id=resource_id,
                resource_type=resource_type,
                source=source,
                priority=priority,
                result=result,
                status=LoadStatus.LOADED,
                started_at=time.time(),
                completed_at=time.time(),
                metadata=metadata
            )
            self.requests[resource_id] = request

            return result

        except Exception as e:
            logger.error(f"Failed to load resource {resource_id}: {e}")
            raise

    def load_async(self, resource_id: str, source: str, resource_type: str = 'file',
                   priority: LoadPriority = LoadPriority.NORMAL,
                   callback: Optional[Callable[[str, Any], None]] = None,
                   error_callback: Optional[Callable[[str, Exception], None]] = None,
                   **metadata) -> str:
        """
        Load a resource asynchronously.

        Returns the request ID (same as resource_id).
        """
        # Check if already loaded
        if resource_id in self.resources:
            if callback:
                callback(resource_id, self.resources[resource_id])
            return resource_id

        # Create request
        request = LoadRequest(
            resource_id=resource_id,
            resource_type=resource_type,
            source=source,
            priority=priority,
            callback=callback,
            error_callback=error_callback,
            metadata=metadata
        )
        self.requests[resource_id] = request

        # Add to queue
        with self._queue_lock:
            self._queue.put(request)
            self._progress.total += 1

        # Ensure loader is running
        if not self._running:
            self.start()

        return resource_id

    def load_batch(self, requests: List[Tuple[str, str, str]],
                   priority: LoadPriority = LoadPriority.NORMAL,
                   callback: Optional[Callable[[str, Any], None]] = None) -> List[str]:
        """
        Load multiple resources as a batch.

        Args:
            requests: List of (resource_id, source, resource_type) tuples
            priority: Priority for all requests
            callback: Optional callback for each loaded resource

        Returns list of request IDs.
        """
        request_ids = []
        for resource_id, source, resource_type in requests:
            req_id = self.load_async(
                resource_id, source, resource_type,
                priority=priority, callback=callback
            )
            request_ids.append(req_id)
        return request_ids

    def preload(self, resources: Dict[str, Tuple[str, str]]):
        """
        Preload resources with low priority.

        Args:
            resources: Dict of {resource_id: (source, resource_type)}
        """
        for resource_id, (source, resource_type) in resources.items():
            self.load_async(
                resource_id, source, resource_type,
                priority=LoadPriority.PRELOAD
            )

    def get(self, resource_id: str, default: Optional[T] = None) -> Optional[T]:
        """Get a loaded resource."""
        return self.resources.get(resource_id, default)

    def is_loaded(self, resource_id: str) -> bool:
        """Check if resource is loaded."""
        return resource_id in self.resources

    def get_status(self, resource_id: str) -> Optional[LoadStatus]:
        """Get load status for a resource."""
        request = self.requests.get(resource_id)
        return request.status if request else None

    def cancel(self, resource_id: str) -> bool:
        """Cancel a pending load request."""
        request = self.requests.get(resource_id)
        if request and request.status == LoadStatus.PENDING:
            request.status = LoadStatus.CANCELLED
            return True
        return False

    def wait_for(self, resource_id: str, timeout: float = 10.0) -> bool:
        """Wait for a resource to be loaded."""
        start = time.time()
        while resource_id not in self.resources:
            if time.time() - start > timeout:
                return False
            request = self.requests.get(resource_id)
            if request and request.status in (LoadStatus.FAILED, LoadStatus.CANCELLED):
                return False
            time.sleep(0.01)
        return True

    def get_progress(self) -> LoadProgress:
        """Get current loading progress."""
        with self._queue_lock:
            # Update progress
            loaded = sum(1 for r in self.requests.values()
                        if r.status == LoadStatus.LOADED)
            failed = sum(1 for r in self.requests.values()
                        if r.status == LoadStatus.FAILED)

            return LoadProgress(
                total=self._progress.total,
                loaded=loaded,
                failed=failed,
                current=None  # Could track current loading item
            )

    def add_progress_callback(self, callback: Callable[[LoadProgress], None]):
        """Add a callback for progress updates."""
        self._progress_callbacks.append(callback)

    def clear_cache(self, resource_type: Optional[str] = None):
        """Clear cached resources."""
        if resource_type:
            to_remove = [
                rid for rid, req in self.requests.items()
                if req.resource_type == resource_type
            ]
            for rid in to_remove:
                self.resources.pop(rid, None)
                self.requests.pop(rid, None)
        else:
            self.resources.clear()
            self.requests.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get loader statistics."""
        total_requests = len(self.requests)
        loaded = sum(1 for r in self.requests.values() if r.status == LoadStatus.LOADED)
        failed = sum(1 for r in self.requests.values() if r.status == LoadStatus.FAILED)
        pending = sum(1 for r in self.requests.values() if r.status == LoadStatus.PENDING)
        loading = sum(1 for r in self.requests.values() if r.status == LoadStatus.LOADING)

        return {
            'total_requests': total_requests,
            'loaded': loaded,
            'failed': failed,
            'pending': pending,
            'loading': loading,
            'cache_size': len(self.resources),
            'queue_size': self._queue.qsize() if self._queue else 0,
        }

    def _worker_loop(self):
        """Background worker loop."""
        while self._running:
            try:
                # Get next request with timeout
                try:
                    request = self._queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                # Check if cancelled
                if request.status == LoadStatus.CANCELLED:
                    self._queue.task_done()
                    continue

                # Skip if already loaded
                if request.resource_id in self.resources:
                    self._queue.task_done()
                    continue

                # Submit to thread pool
                if self._executor:
                    self._executor.submit(self._load_resource, request)

                self._queue.task_done()

            except Exception as e:
                logger.error(f"Error in worker loop: {e}")

    def _load_resource(self, request: LoadRequest):
        """Load a single resource."""
        if request.status != LoadStatus.PENDING:
            return

        request.status = LoadStatus.LOADING
        request.started_at = time.time()

        try:
            # Get loader
            loader = self.get_loader(request.resource_type)
            if not loader:
                raise ValueError(f"No loader for type: {request.resource_type}")

            # Load resource
            result = loader.load(request.source, request.metadata)

            # Store result
            self.resources[request.resource_id] = result
            request.result = result
            request.status = LoadStatus.LOADED
            request.completed_at = time.time()

            # Call callback
            if request.callback:
                try:
                    request.callback(request.resource_id, result)
                except Exception as e:
                    logger.error(f"Error in load callback: {e}")

        except Exception as e:
            request.error = e
            request.status = LoadStatus.FAILED
            request.completed_at = time.time()

            logger.error(f"Failed to load {request.resource_id}: {e}")

            # Call error callback
            if request.error_callback:
                try:
                    request.error_callback(request.resource_id, e)
                except Exception as e2:
                    logger.error(f"Error in error callback: {e2}")

        # Notify progress callbacks
        for callback in self._progress_callbacks:
            try:
                callback(self.get_progress())
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")


# Global lazy loader instance
lazy_loader = LazyLoader()


if __name__ == "__main__":
    # Test lazy loader
    print("Testing Lazy Loader")

    # Create test files
    test_dir = Path("test_resources")
    test_dir.mkdir(exist_ok=True)

    test_file = test_dir / "test.txt"
    test_file.write_text("Hello, lazy loading!")

    # Test loader
    loader = LazyLoader(max_workers=2)
    loader.start()

    # Test immediate load
    print("\nTest 1: Immediate load")
    data = loader.load_now("test1", str(test_file), 'file')
    print(f"Loaded: {data.decode()}")

    # Test async load
    print("\nTest 2: Async load")
    results = []

    def on_load(resource_id, result):
        print(f"  Loaded: {resource_id}")
        results.append(result)

    loader.load_async("test2", str(test_file), 'file', callback=on_load)

    # Wait for completion
    time.sleep(0.5)
    print(f"Results: {len(results)}")

    # Test batch load
    print("\nTest 3: Batch load")
    requests = [
        ("batch1", str(test_file), 'file'),
        ("batch2", str(test_file), 'file'),
    ]

    loader.load_batch(requests, callback=on_load)
    time.sleep(0.5)
    print(f"Batch results: {len(results)}")

    # Test wait_for
    print("\nTest 4: Wait for load")
    loader.load_async("wait_test", str(test_file), 'file')
    if loader.wait_for("wait_test", timeout=2):
        print("  Resource loaded successfully")
        print(f"  Content: {loader.get('wait_test').decode()}")

    # Print stats
    print("\nStats:", loader.get_stats())

    # Cleanup
    loader.stop()
    test_file.unlink()
    try:
        test_dir.rmdir()
    except:
        pass

    print("\nLazy loader test passed!")
