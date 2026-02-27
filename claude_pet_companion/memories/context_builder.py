#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Context Builder for Claude Pet Companion

Build conversation context from stored conversations for restoration.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from .conversation import ConversationMemory, MessageRole
from .conversation_store import ConversationStore


class ContextBuilder:
    """Build context from conversations for restoration"""

    def __init__(self, store: ConversationStore):
        """
        Initialize the context builder.

        Args:
            store: The conversation store
        """
        self.store = store

    def build_context(self, conversation_id: str,
                     format: str = 'markdown',
                     max_messages: int = 50) -> str:
        """
        Build context from a conversation.

        Args:
            conversation_id: The conversation ID
            format: Output format ('markdown' or 'json')
            max_messages: Maximum messages to include

        Returns:
            The formatted context string
        """
        conv = self.store.get_conversation(conversation_id)
        if not conv:
            return ""

        if format == 'json':
            import json
            return json.dumps(conv.to_dict(), indent=2, ensure_ascii=False)

        return self._build_markdown_context(conv, max_messages)

    def _build_markdown_context(self, conv: ConversationMemory,
                               max_messages: int) -> str:
        """Build markdown context from a conversation"""
        lines = []

        # Header
        lines.append(f"# Previous Conversation: {conv.title}")
        lines.append(f"**Date:** {conv.started_at.strftime('%Y-%m-%d %H:%M')}")
        if conv.ended_at:
            duration = (conv.ended_at - conv.started_at).total_seconds() / 60
            lines.append(f"**Duration:** {int(duration)} minutes")

        lines.append("")

        # Summary section
        if conv.summary:
            lines.append("## Summary")
            lines.append(conv.summary)
            lines.append("")

        # Key points
        lines.extend(self._extract_key_points(conv))

        # Files discussed
        if conv.files_touched:
            lines.append("## Files Discussed")
            # Group by extension
            from collections import Counter
            from pathlib import Path

            ext_groups = Counter()
            for f in conv.files_touched:
                ext = Path(f).suffix or 'no extension'
                ext_groups[ext] += 1

            for ext, count in ext_groups.most_common():
                lines.append(f"- {count} files with `{ext}` extension")

            lines.append("")

        # Tags
        if conv.tags:
            lines.append(f"**Tags:** {', '.join(f'`{tag}`' for tag in conv.tags)}")
            lines.append("")

        # Last exchange
        last_user, last_assistant = conv.get_last_exchange()
        if last_user or last_assistant:
            lines.append("## Last Exchange")
            if last_user:
                lines.append(f"**User:** {last_user[:500]}{'...' if len(last_user) > 500 else ''}")
            if last_assistant:
                lines.append(f"**Assistant:** {last_assistant[:500]}{'...' if len(last_assistant) > 500 else ''}")
            lines.append("")

        # Recent messages
        if conv.messages:
            lines.append("## Recent Messages")
            messages = conv.messages[-max_messages:]
            for msg in messages:
                role = msg.role.capitalize()
                content = msg.content
                # Truncate long messages
                if len(content) > 1000:
                    content = content[:1000] + "..."

                if msg.role == MessageRole.USER.value:
                    lines.append(f"**{role}:** {content}")
                else:
                    lines.append(f"**{role}:** {content}")

                lines.append("")

        return "\n".join(lines)

    def _extract_key_points(self, conv: ConversationMemory) -> List[str]:
        """Extract key points from a conversation"""
        points = []

        # Look for patterns in messages
        for msg in conv.messages[-20:]:  # Check last 20 messages
            content = msg.content.lower()

            # Look for success/error indicators
            if any(word in content for word in ['fixed', 'resolved', 'solved', 'working']):
                if "Issue resolved" not in points:
                    points.append("- Issue was resolved")
            elif any(word in content for word in ['error', 'failed', 'broken', "doesn't work"]):
                if "Errors encountered" not in points:
                    points.append("- Errors were encountered and addressed")

            # Look for file operations
            if msg.files_touched and len(msg.files_touched) > 2:
                if "Multiple files modified" not in points:
                    points.append(f"- Multiple files were modified")

            # Look for specific tool usage
            if msg.tool_used:
                if f"Used {msg.tool_used}" not in points:
                    points.append(f"- Used {msg.tool_used}")

        if not points:
            if conv.success:
                points = ["- Conversation completed successfully"]
            else:
                points = ["- Conversation may have unresolved issues"]

        return ["## Key Points"] + points + [""]

    def build_continue_context(self, conversation_id: str,
                              new_message: str = "") -> str:
        """
        Build context for continuing a conversation.

        This includes a brief summary and the last few messages
        to maintain context continuity.

        Args:
            conversation_id: The conversation to continue
            new_message: The new user message (optional)

        Returns:
            Context for continuation
        """
        conv = self.store.get_conversation(conversation_id)
        if not conv:
            return ""

        lines = []

        lines.append(f"# Continuing: {conv.title}")
        lines.append("")
        lines.append(f"*Originally: {conv.started_at.strftime('%Y-%m-%d %H:%M')}*")
        lines.append("")

        # Brief summary
        if conv.summary:
            lines.append(f"**Summary:** {conv.summary}")
        else:
            lines.append(f"**Summary:** {conv.generate_summary()}")

        lines.append("")

        # Last few messages for context
        lines.append("## Context from last messages:")
        for msg in conv.messages[-5:]:
            role = msg.role.capitalize()
            # Truncate
            content = msg.content
            if len(content) > 300:
                content = content[:300] + "..."

            lines.append(f"**{role}:** {content}")

        lines.append("")

        # New message if provided
        if new_message:
            lines.append("## New Message")
            lines.append(new_message)

        return "\n".join(lines)

    def build_quick_reference(self, conversation_id: str) -> str:
        """
        Build a quick reference summary for a conversation.

        Args:
            conversation_id: The conversation ID

        Returns:
            Quick reference string
        """
        conv = self.store.get_conversation(conversation_id)
        if not conv:
            return "Conversation not found"

        parts = []

        # Title and date
        parts.append(f"📋 {conv.title}")
        parts.append(f"📅 {conv.started_at.strftime('%Y-%m-%d %H:%M')}")

        # Stats
        parts.append(f"💬 {len(conv.messages)} messages")
        if conv.files_touched:
            parts.append(f"📁 {len(conv.files_touched)} files")

        # Tags
        if conv.tags:
            parts.append(f"🏷️ {' '.join(f'#{tag}' for tag in conv.tags[:3])}")

        # Last message preview
        if conv.messages:
            last_msg = conv.messages[-1]
            preview = last_msg.content[:50]
            if len(last_msg.content) > 50:
                preview += "..."
            parts.append(f"💭 {preview}")

        return "\n".join(parts)
