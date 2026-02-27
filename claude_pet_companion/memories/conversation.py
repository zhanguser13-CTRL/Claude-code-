#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversation Memory System for Claude Pet Companion

Provides conversation tracking and storage for pet interactions.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import json
import uuid


class MessageRole(Enum):
    """Message role in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    PET = "pet"  # Pet's own responses


@dataclass
class ConversationMessage:
    """Single message in a conversation"""
    id: str
    role: str  # MessageRole value
    content: str
    timestamp: datetime

    # Additional metadata
    tool_used: Optional[str] = None
    files_touched: List[str] = field(default_factory=list)
    tokens_used: int = 0
    emotion: str = "neutral"  # Pet's emotion during this message

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'tool_used': self.tool_used,
            'files_touched': self.files_touched,
            'tokens_used': self.tokens_used,
            'emotion': self.emotion,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """Create from dictionary"""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            role=data.get('role', 'user'),
            content=data.get('content', ''),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            tool_used=data.get('tool_used'),
            files_touched=data.get('files_touched', []),
            tokens_used=data.get('tokens_used', 0),
            emotion=data.get('emotion', 'neutral'),
        )


@dataclass
class ConversationMemory:
    """A complete conversation session"""
    id: str
    session_id: str  # Links to MemoryManager session

    # Metadata
    title: str
    started_at: datetime
    ended_at: Optional[datetime] = None

    # Content
    messages: List[ConversationMessage] = field(default_factory=list)

    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    # Tracking
    task_ids: List[str] = field(default_factory=list)  # Related task IDs
    files_touched: List[str] = field(default_factory=list)
    total_tokens: int = 0

    # Outcome
    success: bool = True
    summary: str = ""

    # User feedback
    user_rating: Optional[int] = None  # 1-5 stars
    user_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'title': self.title,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'messages': [m.to_dict() for m in self.messages],
            'context': self.context,
            'tags': self.tags,
            'task_ids': self.task_ids,
            'files_touched': self.files_touched,
            'total_tokens': self.total_tokens,
            'success': self.success,
            'summary': self.summary,
            'user_rating': self.user_rating,
            'user_notes': self.user_notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMemory':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            session_id=data.get('session_id', ''),
            title=data['title'],
            started_at=datetime.fromisoformat(data['started_at']),
            ended_at=datetime.fromisoformat(data['ended_at']) if data.get('ended_at') else None,
            messages=[ConversationMessage.from_dict(m) for m in data.get('messages', [])],
            context=data.get('context', {}),
            tags=data.get('tags', []),
            task_ids=data.get('task_ids', []),
            files_touched=data.get('files_touched', []),
            total_tokens=data.get('total_tokens', 0),
            success=data.get('success', True),
            summary=data.get('summary', ''),
            user_rating=data.get('user_rating'),
            user_notes=data.get('user_notes', ''),
        )

    def add_message(self, role: str, content: str, **kwargs) -> ConversationMessage:
        """Add a message to this conversation"""
        message = ConversationMessage(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now(),
            **kwargs
        )
        self.messages.append(message)

        # Update tracking
        if kwargs.get('tokens_used'):
            self.total_tokens += kwargs['tokens_used']
        if kwargs.get('files_touched'):
            for f in kwargs['files_touched']:
                if f not in self.files_touched:
                    self.files_touched.append(f)

        return message

    def get_last_exchange(self) -> tuple[Optional[str], Optional[str]]:
        """Get the last user/assistant exchange"""
        last_user = None
        last_assistant = None

        for msg in reversed(self.messages):
            if msg.role == MessageRole.USER.value and not last_user:
                last_user = msg.content
            elif msg.role == MessageRole.ASSISTANT.value and not last_assistant:
                last_assistant = msg.content

            if last_user and last_assistant:
                break

        return last_user, last_assistant

    def get_files_summary(self) -> str:
        """Get a summary of files worked on"""
        if not self.files_touched:
            return "No files"

        # Group by extension
        from collections import Counter
        exts = Counter(Path(f).suffix.lower() for f in self.files_touched if f)

        parts = []
        for ext, count in exts.most_common(5):
            ext_name = ext[1:] if ext else "no extension"
            parts.append(f"{count} {ext_name}")

        return ", ".join(parts)

    def generate_summary(self) -> str:
        """Generate a summary of the conversation"""
        if not self.messages:
            return "Empty conversation"

        # Count messages by role
        from collections import Counter
        role_counts = Counter(m.role for m in self.messages)

        parts = []
        if role_counts.get('user'):
            parts.append(f"{role_counts['user']} user messages")
        if role_counts.get('assistant'):
            parts.append(f"{role_counts['assistant']} responses")

        summary = " | ".join(parts)

        if self.files_touched:
            summary += f" | Files: {self.get_files_summary()}"

        return summary


def create_conversation(title: str, session_id: str = "",
                        tags: List[str] = None) -> ConversationMemory:
    """Create a new conversation"""
    return ConversationMemory(
        id=str(uuid.uuid4()),
        session_id=session_id,
        title=title,
        started_at=datetime.now(),
        tags=tags or [],
    )


# For path handling (lazy import)
from pathlib import Path
