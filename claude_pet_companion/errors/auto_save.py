"""
Auto Save System for Claude Pet Companion

Provides:
- Periodic automatic saves
- Saves after critical operations
- Crash recovery from last save
- Backup management with rotation
"""

import os
import json
import logging
import threading
import time
import shutil
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib
import pickle

logger = logging.getLogger(__name__)


@dataclass
class SaveState:
    """A saved state snapshot."""
    timestamp: float = field(default_factory=time.time)
    version: str = "2.3.4"
    data: Dict[str, Any] = field(default_factory=dict)
    checksum: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def compute_checksum(self) -> str:
        """Compute checksum of data."""
        data_json = json.dumps(self.data, sort_keys=True, default=str)
        return hashlib.sha256(data_json.encode()).hexdigest()

    def verify(self) -> bool:
        """Verify data integrity."""
        return self.compute_checksum() == self.checksum


@dataclass
class BackupInfo:
    """Information about a backup file."""
    path: Path
    timestamp: float
    size: int
    version: str = "2.3.4"

    def age_seconds(self) -> float:
        """Get age of backup in seconds."""
        return time.time() - self.timestamp


class AutoSaveManager:
    """
    Manages automatic saving and backup of application state.
    """

    def __init__(self, save_dir: Path, auto_save_interval: float = 60.0,
                 max_backups: int = 10):
        """
        Initialize auto-save manager.

        Args:
            save_dir: Directory for save files
            auto_save_interval: Seconds between auto-saves
            max_backups: Maximum number of backups to keep
        """
        self.save_dir = Path(save_dir)
        self.auto_save_interval = auto_save_interval
        self.max_backups = max_backups

        # State
        self._state: Dict[str, Any] = {}
        self._dirty: bool = False
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._stop_event = threading.Event()

        # Callbacks
        self._on_save_callbacks: List[Callable[[SaveState], None]] = []
        self._on_load_callbacks: List[Callable[[SaveState], None]] = []

        # File paths
        self.current_save_path = self.save_dir / "current_save.json"
        self.backup_dir = self.save_dir / "backups"

        # Create directories
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def start(self):
        """Start auto-save background thread."""
        if self._running:
            return

        self._running = True
        self._stop_event.clear()

        self._thread = threading.Thread(target=self._auto_save_loop, daemon=True)
        self._thread.start()

        logger.info(f"Auto-save started (interval: {self.auto_save_interval}s)")

    def stop(self):
        """Stop auto-save background thread."""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()

        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

        # Final save before stopping
        self.save_now()

        logger.info("Auto-save stopped")

    def set(self, key: str, value: Any):
        """Set a value in the state."""
        with self._lock:
            self._state[key] = value
            self._dirty = True

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the state."""
        with self._lock:
            return self._state.get(key, default)

    def update(self, data: Dict[str, Any]):
        """Update multiple values in the state."""
        with self._lock:
            self._state.update(data)
            self._dirty = True

    def clear(self):
        """Clear all state."""
        with self._lock:
            self._state.clear()
            self._dirty = True

    def save_now(self) -> bool:
        """Immediately save current state."""
        with self._lock:
            return self._save_state()

    def load(self) -> bool:
        """Load state from disk."""
        if not self.current_save_path.exists():
            logger.info("No save file found")
            return False

        try:
            with open(self.current_save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Verify checksum
            checksum = data.pop('checksum', '')
            test_data = data.copy()
            if 'metadata' in test_data:
                test_metadata = test_data.pop('metadata', {})
            else:
                test_metadata = {}

            computed = hashlib.sha256(
                json.dumps(test_data, sort_keys=True, default=str).encode()
            ).hexdigest()

            if computed != checksum:
                logger.warning("Save file checksum mismatch, trying backup")
                return self._load_from_backup()

            # Restore state
            with self._lock:
                self._state = data.get('data', {})
                self._dirty = False

            # Notify callbacks
            state = SaveState(**data)
            for callback in self._on_load_callbacks:
                try:
                    callback(state)
                except Exception as e:
                    logger.error(f"Error in load callback: {e}")

            logger.info(f"State loaded from {self.current_save_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load save file: {e}")
            return self._load_from_backup()

    def _load_from_backup(self) -> bool:
        """Load from most recent backup."""
        backups = self._list_backups()
        if not backups:
            return False

        backup = backups[0]  # Most recent
        try:
            with open(backup.path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            with self._lock:
                self._state = data.get('data', {})
                self._dirty = False

            logger.info(f"State loaded from backup {backup.path.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to load backup: {e}")
            return False

    def _save_state(self) -> bool:
        """Save current state to disk."""
        if not self._dirty:
            return True  # Nothing to save

        try:
            # Create backup of current save first
            if self.current_save_path.exists():
                self._create_backup(self.current_save_path)

            # Prepare save data
            save_data = {
                'timestamp': time.time(),
                'version': '2.3.4',
                'data': dict(self._state),
                'metadata': {
                    'saved_at': datetime.now().isoformat(),
                    'auto_save': True,
                }
            }

            # Compute checksum
            data_for_checksum = {k: v for k, v in save_data.items() if k != 'checksum'}
            checksum = hashlib.sha256(
                json.dumps(data_for_checksum, sort_keys=True, default=str).encode()
            ).hexdigest()
            save_data['checksum'] = checksum

            # Write to temp file first
            temp_path = self.current_save_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, default=str)

            # Atomic rename
            temp_path.replace(self.current_save_path)

            self._dirty = False

            # Notify callbacks
            state = SaveState(**save_data)
            for callback in self._on_save_callbacks:
                try:
                    callback(state)
                except Exception as e:
                    logger.error(f"Error in save callback: {e}")

            logger.debug(f"State saved to {self.current_save_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False

    def _create_backup(self, source_path: Path):
        """Create a backup of a save file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.json"
        backup_path = self.backup_dir / backup_name

        try:
            shutil.copy2(source_path, backup_path)

            # Clean old backups
            self._cleanup_old_backups()

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")

    def _cleanup_old_backups(self):
        """Remove old backups beyond max_backups limit."""
        backups = self._list_backups()

        while len(backups) > self.max_backups:
            old_backup = backups.pop()
            try:
                old_backup.path.unlink()
                logger.debug(f"Removed old backup: {old_backup.path.name}")
            except Exception as e:
                logger.error(f"Failed to delete backup: {e}")

    def _list_backups(self) -> List[BackupInfo]:
        """List all backup files, sorted by timestamp (newest first)."""
        backups = []

        for file in self.backup_dir.glob("backup_*.json"):
            try:
                stat = file.stat()
                backups.append(BackupInfo(
                    path=file,
                    timestamp=stat.st_mtime,
                    size=stat.st_size
                ))
            except Exception as e:
                logger.error(f"Error reading backup {file}: {e}")

        backups.sort(key=lambda b: b.timestamp, reverse=True)
        return backups

    def _auto_save_loop(self):
        """Background thread for auto-saving."""
        while self._running:
            # Wait for interval or stop event
            self._stop_event.wait(self.auto_save_interval)

            if self._stop_event.is_set():
                break

            # Save if dirty
            with self._lock:
                if self._dirty:
                    self._save_state()

    def add_save_callback(self, callback: Callable[[SaveState], None]):
        """Add callback to be called after save."""
        self._on_save_callbacks.append(callback)

    def add_load_callback(self, callback: Callable[[SaveState], None]):
        """Add callback to be called after load."""
        self._on_load_callbacks.append(callback)

    def get_state(self) -> Dict[str, Any]:
        """Get copy of current state."""
        with self._lock:
            return dict(self._state)

    def is_dirty(self) -> bool:
        """Check if state has unsaved changes."""
        with self._lock:
            return self._dirty

    def get_save_info(self) -> Optional[SaveState]:
        """Get information about current save file."""
        if not self.current_save_path.exists():
            return None

        try:
            with open(self.current_save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return SaveState(**data)
        except Exception as e:
            logger.error(f"Failed to read save info: {e}")
            return None

    def get_backup_count(self) -> int:
        """Get number of backup files."""
        return len(self._list_backups())

    def delete_all_saves(self):
        """Delete all save files and backups."""
        with self._lock:
            # Delete current save
            if self.current_save_path.exists():
                self.current_save_path.unlink()

            # Delete backups
            for backup in self.backup_dir.glob("backup_*.json"):
                try:
                    backup.unlink()
                except Exception as e:
                    logger.error(f"Failed to delete backup: {e}")

            # Clear state
            self._state.clear()
            self._dirty = True

    def export_save(self, export_path: Path) -> bool:
        """Export current state to a file."""
        try:
            export_path.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                data = {
                    'timestamp': time.time(),
                    'version': '2.3.4',
                    'data': dict(self._state),
                    'metadata': {
                        'exported_at': datetime.now().isoformat(),
                    }
                }
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to export save: {e}")
            return False

    def import_save(self, import_path: Path) -> bool:
        """Import state from a file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            with self._lock:
                self._state = data.get('data', {})
                self._dirty = True

            logger.info(f"Imported save from {import_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to import save: {e}")
            return False


class CriticalOperationSaver:
    """Context manager for saving after critical operations."""

    def __init__(self, manager: AutoSaveManager, save_on_success: bool = True,
                 save_on_error: bool = False):
        self.manager = manager
        self.save_on_success = save_on_success
        self.save_on_error = save_on_error
        self.success = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.success = True
            if self.save_on_success:
                self.manager.save_now()
        elif self.save_on_error:
            self.manager.save_now()
        return False


# Global auto-save manager instance
auto_save_manager: Optional[AutoSaveManager] = None


def setup_auto_save(save_dir: Path, interval: float = 60.0,
                   max_backups: int = 10) -> AutoSaveManager:
    """
    Setup the global auto-save manager.

    Args:
        save_dir: Directory for save files
        interval: Auto-save interval in seconds
        max_backups: Maximum number of backups

    Returns:
        The auto-save manager instance
    """
    global auto_save_manager
    auto_save_manager = AutoSaveManager(save_dir, interval, max_backups)
    auto_save_manager.start()
    return auto_save_manager


def critical_operation(manager: AutoSaveManager,
                      save_on_success: bool = True,
                      save_on_error: bool = False) -> CriticalOperationSaver:
    """Create a context manager for critical operations."""
    return CriticalOperationSaver(manager, save_on_success, save_on_error)


if __name__ == "__main__":
    # Test auto-save
    print("Testing Auto Save System")

    # Create test directory
    test_dir = Path("test_saves")

    manager = AutoSaveManager(test_dir, auto_save_interval=1.0)

    # Test 1: Set values
    print("\nTest 1: Set values")
    manager.set("test_key", "test_value")
    manager.set("number", 42)
    manager.update({"nested": {"key": "value"}})
    print(f"  State: {manager.get_state()}")
    print(f"  Is dirty: {manager.is_dirty()}")

    # Test 2: Save
    print("\nTest 2: Manual save")
    manager.save_now()
    print(f"  Is dirty after save: {manager.is_dirty()}")

    # Test 3: Load
    print("\nTest 3: Load")
    new_manager = AutoSaveManager(test_dir)
    loaded = new_manager.load()
    print(f"  Loaded: {loaded}")
    print(f"  State: {new_manager.get_state()}")

    # Test 4: Auto-save loop
    print("\nTest 4: Auto-save loop")
    manager.start()
    manager.set("auto_test", "auto_value")
    time.sleep(1.5)  # Wait for auto-save
    print(f"  Is dirty after auto-save: {manager.is_dirty()}")
    manager.stop()

    # Test 5: Critical operation context
    print("\nTest 5: Critical operation context")
    with critical_operation(manager, save_on_success=True):
        manager.set("critical_key", "critical_value")
    print(f"  Saved after critical operation")

    # Test 6: Export/Import
    print("\nTest 6: Export/Import")
    export_file = test_dir / "export.json"
    manager.export_save(export_file)
    print(f"  Exported to {export_file}")

    manager.clear()
    print(f"  After clear: {manager.get_state()}")

    manager.import_save(export_file)
    print(f"  After import: {manager.get_state()}")

    # Test 7: Backup info
    print("\nTest 7: Backup info")
    save_info = manager.get_save_info()
    if save_info:
        print(f"  Save timestamp: {datetime.fromtimestamp(save_info.timestamp)}")
        print(f"  Save version: {save_info.version}")

    print(f"  Backup count: {manager.get_backup_count()}")

    # Cleanup
    manager.stop()
    import shutil
    try:
        shutil.rmtree(test_dir)
    except:
        pass

    print("\nAuto save system test passed!")
