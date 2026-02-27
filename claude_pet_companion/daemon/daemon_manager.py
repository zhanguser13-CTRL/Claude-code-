#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daemon Manager for Claude Pet Companion

Manages the lifecycle of the pet daemon process.
"""
import os
import sys
import time
import signal
import logging
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from .single_instance import SingleInstanceLock, is_locked

logger = logging.getLogger('DaemonManager')


class DaemonStatus:
    """Daemon status constants"""
    RUNNING = "running"
    STOPPED = "stopped"
    CRASHED = "crashed"
    UNKNOWN = "unknown"


class DaemonManager:
    """Manages the pet daemon lifecycle"""

    def __init__(self, lock_file: Optional[Path] = None,
                 pid_file: Optional[Path] = None):
        """
        Initialize the daemon manager.

        Args:
            lock_file: Path to the lock file
            pid_file: Path to the PID file
        """
        self.data_dir = Path.home() / '.claude-pet-companion'
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if lock_file is None:
            lock_file = self.data_dir / 'daemon.lock'
        if pid_file is None:
            pid_file = self.data_dir / 'daemon.pid'

        self.lock_file = lock_file
        self.pid_file = pid_file

        # IPC settings
        self.ipc_port = 15340
        self.ipc_host = '127.0.0.1'

        # Callbacks
        self.on_shutdown: Optional[Callable] = None

    def get_status(self) -> str:
        """
        Get the current daemon status.

        Returns:
            DaemonStatus constant
        """
        # Check if PID file exists
        if not self.pid_file.exists():
            return DaemonStatus.STOPPED

        # Read PID
        try:
            with open(self.pid_file, 'r') as f:
                pid_str = f.read().strip()
                pid = int(pid_str)

            # Check if process is running
            os.kill(pid, 0)
            return DaemonStatus.RUNNING

        except (ValueError, FileNotFoundError):
            return DaemonStatus.STOPPED
        except OSError:
            # Process not running - might be crashed
            return DaemonStatus.CRASHED

    def get_daemon_info(self) -> Dict[str, Any]:
        """
        Get information about the running daemon.

        Returns:
            Dictionary with daemon information
        """
        status = self.get_status()
        info = {
            'status': status,
            'pid': None,
            'started_at': None,
            'ipc_port': self.ipc_port,
            'ipc_host': self.ipc_host,
        }

        if status == DaemonStatus.RUNNING:
            try:
                with open(self.pid_file, 'r') as f:
                    info['pid'] = int(f.read().strip())

                # Check for metadata file
                meta_file = self.data_dir / 'daemon_meta.json'
                if meta_file.exists():
                    with open(meta_file, 'r') as f:
                        meta = json.load(f)
                        info.update(meta)

            except (ValueError, FileNotFoundError, json.JSONDecodeError):
                pass

        return info

    def is_running(self) -> bool:
        """Check if daemon is running"""
        return self.get_status() == DaemonStatus.RUNNING

    def start(self, wait: bool = True, timeout: float = 10.0) -> bool:
        """
        Start the daemon.

        Args:
            wait: Whether to wait for daemon to start
            timeout: Maximum time to wait for startup

        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running():
            logger.warning("Daemon is already running")
            return False

        logger.info("Starting daemon...")

        # Determine the command to start the daemon
        # This is typically called from within the pet process itself
        # So we just need to set up the lock and PID file

        # Create the lock
        lock = SingleInstanceLock(self.lock_file)
        if not lock.acquire():
            logger.error("Failed to acquire lock")
            return False

        # Write PID file
        self._write_pid_file()

        # Write metadata
        self._write_metadata()

        logger.info("Daemon started successfully")
        return True

    def stop(self, wait: bool = True, timeout: float = 5.0) -> bool:
        """
        Stop the daemon.

        Args:
            wait: Whether to wait for daemon to stop
            timeout: Maximum time to wait for shutdown

        Returns:
            True if stopped successfully, False otherwise
        """
        status = self.get_status()

        if status == DaemonStatus.STOPPED:
            logger.info("Daemon is not running")
            return True

        pid = None
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
        except (ValueError, FileNotFoundError):
            pass

        if pid is None:
            logger.warning("Could not read PID file")
            return False

        logger.info(f"Stopping daemon (PID: {pid})...")

        # Try to gracefully shutdown first
        try:
            # Try connecting via IPC to send shutdown
            from ..ipc.client import IPCClient
            try:
                client = IPCClient(self.ipc_host, self.ipc_port, "daemon_manager")
                if client.connect(timeout=1.0):
                    # Send shutdown command
                    from ..ipc.protocol import create_message, MessageType
                    shutdown_msg = create_message(MessageType.SHUTDOWN)
                    client.send(shutdown_msg)
                    client.disconnect()
                    logger.info("Sent shutdown signal via IPC")
            except Exception:
                pass
        except Exception:
            pass

        # Wait for process to terminate
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            if not self.is_running():
                break
            time.sleep(0.1)

        # If still running, force kill
        if self.is_running():
            logger.warning("Daemon did not stop gracefully, forcing...")
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)
                if self.is_running():
                    os.kill(pid, signal.SIGKILL)
            except OSError as e:
                logger.error(f"Error killing process: {e}")

        # Clean up files
        self._cleanup()

        if not self.is_running():
            logger.info("Daemon stopped")
            return True
        else:
            logger.error("Failed to stop daemon")
            return False

    def restart(self, wait: bool = True, timeout: float = 10.0) -> bool:
        """
        Restart the daemon.

        Args:
            wait: Whether to wait for restart
            timeout: Maximum time to wait

        Returns:
            True if restarted successfully, False otherwise
        """
        logger.info("Restarting daemon...")
        if not self.stop(wait=wait, timeout=timeout):
            return False
        return self.start(wait=wait, timeout=timeout)

    def _write_pid_file(self):
        """Write the PID file"""
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))

    def _write_metadata(self):
        """Write daemon metadata"""
        meta = {
            'started_at': datetime.now().isoformat(),
            'pid': os.getpid(),
            'ipc_port': self.ipc_port,
            'ipc_host': self.ipc_host,
            'version': '1.0.0',
        }

        meta_file = self.data_dir / 'daemon_meta.json'
        with open(meta_file, 'w') as f:
            json.dump(meta, f, indent=2)

    def _cleanup(self):
        """Clean up daemon files"""
        # Remove lock file
        if self.lock_file.exists():
            try:
                self.lock_file.unlink()
            except OSError:
                pass

        # Remove PID file
        if self.pid_file.exists():
            try:
                self.pid_file.unlink()
            except OSError:
                pass

        # Remove metadata
        meta_file = self.data_dir / 'daemon_meta.json'
        if meta_file.exists():
            try:
                meta_file.unlink()
            except OSError:
                pass


# Singleton instance
_daemon_manager: Optional[DaemonManager] = None


def get_daemon_manager() -> DaemonManager:
    """Get or create the singleton daemon manager"""
    global _daemon_manager
    if _daemon_manager is None:
        _daemon_manager = DaemonManager()
    return _daemon_manager


def print_status():
    """Print the daemon status to console"""
    manager = get_daemon_manager()
    info = manager.get_daemon_info()

    status_emoji = {
        DaemonStatus.RUNNING: "🟢",
        DaemonStatus.STOPPED: "🔴",
        DaemonStatus.CRASHED: "🟡",
        DaemonStatus.UNKNOWN: "⚪",
    }

    emoji = status_emoji.get(info['status'], "⚪")
    print(f"\n{emoji} Claude Pet Daemon Status")
    print("=" * 40)
    print(f"Status:  {info['status'].upper()}")
    if info['pid']:
        print(f"PID:     {info['pid']}")
    if info['started_at']:
        print(f"Started: {info['started_at']}")
    print(f"IPC:     {info['ipc_host']}:{info['ipc_port']}")
    print("=" * 40)


def daemon_command(cmd: str):
    """
    Handle daemon CLI commands.

    Args:
        cmd: Command to run (start, stop, restart, status)

    Returns:
        Exit code
    """
    manager = get_daemon_manager()

    if cmd == 'status':
        print_status()
        return 0

    elif cmd == 'start':
        if manager.is_running():
            print("Daemon is already running")
            print_status()
            return 1
        if manager.start():
            print("Daemon started successfully")
            return 0
        else:
            print("Failed to start daemon")
            return 1

    elif cmd == 'stop':
        if not manager.is_running():
            print("Daemon is not running")
            return 1
        if manager.stop():
            print("Daemon stopped successfully")
            return 0
        else:
            print("Failed to stop daemon")
            return 1

    elif cmd == 'restart':
        if manager.restart():
            print("Daemon restarted successfully")
            return 0
        else:
            print("Failed to restart daemon")
            return 1

    else:
        print(f"Unknown command: {cmd}")
        print("Available commands: start, stop, restart, status")
        return 1
