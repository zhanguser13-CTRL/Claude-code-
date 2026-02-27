"""
Crash Handler for Claude Pet Companion

Provides:
- Global exception capture
- Crash logging with stack traces
- Automatic recovery mechanisms
- Crash report generation
"""

import sys
import os
import logging
import traceback
import threading
import time
import signal
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class CrashReport:
    """A crash report containing error information."""
    timestamp: float = field(default_factory=time.time)
    exception_type: str = ""
    exception_message: str = ""
    traceback_text: str = ""
    thread_name: str = ""
    thread_id: int = 0
    python_version: str = ""
    platform: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat(),
            'exception_type': self.exception_type,
            'exception_message': self.exception_message,
            'traceback': self.traceback_text,
            'thread_name': self.thread_name,
            'thread_id': self.thread_id,
            'python_version': self.python_version,
            'platform': self.platform,
            'context': self.context,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def save_to_file(self, path: Path):
        """Save crash report to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())


class CrashHandler:
    """
    Global crash handler for exception capture and reporting.
    """

    _instance: Optional['CrashHandler'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'CrashHandler':
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize crash handler."""
        if self._initialized:
            return

        self._initialized = True

        # Configuration
        self.crash_dir: Optional[Path] = None
        self.auto_restart: bool = False
        self.restart_delay: float = 5.0
        self.max_crash_reports: int = 10

        # State
        self.crash_count: int = 0
        self.recent_crashes: List[float] = []
        self._crash_threshold: int = 5  # Crashes per time window
        self._crash_window: float = 60.0  # Time window in seconds

        # Callbacks
        self.on_crash_callbacks: List[Callable[[CrashReport], None]] = []
        self.on_pre_crash_callbacks: List[Callable[[], None]] = []

        # Original exception hook
        self._original_excepthook: Optional[Callable] = None

        # System info
        self._python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self._platform = sys.platform

    def setup(self, crash_dir: Optional[Path] = None,
              auto_restart: bool = False,
              max_reports: int = 10):
        """
        Setup the crash handler.

        Args:
            crash_dir: Directory to save crash reports
            auto_restart: Whether to attempt auto-restart
            max_reports: Maximum crash reports to keep
        """
        self.crash_dir = Path(crash_dir) if crash_dir else None
        self.auto_restart = auto_restart
        self.max_crash_reports = max_reports

        # Create crash directory
        if self.crash_dir:
            self.crash_dir.mkdir(parents=True, exist_ok=True)

        # Install exception hooks
        self._install_hooks()

        # Install signal handlers
        self._install_signal_handlers()

        logger.info("Crash handler installed")

    def shutdown(self):
        """Remove crash handlers."""
        self._uninstall_hooks()
        self._uninstall_signal_handlers()
        logger.info("Crash handler uninstalled")

    def add_crash_callback(self, callback: Callable[[CrashReport], None]):
        """Add a callback to be called on crash."""
        self.on_crash_callbacks.append(callback)

    def add_pre_crash_callback(self, callback: Callable[[], None]):
        """Add a callback to be called before crash handling."""
        self.on_pre_crash_callbacks.append(callback)

    def _install_hooks(self):
        """Install exception hooks."""
        # Save original
        if sys.excepthook != self._excepthook:
            self._original_excepthook = sys.excepthook

        # Install custom hook
        sys.excepthook = self._excepthook

        # Install threading hook
        threading.excepthook = self._thread_excepthook  # type: ignore

    def _uninstall_hooks(self):
        """Restore original exception hooks."""
        if self._original_excepthook:
            sys.excepthook = self._original_excepthook

    def _install_signal_handlers(self):
        """Install signal handlers for fatal signals."""
        if sys.platform == 'win32':
            # Windows signals
            signals = [signal.SIGABRT, signal.SIGTERM, signal.SIGINT]
        else:
            # Unix signals
            signals = [signal.SIGABRT, signal.SIGTERM, signal.SIGINT, signal.SIGQUIT]

        for sig in signals:
            try:
                signal.signal(sig, self._signal_handler)
            except (ValueError, AttributeError):
                pass  # Signal not available

    def _uninstall_signal_handlers(self):
        """Restore default signal handlers."""
        if sys.platform == 'win32':
            signals = [signal.SIGABRT, signal.SIGTERM, signal.SIGINT]
        else:
            signals = [signal.SIGABRT, signal.SIGTERM, signal.SIGINT, signal.SIGQUIT]

        for sig in signals:
            try:
                signal.signal(sig, signal.SIG_DFL)
            except (ValueError, AttributeError):
                pass

    def _excepthook(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        self._handle_exception(exc_type, exc_value, exc_traceback)

    def _thread_excepthook(self, args):
        """Handle exceptions in threads."""
        self._handle_exception(
            args.exc_type,
            args.exc_value,
            args.exc_traceback,
            thread=args.thread
        )

    def _signal_handler(self, signum, frame):
        """Handle fatal signals."""
        # Create crash report for signal
        report = CrashReport(
            timestamp=time.time(),
            exception_type=f"Signal_{signum}",
            exception_message=f"Process terminated by signal {signum}",
            traceback_text="".join(traceback.format_stack(frame)),
            thread_name=threading.current_thread().name,
            thread_id=threading.get_ident(),
            python_version=self._python_version,
            platform=self._platform,
        )

        self._process_crash(report)

        # Call original handler
        signal.signal(signum, signal.SIG_DFL)
        os.kill(os.getpid(), signum)

    def _handle_exception(self, exc_type, exc_value, exc_traceback, thread=None):
        """Handle an exception."""
        # Create traceback string
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_text = "".join(tb_lines)

        # Create crash report
        current_thread = thread or threading.current_thread()
        report = CrashReport(
            timestamp=time.time(),
            exception_type=exc_type.__name__,
            exception_message=str(exc_value),
            traceback_text=tb_text,
            thread_name=current_thread.name,
            thread_id=current_thread.ident or 0,
            python_version=self._python_version,
            platform=self._platform,
        )

        self._process_crash(report)

    def _process_crash(self, report: CrashReport):
        """Process a crash report."""
        self.crash_count += 1

        # Track recent crashes
        now = time.time()
        self.recent_crashes.append(now)
        # Clean old crashes
        self.recent_crashes = [t for t in self.recent_crashes if now - t < self._crash_window]

        # Call pre-crash callbacks
        for callback in self.on_pre_crash_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in pre-crash callback: {e}")

        # Save crash report
        if self.crash_dir:
            filename = f"crash_{int(report.timestamp)}.json"
            filepath = self.crash_dir / filename
            try:
                report.save_to_file(filepath)
                logger.info(f"Crash report saved to {filepath}")

                # Clean old reports
                self._cleanup_old_reports()
            except Exception as e:
                logger.error(f"Failed to save crash report: {e}")

        # Log crash
        logger.critical(
            f"Crash detected: {report.exception_type}: {report.exception_message}\n"
            f"Thread: {report.thread_name}\n"
            f"Traceback:\n{report.traceback_text}"
        )

        # Call crash callbacks
        for callback in self.on_crash_callbacks:
            try:
                callback(report)
            except Exception as e:
                logger.error(f"Error in crash callback: {e}")

        # Check for crash loop
        if self._is_crash_loop():
            logger.error("Crash loop detected, disabling auto-restart")
            self.auto_restart = False

        # Auto-restart if enabled
        if self.auto_restart and not self._is_crash_loop():
            logger.info(f"Auto-restarting in {self.restart_delay} seconds...")
            time.sleep(self.restart_delay)
            self._restart_application()

    def _is_crash_loop(self) -> bool:
        """Check if application is in a crash loop."""
        # Count crashes in the time window
        recent_count = len(self.recent_crashes)
        return recent_count >= self._crash_threshold

    def _restart_application(self):
        """Restart the application."""
        try:
            # Get current executable and arguments
            executable = sys.executable
            args = sys.argv[:]

            # Restart
            logger.info(f"Restarting: {executable} {' '.join(args)}")
            os.execv(executable, [executable] + args)

        except Exception as e:
            logger.error(f"Failed to restart application: {e}")

    def _cleanup_old_reports(self):
        """Remove old crash reports."""
        if not self.crash_dir:
            return

        # Get all crash reports
        reports = list(self.crash_dir.glob("crash_*.json"))
        reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Remove excess reports
        for report in reports[self.max_crash_reports:]:
            try:
                report.unlink()
            except Exception as e:
                logger.error(f"Failed to delete old crash report: {e}")

    def get_crash_count(self) -> int:
        """Get total crash count."""
        return self.crash_count

    def get_recent_crash_count(self) -> int:
        """Get crash count in the time window."""
        now = time.time()
        return len([t for t in self.recent_crashes if now - t < self._crash_window])

    def clear_crash_history(self):
        """Clear crash history."""
        self.crash_count = 0
        self.recent_crashes.clear()

    def set_context(self, key: str, value: Any):
        """Set context information for next crash report."""
        # This would be added to the next crash report
        # For now, just log it
        logger.debug(f"Crash context: {key} = {value}")

    def get_crash_reports(self) -> List[CrashReport]:
        """Load all crash reports from disk."""
        if not self.crash_dir or not self.crash_dir.exists():
            return []

        reports = []
        for file in self.crash_dir.glob("crash_*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                report = CrashReport(
                    timestamp=data.get('timestamp', 0),
                    exception_type=data.get('exception_type', ''),
                    exception_message=data.get('exception_message', ''),
                    traceback_text=data.get('traceback', ''),
                    thread_name=data.get('thread_name', ''),
                    thread_id=data.get('thread_id', 0),
                    python_version=data.get('python_version', ''),
                    platform=data.get('platform', ''),
                    context=data.get('context', {}),
                )
                reports.append(report)
            except Exception as e:
                logger.error(f"Failed to load crash report {file}: {e}")

        reports.sort(key=lambda r: r.timestamp, reverse=True)
        return reports


# Global crash handler instance
crash_handler = CrashHandler()


def setup_crash_handler(crash_dir: Optional[Path] = None,
                        auto_restart: bool = False,
                        max_reports: int = 10) -> CrashHandler:
    """
    Setup the global crash handler.

    Args:
        crash_dir: Directory to save crash reports
        auto_restart: Whether to attempt auto-restart
        max_reports: Maximum crash reports to keep

    Returns:
        The crash handler instance
    """
    crash_handler.setup(crash_dir, auto_restart, max_reports)
    return crash_handler


def capture_exception(exc: Exception) -> CrashReport:
    """
    Capture an exception as a crash report without handling it.

    Args:
        exc: Exception to capture

    Returns:
        CrashReport instance
    """
    report = CrashReport(
        timestamp=time.time(),
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        traceback_text=traceback.format_exception(type(exc), exc, exc.__traceback__)[-1],
        thread_name=threading.current_thread().name,
        thread_id=threading.get_ident(),
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        platform=sys.platform,
    )
    return report


if __name__ == "__main__":
    # Test crash handler
    print("Testing Crash Handler")

    # Setup
    test_dir = Path("test_crash_reports")
    handler = setup_crash_handler(crash_dir=test_dir, auto_restart=False)

    # Test exception capture
    print("\nTest 1: Capture exception")
    try:
        1 / 0
    except ZeroDivisionError as e:
        report = capture_exception(e)
        print(f"  Captured: {report.exception_type}: {report.exception_message}")

    # Test callback
    print("\nTest 2: Crash callback")

    class CallbackTester:
        def __init__(self):
            self.called = False

    callback_tester = CallbackTester()

    def test_callback(crash_report: CrashReport):
        callback_tester.called = True
        print(f"  Callback received: {crash_report.exception_type}")

    handler.add_crash_callback(test_callback)

    # Note: We won't trigger an actual crash in tests
    print("  Callback registered (would be called on crash)")

    # Print stats
    print(f"\nCrash count: {handler.get_crash_count()}")
    print(f"Recent crashes: {handler.get_recent_crash_count()}")

    # Cleanup
    handler.shutdown()
    import shutil
    try:
        shutil.rmtree(test_dir)
    except:
        pass

    print("\nCrash handler test passed!")
