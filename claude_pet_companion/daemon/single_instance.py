#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single Instance Lock for Claude Pet Companion

Provides file-based locking to ensure only one pet instance runs at a time.
"""
import os
import fcntl
import errno
import logging
from pathlib import Path
from typing import Optional
import time

logger = logging.getLogger('SingleInstanceLock')


class SingleInstanceLock:
    """File-based lock for single instance enforcement"""

    def __init__(self, lock_file: Optional[Path] = None):
        """
        Initialize the single instance lock.

        Args:
            lock_file: Path to the lock file. Defaults to ~/.claude-pet-companion/daemon.lock
        """
        if lock_file is None:
            lock_dir = Path.home() / '.claude-pet-companion'
            lock_dir.mkdir(parents=True, exist_ok=True)
            lock_file = lock_dir / 'daemon.lock'

        self.lock_file = lock_file
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)

        self.lock_fd: Optional[int] = None
        self.is_locked = False
        self.pid = os.getpid()

    def acquire(self, blocking: bool = False, timeout: float = -1) -> bool:
        """
        Acquire the lock.

        Args:
            blocking: If True, block until lock is acquired
            timeout: Maximum time to wait for lock (seconds). -1 = wait forever

        Returns:
            True if lock was acquired, False otherwise
        """
        if self.is_locked:
            logger.warning("Lock already held")
            return True

        start_time = time.time()

        while True:
            try:
                # Open lock file (create if not exists)
                self.lock_fd = os.open(self.lock_file, os.O_WRONLY | os.O_CREAT)

                # Try to acquire exclusive lock
                if self._try_lock():
                    # Write our PID to the lock file
                    os.write(self.lock_fd, str(self.pid).encode('utf-8'))
                    self.is_locked = True
                    logger.info(f"Lock acquired: {self.lock_file} (PID: {self.pid})")
                    return True

            except OSError as e:
                if e.errno == errno.EWOULDBLOCK:
                    # Lock is held by another process
                    pass
                else:
                    logger.error(f"Error acquiring lock: {e}")
                    if self.lock_fd is not None:
                        os.close(self.lock_fd)
                        self.lock_fd = None
                    return False

            # Check if we should continue waiting
            if not blocking:
                logger.info("Lock is held by another process")
                return False

            if timeout >= 0:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    logger.info(f"Timeout waiting for lock ({timeout}s)")
                    return False

            # Wait before retrying
            time.sleep(0.1)

    def _try_lock(self) -> bool:
        """Try to acquire the file lock (platform-specific)"""
        if self.lock_fd is None:
            return False

        try:
            # Unix/Linux/macOS: use fcntl
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except AttributeError:
            # Windows: use msvcrt or simple file locking
            try:
                import msvcrt
                msvcrt.locking(self.lock_fd, msvcrt.LK_NBLCK, 1)
                return True
            except (ImportError, OSError):
                # Fallback: check if another instance is running
                return self._check_stale_lock()
        except OSError as e:
            if e.errno in (errno.EACCES, errno.EAGAIN):
                return False
            raise

    def _check_stale_lock(self) -> bool:
        """
        Check if the lock is stale (process no longer running).
        This is a fallback for systems without proper file locking.
        """
        try:
            # Read the PID from the lock file
            with open(self.lock_file, 'r') as f:
                pid_str = f.read().strip()

            if not pid_str:
                # Empty lock file, we can take it
                return True

            # Check if the process is still running
            try:
                pid = int(pid_str)
                # Try to send signal 0 to check if process exists
                os.kill(pid, 0)
                # Process exists, lock is valid
                return False
            except (OSError, ValueError):
                # Process doesn't exist, lock is stale
                logger.info(f"Found stale lock (PID {pid_str} not running)")
                return True

        except (FileNotFoundError, IOError):
            # No lock file exists
            return True

    def release(self) -> bool:
        """
        Release the lock.

        Returns:
            True if lock was released, False otherwise
        """
        if not self.is_locked:
            logger.warning("Lock not held")
            return False

        try:
            if self.lock_fd is not None:
                # Remove the lock file
                try:
                    os.unlink(self.lock_file)
                except FileNotFoundError:
                    pass

                # Release the file lock
                try:
                    fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                except (AttributeError, OSError):
                    pass

                # Close the file descriptor
                os.close(self.lock_fd)
                self.lock_fd = None

            self.is_locked = False
            logger.info("Lock released")
            return True

        except Exception as e:
            logger.error(f"Error releasing lock: {e}")
            return False

    def get_lock_holder_pid(self) -> Optional[int]:
        """
        Get the PID of the process holding the lock.

        Returns:
            PID if lock is held by another process, None otherwise
        """
        try:
            with open(self.lock_file, 'r') as f:
                pid_str = f.read().strip()

            if pid_str:
                return int(pid_str)

        except (FileNotFoundError, ValueError, IOError):
            pass

        return None

    def __enter__(self):
        """Context manager entry"""
        self.acquire(blocking=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()

    def __del__(self):
        """Destructor"""
        self.release()


# Convenience functions

def acquire_lock(lock_file: Optional[Path] = None,
                 blocking: bool = False,
                 timeout: float = -1) -> Optional[SingleInstanceLock]:
    """
    Acquire a single instance lock.

    Args:
        lock_file: Path to the lock file
        blocking: Whether to block until lock is acquired
        timeout: Maximum time to wait for lock

    Returns:
        SingleInstanceLock if acquired, None otherwise
    """
    lock = SingleInstanceLock(lock_file)
    if lock.acquire(blocking=blocking, timeout=timeout):
        return lock
    return None


def release_lock(lock: SingleInstanceLock) -> bool:
    """
    Release a single instance lock.

    Args:
        lock: The lock to release

    Returns:
        True if released, False otherwise
    """
    return lock.release()


def is_locked(lock_file: Optional[Path] = None) -> bool:
    """
    Check if a lock is currently held.

    Args:
        lock_file: Path to the lock file

    Returns:
        True if locked, False otherwise
    """
    lock = SingleInstanceLock(lock_file)
    holder_pid = lock.get_lock_holder_pid()

    if holder_pid is None:
        return False

    # Verify the process is actually running
    try:
        os.kill(holder_pid, 0)
        return True
    except OSError:
        return False
