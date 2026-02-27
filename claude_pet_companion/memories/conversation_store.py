#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversation Store for Claude Pet Companion

Persistent storage for conversations.
"""
import json
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

from .conversation import ConversationMemory, create_conversation


class ConversationStore:
    """Store and manage conversations"""

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize the conversation store.

        Args:
            storage_dir: Directory for storing conversations. Defaults to ~/.claude-pet-companion/conversations/
        """
        if storage_dir is None:
            storage_dir = Path.home() / '.claude-pet-companion' / 'conversations'

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.index_file = self.storage_dir / 'index.json'
        self.lock = threading.Lock()

        # In-memory cache
        self._conversations: Dict[str, ConversationMemory] = {}
        self._index: Dict[str, Any] = {}

        # Load existing index
        self._load_index()

    def _load_index(self):
        """Load the conversation index"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self._index = json.load(f)

                # Pre-load metadata for all conversations
                for conv_id, meta in self._index.get('conversations', {}).items():
                    if meta.get('deleted', False):
                        continue
                    # Don't load full conversation, just metadata
                    self._conversations[conv_id] = None  # Lazy load

            except (json.JSONDecodeError, IOError):
                self._index = {'conversations': {}, 'last_updated': None}
        else:
            self._index = {'conversations': {}, 'last_updated': None}

    def _save_index(self):
        """Save the conversation index"""
        self._index['last_updated'] = datetime.now().isoformat()

        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self._index, f, indent=2, ensure_ascii=False)

    def _get_conversation_path(self, conversation_id: str) -> Path:
        """Get the file path for a conversation"""
        return self.storage_dir / f'{conversation_id}.json'

    def start_conversation(self, title: str, tags: List[str] = None,
                          session_id: str = "") -> str:
        """
        Start a new conversation.

        Args:
            title: Conversation title
            tags: Optional tags
            session_id: Optional session ID

        Returns:
            The new conversation ID
        """
        with self.lock:
            conv = create_conversation(title, session_id, tags)

            # Save to file
            self._save_conversation(conv)

            # Update index
            self._index['conversations'][conv.id] = {
                'id': conv.id,
                'title': conv.title,
                'started_at': conv.started_at.isoformat(),
                'ended_at': None,
                'tags': conv.tags,
                'message_count': 0,
                'deleted': False,
            }
            self._save_index()

            # Cache
            self._conversations[conv.id] = conv

            return conv.id

    def add_message(self, conversation_id: str, role: str, content: str,
                   **kwargs) -> bool:
        """
        Add a message to a conversation.

        Args:
            conversation_id: The conversation ID
            role: Message role (user, assistant, etc.)
            content: Message content
            **kwargs: Additional message metadata

        Returns:
            True if message was added, False otherwise
        """
        with self.lock:
            conv = self._load_or_get(conversation_id)
            if not conv:
                return False

            conv.add_message(role, content, **kwargs)

            # Save updated conversation
            self._save_conversation(conv)

            # Update index
            if conv.id in self._index['conversations']:
                self._index['conversations'][conv.id]['message_count'] = len(conv.messages)
                self._save_index()

            return True

    def end_conversation(self, conversation_id: str, summary: str = "",
                        success: bool = True, rating: int = None):
        """
        End a conversation.

        Args:
            conversation_id: The conversation ID
            summary: Optional summary
            success: Whether the conversation was successful
            rating: Optional user rating (1-5)
        """
        with self.lock:
            conv = self._load_or_get(conversation_id)
            if not conv:
                return

            conv.ended_at = datetime.now()
            conv.summary = summary
            conv.success = success
            conv.user_rating = rating

            # If no summary provided, generate one
            if not summary:
                conv.summary = conv.generate_summary()

            # Save
            self._save_conversation(conv)

            # Update index
            if conv.id in self._index['conversations']:
                self._index['conversations'][conv.id]['ended_at'] = conv.ended_at.isoformat()
                self._index['conversations'][conv.id]['summary'] = conv.summary
                self._save_index()

    def get_conversation(self, conversation_id: str) -> Optional[ConversationMemory]:
        """
        Get a conversation by ID.

        Args:
            conversation_id: The conversation ID

        Returns:
            The conversation, or None if not found
        """
        with self.lock:
            return self._load_or_get(conversation_id)

    def list_conversations(self, limit: int = 50,
                          include_deleted: bool = False) -> List[Dict[str, Any]]:
        """
        List conversations.

        Args:
            limit: Maximum number to return
            include_deleted: Whether to include deleted conversations

        Returns:
            List of conversation metadata
        """
        with self.lock:
            convs = []

            for conv_id, meta in self._index.get('conversations', {}).items():
                if not include_deleted and meta.get('deleted', False):
                    continue

                convs.append({
                    'id': conv_id,
                    'title': meta.get('title', 'Untitled'),
                    'started_at': meta.get('started_at'),
                    'ended_at': meta.get('ended_at'),
                    'tags': meta.get('tags', []),
                    'message_count': meta.get('message_count', 0),
                    'summary': meta.get('summary', ''),
                })

            # Sort by start time (newest first)
            convs.sort(key=lambda x: x.get('started_at', ''), reverse=True)

            return convs[:limit]

    def search_conversations(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search conversations by query.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching conversations
        """
        query = query.lower()
        results = []

        with self.lock:
            for conv_id, meta in self._index.get('conversations', {}).items():
                if meta.get('deleted', False):
                    continue

                # Search in title
                if query in meta.get('title', '').lower():
                    results.append(meta)
                    continue

                # Search in tags
                if any(query in tag.lower() for tag in meta.get('tags', [])):
                    results.append(meta)
                    continue

                # Search in summary
                if query in meta.get('summary', '').lower():
                    results.append(meta)
                    continue

                if len(results) >= limit:
                    break

        return results[:limit]

    def delete_conversation(self, conversation_id: str, permanent: bool = False):
        """
        Delete a conversation.

        Args:
            conversation_id: The conversation ID
            permanent: If True, permanently delete; otherwise mark as deleted
        """
        with self.lock:
            if permanent:
                # Remove from index
                if conversation_id in self._index.get('conversations', {}):
                    del self._index['conversations'][conversation_id]
                    self._save_index()

                # Remove file
                conv_path = self._get_conversation_path(conversation_id)
                if conv_path.exists():
                    conv_path.unlink()

                # Remove from cache
                self._conversations.pop(conversation_id, None)

            else:
                # Mark as deleted
                if conversation_id in self._index.get('conversations', {}):
                    self._index['conversations'][conversation_id]['deleted'] = True
                    self._save_index()

    def _load_or_get(self, conversation_id: str) -> Optional[ConversationMemory]:
        """Load a conversation if not cached, or return from cache"""
        # Check cache
        if conversation_id in self._conversations:
            cached = self._conversations[conversation_id]
            if cached is not None:
                return cached

        # Check if conversation exists
        conv_path = self._get_conversation_path(conversation_id)
        if not conv_path.exists():
            return None

        try:
            with open(conv_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            conv = ConversationMemory.from_dict(data)
            self._conversations[conversation_id] = conv
            return conv

        except (json.JSONDecodeError, IOError, KeyError):
            return None

    def _save_conversation(self, conv: ConversationMemory):
        """Save a conversation to disk"""
        conv_path = self._get_conversation_path(conv.id)

        with open(conv_path, 'w', encoding='utf-8') as f:
            json.dump(conv.to_dict(), f, indent=2, ensure_ascii=False)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored conversations"""
        with self.lock:
            total = len(self._index.get('conversations', {}))
            active = sum(1 for m in self._index.get('conversations', {}).values()
                        if not m.get('deleted', False))

            # Count by tags
            tag_counts = defaultdict(int)
            for meta in self._index.get('conversations', {}).values():
                if meta.get('deleted', False):
                    continue
                for tag in meta.get('tags', []):
                    tag_counts[tag] += 1

            return {
                'total_conversations': total,
                'active_conversations': active,
                'deleted_conversations': total - active,
                'tag_counts': dict(tag_counts),
            }


# Singleton instance
_conversation_store: Optional[ConversationStore] = None


def get_conversation_store() -> ConversationStore:
    """Get or create the singleton conversation store"""
    global _conversation_store
    if _conversation_store is None:
        _conversation_store = ConversationStore()
    return _conversation_store
