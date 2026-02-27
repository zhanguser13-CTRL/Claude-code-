#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversation Search for Claude Pet Companion

Search functionality for conversations.
"""
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import Counter

from .conversation import ConversationMemory
from .conversation_store import ConversationStore


class ConversationSearch:
    """Search and filter conversations"""

    def __init__(self, store: ConversationStore):
        """
        Initialize the search handler.

        Args:
            store: The conversation store to search
        """
        self.store = store

    def search(self, query: str = None, filters: Dict[str, Any] = None,
               limit: int = 20) -> List[ConversationMemory]:
        """
        Search conversations with optional filters.

        Args:
            query: Text search query
            filters: Optional filters (tags, date_range, etc.)
            limit: Maximum results

        Returns:
            List of matching conversations
        """
        # Get base list
        conv_list = self.store.list_conversations(limit=limit * 2)

        results = []
        for meta in conv_list:
            conv = self.store.get_conversation(meta['id'])
            if not conv:
                continue

            if self._matches_filters(conv, query, filters):
                results.append(conv)

            if len(results) >= limit:
                break

        return results

    def _matches_filters(self, conv: ConversationMemory,
                        query: str = None,
                        filters: Dict[str, Any] = None) -> bool:
        """Check if a conversation matches the search criteria"""
        if filters is None:
            filters = {}

        # Text search
        if query:
            query_lower = query.lower()

            # Search in title
            if query_lower in conv.title.lower():
                return True

            # Search in messages
            for msg in conv.messages:
                if query_lower in msg.content.lower():
                    return True

            # Search in tags
            if any(query_lower in tag.lower() for tag in conv.tags):
                return True

            # Search in summary
            if query_lower in conv.summary.lower():
                return True

            # If no match in text, fail
            return False

        # Tag filter
        if 'tags' in filters and filters['tags']:
            required_tags = set(filters['tags'])
            if not required_tags.intersection(conv.tags):
                return False

        # Date range filter
        if 'date_from' in filters:
            date_from = filters['date_from']
            if isinstance(date_from, str):
                date_from = datetime.fromisoformat(date_from)
            if conv.started_at < date_from:
                return False

        if 'date_to' in filters:
            date_to = filters['date_to']
            if isinstance(date_to, str):
                date_to = datetime.fromisoformat(date_to)
            if conv.started_at > date_to:
                return False

        # Success filter
        if 'success' in filters:
            if conv.success != filters['success']:
                return False

        # Has file filter
        if 'has_files' in filters and filters['has_files']:
            if not conv.files_touched:
                return False

        # Minimum messages filter
        if 'min_messages' in filters:
            if len(conv.messages) < filters['min_messages']:
                return False

        # File pattern filter
        if 'file_pattern' in filters:
            pattern = filters['file_pattern'].lower()
            if not any(pattern in f.lower() for f in conv.files_touched):
                return False

        return True

    def find_by_file(self, file_pattern: str, limit: int = 20) -> List[ConversationMemory]:
        """Find conversations that touched a specific file"""
        return self.search(
            filters={'file_pattern': file_pattern},
            limit=limit
        )

    def find_by_tag(self, tag: str, limit: int = 20) -> List[ConversationMemory]:
        """Find conversations with a specific tag"""
        return self.search(
            filters={'tags': [tag]},
            limit=limit
        )

    def find_recent(self, hours: int = 24, limit: int = 20) -> List[ConversationMemory]:
        """Find conversations from the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return self.search(
            filters={'date_from': cutoff.isoformat()},
            limit=limit
        )

    def find_successful(self, limit: int = 20) -> List[ConversationMemory]:
        """Find successful conversations"""
        return self.search(
            filters={'success': True},
            limit=limit
        )

    def get_trending_tags(self, limit: int = 10) -> List[tuple[str, int]]:
        """Get the most commonly used tags"""
        tag_counter = Counter()

        for meta in self.store.list_conversations(limit=1000):
            for tag in meta.get('tags', []):
                tag_counter[tag] += 1

        return tag_counter.most_common(limit)

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics"""
        convs = self.store.list_conversations(limit=10000)

        total = len(convs)
        if total == 0:
            return {'total': 0}

        # Count by outcome
        successful = sum(1 for c in convs if not c.get('ended_at') or c.get('summary', '') == '')

        # Total messages
        total_messages = sum(c.get('message_count', 0) for c in convs)

        # Active (not ended)
        active = sum(1 for c in convs if not c.get('ended_at'))

        # Recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent = sum(1 for c in convs
                    if c.get('started_at') and
                    datetime.fromisoformat(c['started_at']) > week_ago)

        return {
            'total_conversations': total,
            'active_conversations': active,
            'completed_conversations': total - active,
            'total_messages': total_messages,
            'recent_week': recent,
            'avg_messages_per_conversation': total_messages / total if total > 0 else 0,
        }


def create_search_query(text: str = None,
                        tags: List[str] = None,
                        date_from: str = None,
                        date_to: str = None,
                        file_pattern: str = None,
                        min_messages: int = None) -> Dict[str, Any]:
    """
    Create a search query dictionary.

    Args:
        text: Text search query
        tags: Tags to filter by
        date_from: Start date (ISO format)
        date_to: End date (ISO format)
        file_pattern: File pattern to search
        min_messages: Minimum message count

    Returns:
        Query dictionary
    """
    query = {}

    if text:
        query['text'] = text

    filters = {}
    if tags:
        filters['tags'] = tags
    if date_from:
        filters['date_from'] = date_from
    if date_to:
        filters['date_to'] = date_to
    if file_pattern:
        filters['file_pattern'] = file_pattern
    if min_messages:
        filters['min_messages'] = min_messages

    if filters:
        query['filters'] = filters

    return query
