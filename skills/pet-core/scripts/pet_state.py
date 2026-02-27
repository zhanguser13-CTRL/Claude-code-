"""
PetState - Core state management for Claude Code Pet Companion

Handles pet state persistence, loading, saving, and core state operations.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class PetState:
    """Core pet state class that manages all pet attributes and persistence."""

    # Basic Info
    name: str = "Pixel"
    species: str = "code-companion"

    # Level System
    level: int = 1
    xp: int = 0
    xp_to_next_level: int = 100
    total_xp: int = 0

    # Core Stats (0-100)
    hunger: int = 100
    happiness: int = 100
    energy: int = 100

    # State
    mood: str = "content"  # content, happy, excited, worried, sad, sleepy, hungry
    is_sleeping: bool = False
    is_active: bool = True

    # Evolution
    evolution_stage: int = 0
    evolution_name: str = "Egg"

    # Progress
    achievements: List[str] = field(default_factory=list)

    # Coding Stats
    files_created: int = 0
    files_modified: int = 0
    commands_run: int = 0
    errors_fixed: int = 0
    consecutive_successes: int = 0
    consecutive_failures: int = 0
    total_sessions: int = 0

    # Interaction Stats
    times_fed: int = 0
    times_played: int = 0
    times_slept: int = 0

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    last_meal_time: Optional[str] = None
    last_sleep_time: Optional[str] = None
    last_interaction: Optional[str] = None

    # Position for UI
    position: Dict[str, int] = field(default_factory=lambda: {"left": 100, "top": 100})

    def __post_init__(self):
        """Initialize derived values after creation."""
        self.update_evolution_name()

    def update_evolution_name(self):
        """Update evolution name based on stage."""
        evolution_names = {
            0: "Egg",
            1: "Baby",
            2: "Child",
            3: "Teen",
            4: "Adult",
            5: "Elder",
            6: "Ancient"
        }
        self.evolution_name = evolution_names.get(self.evolution_stage, "Unknown")

    @classmethod
    def get_state_file(cls) -> Path:
        """Get the path to the state file."""
        # Try to get from environment variable first
        plugin_root = os.environ.get('CLAUDE_PLUGIN_ROOT')
        if plugin_root:
            return Path(plugin_root) / 'data' / 'pet_state.json'
        # Fallback to current directory
        return Path.cwd() / 'claude-pet-companion' / 'data' / 'pet_state.json'

    @classmethod
    def load(cls) -> 'PetState':
        """Load pet state from file, or create new if doesn't exist."""
        state_file = cls.get_state_file()

        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return cls(**data)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error loading state file: {e}. Creating new state.")
                return cls()
        else:
            # Ensure directory exists
            state_file.parent.mkdir(parents=True, exist_ok=True)
            return cls()

    def save(self) -> bool:
        """Save pet state to file."""
        try:
            state_file = self.get_state_file()
            state_file.parent.mkdir(parents=True, exist_ok=True)

            self.last_updated = datetime.now().isoformat()

            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving state: {e}")
            return False

    def update_mood(self, new_mood: str):
        """Update the pet's mood."""
        valid_moods = [
            "content", "happy", "excited", "worried",
            "sad", "sleepy", "hungry", "ecstatic",
            "confused", "proud", "lonely"
        ]
        if new_mood in valid_moods:
            self.mood = new_mood

    def add_xp(self, amount: int) -> bool:
        """Add XP and check for level up. Returns True if leveled up."""
        self.xp += amount
        self.total_xp += amount

        leveled_up = False
        while self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            self.xp_to_next_level = self.calculate_xp_for_level(self.level)
            leveled_up = True

        return leveled_up

    def calculate_xp_for_level(self, level: int) -> int:
        """Calculate XP needed for a given level."""
        return int(100 * (1.5 ** (level - 1)))

    def can_evolve(self) -> bool:
        """Check if pet can evolve based on level."""
        evolution_levels = [10, 20, 30, 50, 75, 100]
        return self.level in evolution_levels and self.evolution_stage < 6

    def evolve(self) -> bool:
        """Evolve the pet to next stage. Returns True if evolved."""
        if self.can_evolve():
            self.evolution_stage += 1
            self.update_evolution_name()
            return True
        return False

    def add_achievement(self, achievement_id: str) -> bool:
        """Add an achievement. Returns True if newly unlocked."""
        if achievement_id not in self.achievements:
            self.achievements.append(achievement_id)
            return True
        return False

    def modify_stat(self, stat: str, amount: int) -> int:
        """Modify a stat (hunger, happiness, energy) and clamp to 0-100."""
        if hasattr(self, stat):
            current = getattr(self, stat)
            new_value = max(0, min(100, current + amount))
            setattr(self, stat, new_value)
            return new_value
        return 0

    def is_meal_time(self) -> tuple[bool, str]:
        """Check if it's currently meal time. Returns (is_meal_time, meal_name)."""
        hour = datetime.now().hour

        meal_times = {
            "breakfast": (7, 9),
            "lunch": (12, 14),
            "dinner": (18, 20)
        }

        for meal_name, (start, end) in meal_times.items():
            if start <= hour <= end:
                return True, meal_name

        return False, ""

    def should_be_sleeping(self) -> bool:
        """Check if pet should be sleeping based on time of day."""
        hour = datetime.now().hour
        return hour >= 22 or hour < 6

    def record_activity(self, activity_type: str, success: bool = True):
        """Record a coding activity."""
        if success:
            self.consecutive_successes += 1
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
            self.consecutive_successes = 0

        if activity_type == "file_created":
            self.files_created += 1
        elif activity_type == "file_modified":
            self.files_modified += 1
        elif activity_type == "command_run":
            self.commands_run += 1
        elif activity_type == "error_fixed":
            self.errors_fixed += 1

    def get_summary(self) -> str:
        """Get a text summary of pet status."""
        mood_emojis = {
            "content": "😊",
            "happy": "😄",
            "excited": "🤩",
            "worried": "😟",
            "sad": "😢",
            "sleepy": "😴",
            "hungry": "😋",
            "ecstatic": "🥳",
            "confused": "😕",
            "proud": "😎",
            "lonely": "😔"
        }

        emoji = mood_emojis.get(self.mood, "🐾")
        sleep_status = " (Sleeping)" if self.is_sleeping else ""

        return f"""
╔═════════════════════════════╗
║   {self.name} the {self.evolution_name}   ║
║      Level {self.level} {emoji}{' ' * (15 - len(str(self.level)) - len(self.evolution_name) - 6)}║
╠═════════════════════════════╣
║ Mood: {self.mood.capitalize():12} {' ' * (10 - len(self.mood))} ║
║ Hunger: {'█' * (self.hunger // 10)}{' ' * (10 - self.hunger // 10)} {self.hunger:3}/100 ║
║ Happy:  {'█' * (self.happiness // 10)}{' ' * (10 - self.happiness // 10)} {self.happiness:3}/100 ║
║ Energy: {'█' * (self.energy // 10)}{' ' * (10 - self.energy // 10)} {self.energy:3}/100 ║
║ XP: {self.xp:4}/{self.xp_to_next_level:4}{' ' * (9 - len(str(self.xp)) - len(str(self.xp_to_next_level)))} ║
╠═════════════════════════════╣
║ Files: {self.files_created} created | {self.files_modified} edited ║
║ Session #{self.total_sessions}{' ' * (7 - len(str(self.total_sessions)))} ║
╚═════════════════════════════╝{sleep_status}
        """.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PetState':
        """Create state from dictionary."""
        return cls(**data)


def get_state() -> PetState:
    """Get the current pet state (singleton pattern with file backing)."""
    return PetState.load()


def save_state(state: PetState) -> bool:
    """Save the pet state."""
    return state.save()


if __name__ == "__main__":
    # Test creating and saving state
    state = PetState()
    print("Created new pet state:")
    print(state.get_summary())
    state.save()
    print(f"\nSaved to: {PetState.get_state_file()}")
