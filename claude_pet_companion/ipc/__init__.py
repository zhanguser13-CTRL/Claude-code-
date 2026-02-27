#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPC Package for Claude Pet Companion

Provides inter-process communication between the pet daemon and clients.
"""
from typing import TYPE_CHECKING
from .protocol import Message, MessageType, create_message, parse_message

# Lazy imports to avoid circular dependency
if TYPE_CHECKING:
    from .server import IPCServer, DefaultMessageHandler
    from .client import IPCClient
else:
    def __getattr__(name):
        if name == "IPCServer":
            from .server import IPCServer
            return IPCServer
        if name == "DefaultMessageHandler":
            from .server import DefaultMessageHandler
            return DefaultMessageHandler
        if name == "IPCClient":
            from .client import IPCClient
            return IPCClient
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    'Message',
    'MessageType',
    'create_message',
    'parse_message',
    'IPCServer',
    'DefaultMessageHandler',
    'IPCClient',
]

# Default IPC port
DEFAULT_IPC_PORT = 15340
DEFAULT_IPC_HOST = '127.0.0.1'
