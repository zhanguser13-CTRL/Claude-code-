"""
Performance Profiler for Claude Pet Companion

Provides:
- Function execution time measurement
- Memory usage monitoring
- Call counting and statistics
- Performance report generation
"""

import time
import functools
import logging
import threading
from typing import Dict, List, Callable, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import traceback

logger = logging.getLogger(__name__)


@dataclass
class FunctionStats:
    """Statistics for a function's performance."""
    name: str
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    last_time: float = 0.0

    # Error tracking
    error_count: int = 0
    last_error: Optional[str] = None

    # Memory tracking (when psutil is available)
    avg_memory: float = 0.0
    max_memory: float = 0.0

    def update(self, elapsed: float, error: Optional[Exception] = None):
        """Update statistics with a new execution."""
        self.call_count += 1
        self.total_time += elapsed
        self.min_time = min(self.min_time, elapsed)
        self.max_time = max(self.max_time, elapsed)
        self.avg_time = self.total_time / self.call_count
        self.last_time = elapsed

        if error:
            self.error_count += 1
            self.last_error = str(error)[:100]

    def get_summary(self) -> Dict:
        """Get summary as dictionary."""
        return {
            'name': self.name,
            'call_count': self.call_count,
            'total_time': self.total_time,
            'min_time': self.min_time if self.min_time != float('inf') else 0,
            'max_time': self.max_time,
            'avg_time': self.avg_time,
            'last_time': self.last_time,
            'error_count': self.error_count,
            'error_rate': self.error_count / self.call_count if self.call_count > 0 else 0,
        }


@dataclass
class CallStack:
    """A call stack entry for timing."""
    name: str
    start_time: float
    parent: Optional['CallStack'] = None
    children: List['CallStack'] = field(default_factory=list)


class Profiler:
    """Main profiler class for tracking performance."""

    _instance: Optional['Profiler'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'Profiler':
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize profiler."""
        if self._initialized:
            return

        self._initialized = True
        self.enabled: bool = True
        self.functions: Dict[str, FunctionStats] = {}
        self.call_stacks: Dict[int, CallStack] = {}  # thread_id -> stack
        self.stack_lock = threading.Lock()

        # Thresholds for warnings
        self.slow_threshold: float = 1.0  # seconds
        self.memory_threshold: float = 100 * 1024 * 1024  # 100MB

        # Try to import psutil for memory tracking
        self._psutil = None
        try:
            import psutil
            self._psutil = psutil
        except ImportError:
            pass

    def enable(self):
        """Enable profiling."""
        self.enabled = True

    def disable(self):
        """Disable profiling."""
        self.enabled = False

    def profile(self, name: Optional[str] = None) -> Callable:
        """
        Decorator to profile a function.

        Args:
            name: Optional name for the function (defaults to function name)
        """
        def decorator(func: Callable) -> Callable:
            func_name = name or f"{func.__module__}.{func.__qualname__}"

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                # Get or create stats
                if func_name not in self.functions:
                    self.functions[func_name] = FunctionStats(name=func_name)
                stats = self.functions[func_name]

                # Track call stack
                thread_id = threading.get_ident()
                with self.stack_lock:
                    stack = self.call_stacks.get(thread_id)
                    current = CallStack(func_name, time.time(), stack)
                    self.call_stacks[thread_id] = current

                # Measure execution
                start_memory = self._get_memory() if self._psutil else 0
                error = None
                result = None

                try:
                    start_time = time.perf_counter()
                    result = func(*args, **kwargs)
                    elapsed = time.perf_counter() - start_time

                    # Check for slow function
                    if elapsed > self.slow_threshold:
                        logger.warning(f"Slow function detected: {func_name} took {elapsed:.2f}s")

                except Exception as e:
                    error = e
                    elapsed = time.perf_counter() - start_time
                    raise
                finally:
                    # Update stats
                    stats.update(elapsed, error)

                    # Restore call stack
                    with self.stack_lock:
                        if stack is not None:
                            stack.children.append(current)
                        self.call_stacks[thread_id] = stack

                    # Track memory if available
                    if self._psutil:
                        end_memory = self._get_memory()
                        memory_used = end_memory - start_memory
                        if memory_used > 0:
                            stats.max_memory = max(stats.max_memory, memory_used)

                return result

            return wrapper
        return decorator

    def context(self, name: str) -> 'ProfileContext':
        """Create a profiling context manager."""
        return ProfileContext(self, name)

    def get_stats(self, name: str) -> Optional[FunctionStats]:
        """Get stats for a specific function."""
        return self.functions.get(name)

    def get_all_stats(self) -> List[FunctionStats]:
        """Get all function statistics."""
        return list(self.functions.values())

    def get_sorted_stats(self, by: str = 'total_time') -> List[FunctionStats]:
        """
        Get statistics sorted by a metric.

        Args:
            by: Sort metric - 'total_time', 'avg_time', 'call_count', 'max_time'
        """
        stats = self.get_all_stats()
        reverse = by in ['total_time', 'avg_time', 'call_count', 'max_time']
        return sorted(stats, key=lambda s: getattr(s, by, 0), reverse=reverse)

    def get_report(self, limit: int = 20) -> str:
        """Generate a performance report."""
        lines = [
            "=" * 70,
            "PERFORMANCE PROFILER REPORT",
            "=" * 70,
            "",
        ]

        # Top functions by total time
        sorted_by_total = self.get_sorted_stats('total_time')[:limit]
        if sorted_by_total:
            lines.extend([
                "Top Functions by Total Time:",
                "-" * 70,
                f"{'Function':<40} {'Calls':>8} {'Total':>10} {'Avg':>10} {'Max':>10}",
                "-" * 70,
            ])
            for stat in sorted_by_total:
                lines.append(
                    f"{stat.name:<40} {stat.call_count:>8} "
                    f"{stat.total_time:>10.3f} {stat.avg_time:>10.4f} {stat.max_time:>10.4f}"
                )
            lines.append("")

        # Functions with errors
        errors = [s for s in self.get_all_stats() if s.error_count > 0]
        if errors:
            lines.extend([
                "Functions with Errors:",
                "-" * 70,
                f"{'Function':<40} {'Errors':>8} {'Error Rate':>12}",
                "-" * 70,
            ])
            for stat in sorted(errors, key=lambda s: s.error_count, reverse=True)[:limit]:
                lines.append(
                    f"{stat.name:<40} {stat.error_count:>8} {stat.error_rate*100:>11.1f}%"
                )
            lines.append("")

        # Slowest functions (by max time)
        sorted_by_max = self.get_sorted_stats('max_time')[:limit]
        if sorted_by_max:
            lines.extend([
                "Slowest Function Calls (by max time):",
                "-" * 70,
                f"{'Function':<40} {'Max':>10} {'Avg':>10}",
                "-" * 70,
            ])
            for stat in sorted_by_max:
                lines.append(
                    f"{stat.name:<40} {stat.max_time:>10.4f} {stat.avg_time:>10.4f}"
                )
            lines.append("")

        # Summary
        total_calls = sum(s.call_count for s in self.get_all_stats())
        total_time = sum(s.total_time for s in self.get_all_stats())
        total_errors = sum(s.error_count for s in self.get_all_stats())

        lines.extend([
            "-" * 70,
            "Summary:",
            f"  Total functions tracked: {len(self.functions)}",
            f"  Total function calls: {total_calls}",
            f"  Total time tracked: {total_time:.2f}s",
            f"  Total errors: {total_errors}",
            "=" * 70,
        ])

        return "\n".join(lines)

    def print_report(self, limit: int = 20):
        """Print performance report to console."""
        print(self.get_report(limit))

    def reset(self):
        """Reset all statistics."""
        self.functions.clear()
        self.call_stacks.clear()

    def export_stats(self) -> Dict:
        """Export all statistics as a dictionary."""
        return {
            'functions': {
                name: stats.get_summary()
                for name, stats in self.functions.items()
            },
            'summary': {
                'total_functions': len(self.functions),
                'total_calls': sum(s.call_count for s in self.functions.values()),
                'total_time': sum(s.total_time for s in self.functions.values()),
                'total_errors': sum(s.error_count for s in self.functions.values()),
            }
        }

    def _get_memory(self) -> float:
        """Get current memory usage in bytes."""
        if self._psutil:
            process = self._psutil.Process()
            return process.memory_info().rss
        return 0


class ProfileContext:
    """Context manager for profiling code blocks."""

    def __init__(self, profiler: Profiler, name: str):
        self.profiler = profiler
        self.name = name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time

        # Update or create stats
        if self.name not in self.profiler.functions:
            self.profiler.functions[self.name] = FunctionStats(name=self.name)

        error = exc_val if exc_type is not None else None
        self.profiler.functions[self.name].update(elapsed, error)


# Global profiler instance
profiler = Profiler()


# Convenience decorators
def profile(func: Optional[Callable] = None, *, name: Optional[str] = None) -> Callable:
    """
    Decorator to profile a function.

    Usage:
        @profile
        def my_function():
            pass

        @profile(name="custom_name")
        def my_function():
            pass
    """
    if func is None:
        return lambda f: profiler.profile(name)(f)
    return profiler.profile()(func)


def profile_async(func: Optional[Callable] = None, *, name: Optional[str] = None) -> Callable:
    """Decorator to profile async functions."""
    import asyncio

    if func is None:
        return lambda f: profile_async(f, name=name)

    func_name = name or f"{func.__module__}.{func.__qualname__}"

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if not profiler.enabled:
            return await func(*args, **kwargs)

        if func_name not in profiler.functions:
            profiler.functions[func_name] = FunctionStats(name=func_name)
        stats = profiler.functions[func_name]

        start_time = time.perf_counter()
        error = None
        result = None

        try:
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start_time
        except Exception as e:
            error = e
            elapsed = time.perf_counter() - start_time
            raise
        finally:
            stats.update(elapsed, error)

        return result

    return wrapper


def measure(name: str) -> ProfileContext:
    """Create a profiling context manager."""
    return profiler.context(name)


if __name__ == "__main__":
    # Test profiler
    print("Testing Performance Profiler")

    @profile
    def fast_function():
        return sum(range(100))

    @profile
    def slow_function():
        total = 0
        for i in range(1000000):
            total += i
        return total

    @profile
    def error_function():
        raise ValueError("Test error")

    # Run functions
    for _ in range(10):
        fast_function()

    for _ in range(5):
        slow_function()

    for _ in range(3):
        try:
            error_function()
        except ValueError:
            pass

    # Test context manager
    with measure("test_block"):
        total = sum(range(10000))

    # Print report
    profiler.print_report()

    print("\nProfiler test passed!")
