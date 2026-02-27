#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPC Protocol for Claude Pet Companion

Defines the message protocol used for communication between
the pet daemon and connected clients.
"""
import json
import uuid
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from enum import Enum


class MessageType(Enum):
    """Message types for IPC communication"""

    # Connection management
    HELLO = "hello"              # Client handshake
    GOODBYE = "goodbye"          # Client disconnect

    # State queries
    STATUS = "status"            # Query pet status
    STATE_UPDATE = "state_update"  # Push state update to clients

    # Actions
    ACTION = "action"            # Perform an action (feed, play, etc.)
    ACTION_RESPONSE = "action_response"  # Response to an action

    # Conversation/memory
    CONVERSATION_START = "conversation_start"   # Start a new conversation
    CONVERSATION_MESSAGE = "conversation_message"  # Add a message
    CONVERSATION_END = "conversation_end"       # End a conversation
    CONVERSATION_LIST = "conversation_list"     # List conversations
    CONVERSATION_GET = "conversation_get"       # Get a specific conversation
    CONVERSATION_SEARCH = "conversation_search" # Search conversations

    # Context restoration
    RESTORE_CONTEXT = "restore_context"  # Restore conversation context
    CONTINUE_CONVERSATION = "continue_conversation"  # Continue a conversation

    # Events
    EVENT = "event"              # Broadcast event to all clients
    SHUTDOWN = "shutdown"        # Server shutdown notification

    # Error handling
    ERROR = "error"              # Error message
    PING = "ping"                # Ping/pong for keep-alive
    PONG = "pong"                # Pong response


@dataclass
class Message:
    """IPC Message"""
    type: str                    # Message type (MessageType value)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "client"       # Message origin: "client", "server", "daemon"

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        return cls(
            type=data.get('type', ''),
            id=data.get('id', str(uuid.uuid4())),
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            payload=data.get('payload', {}),
            source=data.get('source', 'client')
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create message from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def reply(self, payload: Dict[str, Any], msg_type: Optional[str] = None) -> 'Message':
        """Create a reply message"""
        reply_type = msg_type or f"{self.type}_response"
        return Message(
            type=reply_type,
            payload=payload,
            source="server",
            id=str(uuid.uuid4())
        )

    def error(self, error_message: str) -> 'Message':
        """Create an error response message"""
        return Message(
            type=MessageType.ERROR.value,
            payload={
                'original_type': self.type,
                'original_id': self.id,
                'error': error_message
            },
            source="server"
        )


def create_message(msg_type: MessageType | str, payload: Dict[str, Any] = None,
                   source: str = "client") -> Message:
    """Create a new message"""
    if isinstance(msg_type, MessageType):
        msg_type = msg_type.value
    return Message(
        type=msg_type,
        payload=payload or {},
        source=source
    )


def parse_message(data: str | bytes | Dict[str, Any]) -> Optional[Message]:
    """Parse a message from various input formats"""
    try:
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        if isinstance(data, str):
            data = json.loads(data)
        if isinstance(data, dict):
            return Message.from_dict(data)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None
    return None


# Predefined payload builders for common messages

def build_hello_payload(client_name: str, version: str = "1.0.0") -> Dict[str, Any]:
    """Build hello handshake payload"""
    return {
        'client_name': client_name,
        'version': version,
        'capabilities': ['status', 'actions', 'conversations', 'events']
    }


def build_status_payload(state: Dict[str, Any]) -> Dict[str, Any]:
    """Build status response payload"""
    return {
        'name': state.get('name', 'Claude'),
        'level': state.get('level', 1),
        'xp': state.get('xp', 0),
        'xp_to_next': state.get('xp_to_next', 100),
        'hunger': state.get('hunger', 100),
        'happiness': state.get('happiness', 100),
        'energy': state.get('energy', 100),
        'mood': state.get('mood', 'happy'),
        'is_sleeping': state.get('is_sleeping', False),
        'evolution_stage': state.get('evolution_stage', 0),
        'evolution_path': state.get('evolution_path', 'balanced'),
    }


def build_action_payload(action: str, **kwargs) -> Dict[str, Any]:
    """Build action payload"""
    return {
        'action': action,
        **kwargs
    }


def build_conversation_start_payload(title: str, tags: List[str] = None) -> Dict[str, Any]:
    """Build conversation start payload"""
    return {
        'title': title,
        'tags': tags or [],
        'started_at': datetime.now().isoformat()
    }


def build_conversation_message_payload(conversation_id: str, role: str,
                                       content: str, **kwargs) -> Dict[str, Any]:
    """Build conversation message payload"""
    return {
        'conversation_id': conversation_id,
        'role': role,  # 'user' or 'assistant'
        'content': content,
        'timestamp': datetime.now().isoformat(),
        **kwargs
    }


def build_restore_context_payload(conversation_id: str,
                                  include_messages: bool = True) -> Dict[str, Any]:
    """Build restore context payload"""
    return {
        'conversation_id': conversation_id,
        'include_messages': include_messages,
        'format': 'markdown'  # or 'json'
    }


def build_event_payload(event_type: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Build event payload"""
    return {
        'event_type': event_type,
        'data': data or {},
        'timestamp': datetime.now().isoformat()
    }
