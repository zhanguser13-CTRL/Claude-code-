#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPC Package for Claude Pet Companion

Provides inter-process communication between the pet daemon and clients.
"""
from .protocol import Message, MessageType, create_message, parse_message
from .server import IPCServer, DefaultMessageHandler
from .client import IPCClient

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
