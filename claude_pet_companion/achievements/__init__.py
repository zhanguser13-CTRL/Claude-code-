"""
Claude Code Pet Companion - Extended Achievement System

This module provides:
- Achievement categories and rarity levels
- 30+ achievements across multiple categories
- Achievement tracking and unlocking
- Reward system for achievements
"""
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


# ============================================================================
# Achievement Categories
# ============================================================================

class AchievementCategory(Enum):
    """Categories of achievements."""
    MILESTONE = "milestone"      # Level/evolution milestones
    CODING = "coding"            # Programming-related activities
    SOCIAL = "social"            # Social interactions
    TIME = "time"                # Time-based achievements
    SPECIAL = "special"          # Special/unique achievements
    SECRET = "secret"            # Hidden achievements


# ============================================================================
# Achievement Rarity
# ============================================================================

class AchievementRarity(Enum):
    """Rarity levels for achievements."""
    COMMON = "common"            # Easy to obtain
    RARE = "rare"                # Moderate difficulty
    EPIC = "epic"                # Hard to obtain
    LEGENDARY = "legendary"      # Very difficult
    MYTHIC = "mythic"            # Extremely rare/secret

    @property
    def xp_reward(self) -> int:
        """Get XP reward for this rarity."""
        return {
            AchievementRarity.COMMON: 50,
            AchievementRarity.RARE: 100,
            AchievementRarity.EPIC: 250,
            AchievementRarity.LEGENDARY: 500,
            AchievementRarity.MYTHIC: 1000,
        }[self]

    @property
    def color(self) -> str:
        """Get display color for this rarity."""
        return {
            AchievementRarity.COMMON: "#AAAAAA",
            AchievementRarity.RARE: "#5555FF",
            AchievementRarity.EPIC: "#AA00AA",
            AchievementRarity.LEGENDARY: "#FFAA00",
            AchievementRarity.MYTHIC: "#FF5555",
        }[self]


# ============================================================================
# Achievement Definition
# ============================================================================

@dataclass
class Achievement:
    """Represents a single achievement."""
    id: str
    name: str
    description: str
    category: AchievementCategory
    rarity: AchievementRarity
    requirement: str                 # Human-readable requirement
    check_func: Optional[Callable] = None  # Function to check if unlocked
    hidden: bool = False              # Whether achievement is hidden
    icon: Optional[str] = None        # Icon identifier
    rewards: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.rewards:
            self.rewards = {"xp": self.rarity.xp_reward}

    def check(self, context: Dict[str, Any]) -> bool:
        """
        Check if achievement is unlocked based on context.

        Args:
            context: Dictionary with current state/context

        Returns:
            True if achievement should be unlocked
        """
        if self.check_func:
            return self.check_func(context)
        return False

    def to_dict(self) -> Dict:
        """Convert achievement to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "rarity": self.rarity.value,
            "requirement": self.requirement,
            "hidden": self.hidden,
            "icon": self.icon,
            "rewards": self.rewards,
        }


# ============================================================================
# Achievement Definitions
# ============================================================================

# Milestone Achievements
MILESTONE_ACHIEVEMENTS: List[Achievement] = [
    Achievement(
        id="first_steps",
        name="First Steps",
        description="Begin your journey with your new companion",
        category=AchievementCategory.MILESTONE,
        rarity=AchievementRarity.COMMON,
        requirement="Hatch your pet egg",
        icon="egg",
    ),
    Achievement(
        id="level_5",
        name="Getting Stronger",
        description="Reach level 5",
        category=AchievementCategory.MILESTONE,
        rarity=AchievementRarity.COMMON,
        requirement="Reach level 5",
        check_func=lambda ctx: ctx.get("level", 0) >= 5,
        icon="star",
    ),
    Achievement(
        id="level_10",
        name="Rising Star",
        description="Reach level 10",
        category=AchievementCategory.MILESTONE,
        rarity=AchievementRarity.RARE,
        requirement="Reach level 10",
        check_func=lambda ctx: ctx.get("level", 0) >= 10,
        icon="star_2",
    ),
    Achievement(
        id="level_25",
        name="Veteran",
        description="Reach level 25",
        category=AchievementCategory.MILESTONE,
        rarity=AchievementRarity.EPIC,
        requirement="Reach level 25",
        check_func=lambda ctx: ctx.get("level", 0) >= 25,
        icon="star_3",
    ),
    Achievement(
        id="level_50",
        name="Legend",
        description="Reach level 50",
        category=AchievementCategory.MILESTONE,
        rarity=AchievementRarity.LEGENDARY,
        requirement="Reach level 50",
        check_func=lambda ctx: ctx.get("level", 0) >= 50,
        icon="crown",
    ),
    Achievement(
        id="first_evolution",
        name="Metamorphosis",
        description="Witness your pet's first evolution",
        category=AchievementCategory.MILESTONE,
        rarity=AchievementRarity.RARE,
        requirement="Evolve for the first time",
        icon="evolution",
    ),
    Achievement(
        id="final_evolution",
        name="Ascension",
        description="Reach the final evolution stage",
        category=AchievementCategory.MILESTONE,
        rarity=AchievementRarity.LEGENDARY,
        requirement="Reach evolution stage 10",
        check_func=lambda ctx: ctx.get("evolution_stage", 0) >= 10,
        icon="angel",
    ),
]

# Coding Achievements
CODING_ACHIEVEMENTS: List[Achievement] = [
    Achievement(
        id="first_commit",
        name="Hello World",
        description="Make your first commit with your pet",
        category=AchievementCategory.CODING,
        rarity=AchievementRarity.COMMON,
        requirement="Make 1 commit while pet is active",
        check_func=lambda ctx: ctx.get("commits", 0) >= 1,
        icon="code",
    ),
    Achievement(
        id="git_master",
        name="Git Master",
        description="Show your pet some serious coding",
        category=AchievementCategory.CODING,
        rarity=AchievementRarity.RARE,
        requirement="Make 100 commits",
        check_func=lambda ctx: ctx.get("commits", 0) >= 100,
        icon="git_branch",
    ),
    Achievement(
        id="code_ninja",
        name="Code Ninja",
        description="Code through the night",
        category=AchievementCategory.CODING,
        rarity=AchievementRarity.EPIC,
        requirement="Code for 8 hours in a single session",
        check_func=lambda ctx: ctx.get("longest_session_minutes", 0) >= 480,
        icon="ninja",
    ),
    Achievement(
        id="bug_hunter",
        name="Bug Hunter",
        description="Fix 50 bugs with your pet",
        category=AchievementCategory.CODING,
        rarity=AchievementRarity.RARE,
        requirement="Fix 50 bugs",
        check_func=lambda ctx: ctx.get("bugs_fixed", 0) >= 50,
        icon="bug",
    ),
    Achievement(
        id="polyglot",
        name="Polyglot",
        description="Code in 5 different languages",
        category=AchievementCategory.CODING,
        rarity=AchievementRarity.EPIC,
        requirement="Use 5 different programming languages",
        check_func=lambda ctx: len(ctx.get("languages_used", [])) >= 5,
        icon="language",
    ),
    Achievement(
        id="perfect_day",
        name="Perfect Day",
        description="Maintain all stats at 100% for a full day",
        category=AchievementCategory.CODING,
        rarity=AchievementRarity.LEGENDARY,
        requirement="All stats at 100% for 24 hours",
        check_func=lambda ctx: ctx.get("perfect_days", 0) >= 1,
        icon="sun",
    ),
]

# Social Achievements
SOCIAL_ACHIEVEMENTS: List[Achievement] = [
    Achievement(
        id="friendly",
        name="Friendly",
        description="Interact with your pet 100 times",
        category=AchievementCategory.SOCIAL,
        rarity=AchievementRarity.COMMON,
        requirement="100 interactions",
        check_func=lambda ctx: ctx.get("interactions", 0) >= 100,
        icon="heart",
    ),
    Achievement(
        id="best_friend",
        name="Best Friend",
        description="Interact with your pet 1000 times",
        category=AchievementCategory.SOCIAL,
        rarity=AchievementRarity.RARE,
        requirement="1000 interactions",
        check_func=lambda ctx: ctx.get("interactions", 0) >= 1000,
        icon="heart_2",
    ),
    Achievement(
        id="pet_mentor",
        name="Pet Mentor",
        description="Help another player with their pet",
        category=AchievementCategory.SOCIAL,
        rarity=AchievementRarity.EPIC,
        requirement="Share pet knowledge with community",
        icon="mentor",
    ),
    Achievement(
        id="collector",
        name="Collector",
        description="Unlock 50% of all achievements",
        category=AchievementCategory.SOCIAL,
        rarity=AchievementRarity.EPIC,
        requirement="Unlock half of all achievements",
        check_func=lambda ctx: ctx.get("achievement_count", 0) >= ctx.get("total_achievements", 1) * 0.5,
        icon="trophy",
    ),
    Achievement(
        id="completionist",
        name="Completionist",
        description="Unlock all achievements",
        category=AchievementCategory.SOCIAL,
        rarity=AchievementRarity.MYTHIC,
        requirement="Unlock 100% of achievements",
        check_func=lambda ctx: ctx.get("achievement_count", 0) >= ctx.get("total_achievements", 999),
        icon="trophy_gold",
    ),
]

# Time Achievements
TIME_ACHIEVEMENTS: List[Achievement] = [
    Achievement(
        id="early_bird_2",
        name="Early Bird",
        description="Care for your pet before 8 AM",
        category=AchievementCategory.TIME,
        rarity=AchievementRarity.COMMON,
        requirement="Interact before 8 AM",
        icon="sunrise",
    ),
    Achievement(
        id="night_guardian",
        name="Night Guardian",
        description="Care for your pet after midnight",
        category=AchievementCategory.TIME,
        rarity=AchievementRarity.COMMON,
        requirement="Interact after midnight",
        icon="moon",
    ),
    Achievement(
        id="all_dayer",
        name="All-Dayer",
        description="Interact with your pet at 6 different times of day",
        category=AchievementCategory.TIME,
        rarity=AchievementRarity.RARE,
        requirement="Interact during morning, afternoon, evening, night, late night, and early morning",
        check_func=lambda ctx: len(ctx.get("time_periods_visited", [])) >= 6,
        icon="clock",
    ),
    Achievement(
        id="week_warrior",
        name="Week Warrior",
        description="Care for your pet 7 days in a row",
        category=AchievementCategory.TIME,
        rarity=AchievementRarity.RARE,
        requirement="7 day streak",
        check_func=lambda ctx: ctx.get("day_streak", 0) >= 7,
        icon="calendar",
    ),
    Achievement(
        id="monthly_master",
        name="Monthly Master",
        description="Care for your pet 30 days in a row",
        category=AchievementCategory.TIME,
        rarity=AchievementRarity.EPIC,
        requirement="30 day streak",
        check_func=lambda ctx: ctx.get("day_streak", 0) >= 30,
        icon="calendar_gold",
    ),
    Achievement(
        id="century_club",
        name="Century Club",
        description="Have your pet for 100 days",
        category=AchievementCategory.TIME,
        rarity=AchievementRarity.EPIC,
        requirement="100 total days with pet",
        check_func=lambda ctx: ctx.get("total_days", 0) >= 100,
        icon="medal",
    ),
]

# Special Achievements
SPECIAL_ACHIEVEMENTS: List[Achievement] = [
    Achievement(
        id="perfect_care",
        name="Perfect Care",
        description="Keep all stats at 100% simultaneously",
        category=AchievementCategory.SPECIAL,
        rarity=AchievementRarity.EPIC,
        requirement="Hunger, Happiness, and Energy all at 100%",
        check_func=lambda ctx: (
            ctx.get("hunger", 0) >= 100 and
            ctx.get("happiness", 0) >= 100 and
            ctx.get("energy", 0) >= 100
        ),
        icon="diamond",
    ),
    Achievement(
        id="survivor",
        name="Survivor",
        description="Recover from near-death (all stats below 10%)",
        category=AchievementCategory.SPECIAL,
        rarity=AchievementRarity.RARE,
        requirement="Bring all stats from under 10% back to healthy",
        icon="phoenix",
    ),
    Achievement(
        id="speed_runner",
        name="Speed Runner",
        description="Reach level 10 in under 24 hours",
        category=AchievementCategory.SPECIAL,
        rarity=AchievementRarity.EPIC,
        requirement="Level 10 within 24 hours of hatching",
        icon="lightning",
    ),
    Achievement(
        id="minimalist",
        name="Minimalist",
        description="Reach level 25 with fewer than 50 interactions",
        category=AchievementCategory.SPECIAL,
        rarity=AchievementRarity.LEGENDARY,
        requirement="Level 25 with under 50 interactions",
        check_func=lambda ctx: ctx.get("level", 0) >= 25 and ctx.get("interactions", 999) < 50,
        icon="feather",
    ),
]

# Secret Achievements
SECRET_ACHIEVEMENTS: List[Achievement] = [
    Achievement(
        id="easter_egg",
        name="???",
        description="Shhh...",
        category=AchievementCategory.SECRET,
        rarity=AchievementRarity.MYTHIC,
        requirement="???",
        hidden=True,
        icon="question",
    ),
    Achievement(
        id="void_walker",
        name="???",
        description="Some things are better left undiscovered",
        category=AchievementCategory.SECRET,
        rarity=AchievementRarity.MYTHIC,
        requirement="???",
        hidden=True,
        icon="void",
    ),
    Achievement(
        id="glitch_hunter",
        name="???",
        description="You weren't supposed to find this",
        category=AchievementCategory.SECRET,
        rarity=AchievementRarity.MYTHIC,
        requirement="???",
        hidden=True,
        icon="glitch",
    ),
]


# ============================================================================
# Achievement Manager
# ============================================================================

@dataclass
class UnlockedAchievement:
    """Represents an unlocked achievement."""
    achievement_id: str
    unlocked_at: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "achievement_id": self.achievement_id,
            "unlocked_at": self.unlocked_at.isoformat(),
        }


class AchievementManager:
    """
    Manages achievement tracking and unlocking.
    """

    def __init__(self):
        self._achievements: Dict[str, Achievement] = {}
        self._unlocked: Dict[str, UnlockedAchievement] = {}
        self._register_all_achievements()

    def _register_all_achievements(self):
        """Register all achievement definitions."""
        for achievement_list in [
            MILESTONE_ACHIEVEMENTS,
            CODING_ACHIEVEMENTS,
            SOCIAL_ACHIEVEMENTS,
            TIME_ACHIEVEMENTS,
            SPECIAL_ACHIEVEMENTS,
            SECRET_ACHIEVEMENTS,
        ]:
            for achievement in achievement_list:
                self._achievements[achievement.id] = achievement

    def register(self, achievement: Achievement) -> None:
        """Register a custom achievement."""
        self._achievements[achievement.id] = achievement

    def get(self, achievement_id: str) -> Optional[Achievement]:
        """Get an achievement by ID."""
        return self._achievements.get(achievement_id)

    def get_all(self) -> List[Achievement]:
        """Get all registered achievements."""
        return list(self._achievements.values())

    def get_by_category(self, category: AchievementCategory) -> List[Achievement]:
        """Get all achievements in a category."""
        return [
            a for a in self._achievements.values()
            if a.category == category
        ]

    def get_by_rarity(self, rarity: AchievementRarity) -> List[Achievement]:
        """Get all achievements of a rarity."""
        return [
            a for a in self._achievements.values()
            if a.rarity == rarity
        ]

    def is_unlocked(self, achievement_id: str) -> bool:
        """Check if an achievement is unlocked."""
        return achievement_id in self._unlocked

    def unlock(self, achievement_id: str) -> Optional[Achievement]:
        """
        Unlock an achievement.

        Args:
            achievement_id: ID of achievement to unlock

        Returns:
            Achievement if newly unlocked, None if already unlocked or not found
        """
        if achievement_id in self._unlocked:
            return None

        achievement = self._achievements.get(achievement_id)
        if achievement is None:
            return None

        self._unlocked[achievement_id] = UnlockedAchievement(
            achievement_id=achievement_id,
            unlocked_at=datetime.now()
        )

        return achievement

    def check_and_unlock(self, context: Dict[str, Any]) -> List[Achievement]:
        """
        Check all achievements and unlock any that meet conditions.

        Args:
            context: Current state context

        Returns:
            List of newly unlocked achievements
        """
        newly_unlocked = []

        for achievement_id, achievement in self._achievements.items():
            if achievement_id not in self._unlocked:
                try:
                    if achievement.check(context):
                        unlocked = self.unlock(achievement_id)
                        if unlocked:
                            newly_unlocked.append(unlocked)
                except Exception:
                    pass

        return newly_unlocked

    def get_unlocked_count(self) -> int:
        """Get number of unlocked achievements."""
        return len(self._unlocked)

    def get_total_count(self) -> int:
        """Get total number of achievements."""
        return len(self._achievements)

    def get_completion_percentage(self) -> float:
        """Get achievement completion percentage."""
        total = self.get_total_count()
        if total == 0:
            return 0.0
        return (self.get_unlocked_count() / total) * 100

    def get_unlocked_achievements(self) -> List[UnlockedAchievement]:
        """Get all unlocked achievements."""
        return list(self._unlocked.values())

    def save_state(self) -> Dict:
        """Get serializable state."""
        return {
            "unlocked": [u.to_dict() for u in self._unlocked.values()],
        }

    def load_state(self, state: Dict) -> None:
        """Load state from dictionary."""
        unlocked_data = state.get("unlocked", [])
        self._unlocked.clear()
        for u_data in unlocked_data:
            self._unlocked[u_data["achievement_id"]] = UnlockedAchievement(
                achievement_id=u_data["achievement_id"],
                unlocked_at=datetime.fromisoformat(u_data["unlocked_at"])
            )


# Global achievement manager
_default_manager: Optional[AchievementManager] = None


def get_achievement_manager() -> AchievementManager:
    """Get the global achievement manager."""
    global _default_manager
    if _default_manager is None:
        _default_manager = AchievementManager()
    return _default_manager


__all__ = [
    # Enums
    "AchievementCategory",
    "AchievementRarity",
    # Classes
    "Achievement",
    "UnlockedAchievement",
    "AchievementManager",
    # Achievement lists
    "MILESTONE_ACHIEVEMENTS",
    "CODING_ACHIEVEMENTS",
    "SOCIAL_ACHIEVEMENTS",
    "TIME_ACHIEVEMENTS",
    "SPECIAL_ACHIEVEMENTS",
    "SECRET_ACHIEVEMENTS",
    # Functions
    "get_achievement_manager",
]
