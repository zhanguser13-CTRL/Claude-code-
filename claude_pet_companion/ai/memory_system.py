"""
Memory System for Claude Pet Companion

Provides realistic memory with:
- Short-term and long-term memory
- Memory importance scoring
- Memory decay and forgetting
- Emotional memory association
- Memory recall and retrieval
- Contextual memory triggering
"""

import logging
import random
import time
import json
from typing import Dict, List, Tuple, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import hashlib

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memories."""
    EVENT = "event"           # Something that happened
    INTERACTION = "interaction"  # Interaction with owner
    PLACE = "place"           # Location memory
    PERSON = "person"         # Memory of a person
    OBJECT = "object"         # Memory of an object
    EMOTION = "emotion"       # Emotional memory
    SKILL = "skill"           # Learned skill
    TRAUMA = "trauma"         # Negative experience
    JOY = "joy"              # Positive experience


class MemoryImportance(Enum):
    """Importance levels affecting retention."""
    FORGOTTEN = 0     # Will be forgotten quickly
    LOW = 1           # Minor memory
    MEDIUM = 2        # Notable memory
    HIGH = 3          # Important memory
    CRITICAL = 4      # Life-changing memory
    CORE = 5          # Defining memory


@dataclass
class Memory:
    """A single memory with metadata."""

    # Core memory data
    memory_type: MemoryType
    content: str  # Description of what happened
    importance: MemoryImportance = MemoryImportance.MEDIUM

    # Timestamps
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0

    # Associations
    emotions: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    related_entities: Set[str] = field(default_factory=set)  # People, places, objects

    # Decay
    decay_rate: float = 0.001  # Per day (lower = longer memory)
    strength: float = 1.0  # Current strength (0-1)

    # Context
    context: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        """Make memory hashable for sets."""
        return hash((self.memory_type, self.content, self.created_at))

    def get_age(self) -> float:
        """Get age of memory in seconds."""
        return time.time() - self.created_at

    def get_age_days(self) -> float:
        """Get age of memory in days."""
        return self.get_age() / 86400

    def is_forgotten(self) -> bool:
        """Check if memory has been forgotten."""
        return self.strength < 0.1

    def access(self):
        """Access this memory (boosts retention)."""
        self.last_accessed = time.time()
        self.access_count += 1
        # Boost strength slightly on access
        self.strength = min(1.0, self.strength + 0.1)

    def decay(self, dt_days: float = 1.0):
        """Apply decay to memory strength."""
        # Importance affects decay rate
        importance_modifier = (self.importance.value + 1) * 0.2
        actual_decay = self.decay_rate / importance_modifier

        # Access also slows decay
        access_modifier = 1.0 / (1.0 + self.access_count * 0.1)

        self.strength -= actual_decay * dt_days * access_modifier
        self.strength = max(0.0, self.strength)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'memory_type': self.memory_type.value,
            'content': self.content,
            'importance': self.importance.value,
            'created_at': self.created_at,
            'last_accessed': self.last_accessed,
            'access_count': self.access_count,
            'emotions': list(self.emotions),
            'tags': list(self.tags),
            'related_entities': list(self.related_entities),
            'decay_rate': self.decay_rate,
            'strength': self.strength,
            'context': self.context,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Memory':
        """Create memory from dictionary."""
        return cls(
            memory_type=MemoryType(data['memory_type']),
            content=data['content'],
            importance=MemoryImportance(data['importance']),
            created_at=data['created_at'],
            last_accessed=data['last_accessed'],
            access_count=data['access_count'],
            emotions=set(data.get('emotions', [])),
            tags=set(data.get('tags', [])),
            related_entities=set(data.get('related_entities', [])),
            decay_rate=data.get('decay_rate', 0.001),
            strength=data.get('strength', 1.0),
            context=data.get('context', {}),
        )


class MemoryNetwork:
    """Associative memory network for linking related memories."""

    def __init__(self):
        # Memory ID to memory mapping
        self.memories: Dict[str, Memory] = {}

        # Associations: memory_id -> set of related memory_ids
        self.associations: Dict[str, Set[str]] = {}

        # Entity to memories mapping
        self.entity_memories: Dict[str, Set[str]] = {}

        # Tag to memories mapping
        self.tag_memories: Dict[str, Set[str]] = {}

        # Emotional memories
        self.emotional_memories: Dict[str, Set[str]] = {}

    def _generate_id(self, memory: Memory) -> str:
        """Generate unique ID for memory."""
        content_hash = hashlib.md5(
            f"{memory.content}{memory.created_at}".encode()
        ).hexdigest()[:8]
        return f"{memory.memory_type.value}_{content_hash}"

    def add_memory(self, memory: Memory) -> str:
        """Add a memory to the network."""
        memory_id = self._generate_id(memory)
        self.memories[memory_id] = memory

        # Index by entity
        for entity in memory.related_entities:
            if entity not in self.entity_memories:
                self.entity_memories[entity] = set()
            self.entity_memories[entity].add(memory_id)

        # Index by tag
        for tag in memory.tags:
            if tag not in self.tag_memories:
                self.tag_memories[tag] = set()
            self.tag_memories[tag].add(memory_id)

        # Index by emotion
        for emotion in memory.emotions:
            if emotion not in self.emotional_memories:
                self.emotional_memories[emotion] = set()
            self.emotional_memories[emotion].add(memory_id)

        # Create associations with similar memories
        self._create_associations(memory_id, memory)

        return memory_id

    def _create_associations(self, memory_id: str, memory: Memory):
        """Create associations with similar existing memories."""
        self.associations[memory_id] = set()

        # Find memories with shared entities
        for entity in memory.related_entities:
            if entity in self.entity_memories:
                for other_id in self.entity_memories[entity]:
                    if other_id != memory_id:
                        self.associations[memory_id].add(other_id)
                        self.associations.setdefault(other_id, set()).add(memory_id)

        # Find memories with same tags
        for tag in memory.tags:
            if tag in self.tag_memories:
                for other_id in self.tag_memories[tag]:
                    if other_id != memory_id and other_id not in self.associations[memory_id]:
                        self.associations[memory_id].add(other_id)

    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by ID."""
        if memory_id in self.memories:
            self.memories[memory_id].access()
        return self.memories.get(memory_id)

    def recall_by_entity(self, entity: str, limit: int = 10) -> List[Tuple[str, Memory]]:
        """Recall memories related to an entity."""
        results = []
        if entity in self.entity_memories:
            for memory_id in self.entity_memories[entity]:
                if memory_id in self.memories:
                    memory = self.memories[memory_id]
                    if not memory.is_forgotten():
                        memory.access()
                        results.append((memory_id, memory))

        # Sort by strength and recency
        results.sort(key=lambda x: (x[1].strength, -x[1].last_accessed), reverse=True)
        return results[:limit]

    def recall_by_emotion(self, emotion: str, limit: int = 10) -> List[Tuple[str, Memory]]:
        """Recall memories with a specific emotion."""
        results = []
        if emotion in self.emotional_memories:
            for memory_id in self.emotional_memories[emotion]:
                if memory_id in self.memories:
                    memory = self.memories[memory_id]
                    if not memory.is_forgotten():
                        memory.access()
                        results.append((memory_id, memory))

        results.sort(key=lambda x: x[1].strength, reverse=True)
        return results[:limit]

    def recall_by_tag(self, tag: str, limit: int = 10) -> List[Tuple[str, Memory]]:
        """Recall memories with a specific tag."""
        results = []
        if tag in self.tag_memories:
            for memory_id in self.tag_memories[tag]:
                if memory_id in self.memories:
                    memory = self.memories[memory_id]
                    if not memory.is_forgotten():
                        memory.access()
                        results.append((memory_id, memory))

        results.sort(key=lambda x: x[1].strength, reverse=True)
        return results[:limit]

    def recall_associated(self, memory_id: str, limit: int = 5) -> List[Tuple[str, Memory]]:
        """Recall memories associated with a given memory."""
        results = []
        if memory_id in self.associations:
            for associated_id in self.associations[memory_id]:
                if associated_id in self.memories:
                    memory = self.memories[associated_id]
                    if not memory.is_forgotten():
                        memory.access()
                        results.append((associated_id, memory))

        results.sort(key=lambda x: x[1].strength, reverse=True)
        return results[:limit]

    def search(self, query: str, limit: int = 10) -> List[Tuple[str, Memory]]:
        """Search memories by content."""
        query_lower = query.lower()
        results = []

        for memory_id, memory in self.memories.items():
            if memory.is_forgotten():
                continue
            if query_lower in memory.content.lower():
                memory.access()
                results.append((memory_id, memory))

        results.sort(key=lambda x: x[1].strength, reverse=True)
        return results[:limit]

    def forget_old_memories(self, max_age_days: float = 365):
        """Remove memories that are too old or forgotten."""
        to_remove = []

        for memory_id, memory in self.memories.items():
            # Remove if very old or forgotten (unless critical/core importance)
            if (memory.importance not in (MemoryImportance.CRITICAL, MemoryImportance.CORE) and
                (memory.get_age_days() > max_age_days or memory.is_forgotten())):
                to_remove.append(memory_id)

        for memory_id in to_remove:
            self._remove_memory(memory_id)

        return len(to_remove)

    def _remove_memory(self, memory_id: str):
        """Remove a memory from the network."""
        if memory_id not in self.memories:
            return

        memory = self.memories[memory_id]

        # Remove from entity index
        for entity in memory.related_entities:
            if entity in self.entity_memories and memory_id in self.entity_memories[entity]:
                self.entity_memories[entity].remove(memory_id)

        # Remove from tag index
        for tag in memory.tags:
            if tag in self.tag_memories and memory_id in self.tag_memories[tag]:
                self.tag_memories[tag].remove(memory_id)

        # Remove from emotion index
        for emotion in memory.emotions:
            if emotion in self.emotional_memories and memory_id in self.emotional_memories[emotion]:
                self.emotional_memories[emotion].remove(memory_id)

        # Remove associations
        if memory_id in self.associations:
            for associated_id in self.associations[memory_id]:
                if associated_id in self.associations:
                    self.associations[associated_id].discard(memory_id)

        del self.memories[memory_id]
        self.associations.pop(memory_id, None)

    def decay_all(self, dt_days: float = 1.0):
        """Apply decay to all memories."""
        for memory in self.memories.values():
            memory.decay(dt_days)

    def get_summary(self) -> Dict:
        """Get summary of memory network."""
        return {
            'total_memories': len(self.memories),
            'entities': len(self.entity_memories),
            'tags': len(self.tag_memories),
            'emotions': len(self.emotional_memories),
            'associations': sum(len(a) for a in self.associations.values()) // 2,
        }


class MemorySystem:
    """
    Main memory system managing short-term and long-term memory.
    """

    def __init__(self, short_term_capacity: int = 20, long_term_capacity: int = 1000):
        self.short_term = deque(maxlen=short_term_capacity)
        self.long_term = MemoryNetwork()
        self.short_term_capacity = short_term_capacity
        self.long_term_capacity = long_term_capacity

        # Working memory (currently active thoughts)
        self.working_memory: List[str] = []

        # Last decay time
        self.last_decay = time.time()

    def remember(self, content: str, memory_type: MemoryType = MemoryType.EVENT,
                importance: MemoryImportance = MemoryImportance.MEDIUM,
                entities: List[str] = None, tags: List[str] = None,
                emotions: List[str] = None, context: Dict = None) -> str:
        """
        Create a new memory.

        Args:
            content: Description of the memory
            memory_type: Type of memory
            importance: Importance level
            entities: Related entities (people, places, objects)
            tags: Tags for categorization
            emotions: Associated emotions
            context: Additional context

        Returns:
            Memory ID
        """
        memory = Memory(
            memory_type=memory_type,
            content=content,
            importance=importance,
            related_entities=set(entities or []),
            tags=set(tags or []),
            emotions=set(emotions or []),
            context=context or {}
        )

        # Add to short term
        memory_id = self.long_term.add_memory(memory)
        self.short_term.append(memory_id)

        return memory_id

    def recall(self, query: str = None, entity: str = None,
              emotion: str = None, tag: str = None,
              limit: int = 10) -> List[Tuple[str, Memory]]:
        """
        Recall memories based on criteria.

        Args:
            query: Search query for content
            entity: Related entity to search
            emotion: Emotion to search
            tag: Tag to search
            limit: Maximum results

        Returns:
            List of (memory_id, memory) tuples
        """
        if query:
            return self.long_term.search(query, limit)
        elif entity:
            return self.long_term.recall_by_entity(entity, limit)
        elif emotion:
            return self.long_term.recall_by_emotion(emotion, limit)
        elif tag:
            return self.long_term.recall_by_tag(tag, limit)
        else:
            # Return recent short-term memories
            results = []
            for memory_id in list(self.short_term)[-limit:]:
                memory = self.long_term.get_memory(memory_id)
                if memory:
                    results.append((memory_id, memory))
            return results

    def trigger_memory(self, trigger_type: str, entity: str = None) -> List[Memory]:
        """
        Trigger memory recall based on current situation.

        Args:
            trigger_type: Type of trigger ("see", "hear", "place", etc.)
            entity: Entity that triggered the memory

        Returns:
            List of triggered memories
        """
        triggered = []

        if entity:
            # Recall memories related to this entity
            entity_memories = self.long_term.recall_by_entity(entity, limit=5)
            for memory_id, memory in entity_memories:
                triggered.append(memory)
                self.working_memory.append(memory_id)

        # Also recall associated memories
        if triggered and entity:
            for memory_id, memory in entity_memories[:1]:  # First result
                associated = self.long_term.recall_associated(memory_id, limit=3)
                for assoc_id, assoc_memory in associated:
                    if assoc_memory not in triggered:
                        triggered.append(assoc_memory)

        return triggered

    def update(self, dt: float = None):
        """Update memory system (decay, etc.)."""
        if dt is None:
            dt = time.time() - self.last_decay
            if dt < 3600:  # Only decay once per hour minimum
                return

        dt_days = dt / 86400
        self.long_term.decay_all(dt_days)
        self.last_decay = time.time()

        # Clean working memory
        if len(self.working_memory) > 5:
            self.working_memory = self.working_memory[-5:]

    def consolidate(self):
        """Move important short-term memories to long-term."""
        # In this implementation, all memories go to long-term
        # Short-term is just a buffer for recent access
        pass

    def forget(self, memory_id: str):
        """Explicitly forget a memory."""
        self.long_term._remove_memory(memory_id)

    def get_stats(self) -> Dict:
        """Get memory system statistics."""
        return {
            'short_term_count': len(self.short_term),
            'short_term_capacity': self.short_term_capacity,
            'long_term_summary': self.long_term.get_summary(),
            'working_memory_count': len(self.working_memory),
        }


# Convenience functions

def create_memory(content: str, **kwargs) -> Memory:
    """Create a memory object."""
    return Memory(
        memory_type=kwargs.get('memory_type', MemoryType.EVENT),
        content=content,
        importance=kwargs.get('importance', MemoryImportance.MEDIUM),
        related_entities=set(kwargs.get('entities', [])),
        tags=set(kwargs.get('tags', [])),
        emotions=set(kwargs.get('emotions', [])),
        context=kwargs.get('context', {})
    )


if __name__ == "__main__":
    # Test memory system
    print("Testing Memory System")

    system = MemorySystem()

    # Add some memories
    print("\nAdding memories:")
    m1 = system.remember(
        "Played with owner in the garden",
        memory_type=MemoryType.INTERACTION,
        importance=MemoryImportance.HIGH,
        entities=["owner", "garden"],
        tags=["play", "outdoors"],
        emotions=["joy", "excitement"]
    )
    print(f"  Added: {m1}")

    m2 = system.remember(
        "Ate delicious fish treat",
        memory_type=MemoryType.EVENT,
        importance=MemoryImportance.MEDIUM,
        entities=["fish_treat"],
        tags=["food"],
        emotions=["joy"]
    )
    print(f"  Added: {m2}")

    m3 = system.remember(
        "Scary thunderstorm",
        memory_type=MemoryType.TRAUMA,
        importance=MemoryImportance.HIGH,
        entities=["thunder"],
        tags=["weather", "scary"],
        emotions=["fear"]
    )
    print(f"  Added: {m3}")

    # Test recall
    print("\nRecall by entity 'owner':")
    for memory_id, memory in system.recall(entity="owner"):
        print(f"  {memory.content} (strength: {memory.strength:.2f})")

    print("\nRecall by tag 'food':")
    for memory_id, memory in system.recall(tag="food"):
        print(f"  {memory.content}")

    print("\nRecall by emotion 'fear':")
    for memory_id, memory in system.recall(emotion="fear"):
        print(f"  {memory.content}")

    # Test search
    print("\nSearch 'treat':")
    for memory_id, memory in system.recall(query="treat"):
        print(f"  {memory.content}")

    # Test associated memories
    print("\nAssociated with first memory:")
    for memory_id, memory in system.long_term.recall_associated(m1):
        print(f"  {memory.content}")

    # Test stats
    print(f"\nMemory stats: {system.get_stats()}")

    # Test decay
    print("\nSimulating decay (30 days):")
    system.update(dt=30 * 86400)
    for memory_id, memory in system.recall(entity="owner"):
        print(f"  {memory.content} (strength: {memory.strength:.2f})")

    print("\nMemory system test passed!")
