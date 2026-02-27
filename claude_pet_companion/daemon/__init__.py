#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daemon Package for Claude Pet Companion

Provides single-instance daemon functionality for the pet companion.
"""
from .single_instance import SingleInstanceLock, acquire_lock, release_lock, is_locked
from .daemon_manager import DaemonManager, get_daemon_manager

__all__ = [
    'SingleInstanceLock',
    'acquire_lock',
    'release_lock',
    'is_locked',
    'DaemonManager',
    'get_daemon_manager',
]
