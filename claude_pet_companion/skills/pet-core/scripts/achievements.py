"""
Achievements - Achievement tracking system

Tracks player achievements and rewards.
"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from datetime import datetime
import re
import operator


class AchievementCategory(Enum):
    """Categories of achievements."""
    MILESTONE = "milestone"      # Level/stat milestones
    CODING = "coding"            # Coding activities
    SOCIAL = "social"            # Interaction achievements
    TIME = "time"                # Time-based achievements
    SPECIAL = "special"          # Special/hidden achievements


@dataclass
class Achievement:
    """Represents a single achievement."""
    id: str
    name: str
    description: str
    category: AchievementCategory
    xp_reward: int
    condition: str  # Python expression to evaluate
    icon: str = "🏆"
    hidden: bool = False
    secret: bool = False


class AchievementSystem:
    """Manages achievements and their unlocking."""

    def __init__(self):
        """Initialize achievement system."""
        self.achievements: Dict[str, Achievement] = {}
        self.load_achievements()

    @classmethod
    def get_achievements_file(cls) -> Path:
        """Get the path to the achievements config file."""
        plugin_root = Path(__file__).parent.parent.parent.parent
        return plugin_root / 'data' / 'achievements.json'

    def load_achievements(self):
        """Load achievements from config file."""
        achi_file = self.get_achievements_file()

        if achi_file.exists():
            try:
                with open(achi_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for achi_id, achi_data in data.get("achievements", {}).items():
                        self.achievements[achi_id] = Achievement(
                            id=achi_id,
                            name=achi_data.get("name", ""),
                            description=achi_data.get("description", ""),
                            category=AchievementCategory(achi_data.get("category", "milestone")),
                            xp_reward=achi_data.get("xp_reward", 0),
                            condition=achi_data.get("condition", ""),
                            icon=achi_data.get("icon", "🏆"),
                            hidden=achi_data.get("hidden", False),
                            secret=achi_data.get("secret", False)
                        )
                return
            except (json.JSONDecodeError, IOError):
                pass

        # Use default achievements if file doesn't exist
        self._load_default_achievements()

    def _load_default_achievements(self):
        """Load default hardcoded achievements."""
        default_achievements = {
            # Milestone Achievements
            "first_blood": Achievement(
                id="first_blood",
                name="Hello World",
                description="Create your first file",
                category=AchievementCategory.MILESTONE,
                xp_reward=50,
                condition="files_created >= 1",
                icon="👋"
            ),
            "productive_day": Achievement(
                id="productive_day",
                name="Productive Day",
                description="Create 10 files in a single day",
                category=AchievementCategory.MILESTONE,
                xp_reward=100,
                condition="files_created >= 10",
                icon="📝"
            ),
            "century": Achievement(
                id="century",
                name="Century",
                description="Reach level 100",
                category=AchievementCategory.MILESTONE,
                xp_reward=1000,
                condition="level >= 100",
                icon="💯"
            ),

            # Coding Achievements
            "error_hunter": Achievement(
                id="error_hunter",
                name="Bug Squasher",
                description="Fix 100 errors",
                category=AchievementCategory.CODING,
                xp_reward=500,
                condition="errors_fixed >= 100",
                icon="🔨"
            ),
            "code_warrior": Achievement(
                id="code_warrior",
                name="Code Warrior",
                description="Fix 1000 errors",
                category=AchievementCategory.CODING,
                xp_reward=2000,
                condition="errors_fixed >= 1000",
                icon="⚔️"
            ),
            "speed_coder": Achievement(
                id="speed_coder",
                name="Speed Coder",
                description="Have 10 consecutive successful actions",
                category=AchievementCategory.CODING,
                xp_reward=150,
                condition="consecutive_successes >= 10",
                icon="⚡"
            ),
            "unstoppable": Achievement(
                id="unstoppable",
                name="Unstoppable",
                description="Have 20 consecutive successful actions",
                category=AchievementCategory.CODING,
                xp_reward=300,
                condition="consecutive_successes >= 20",
                icon="🚀"
            ),

            # Social Achievements
            "good_owner": Achievement(
                id="good_owner",
                name="Good Owner",
                description="Feed your pet 50 times",
                category=AchievementCategory.SOCIAL,
                xp_reward=200,
                condition="times_fed >= 50",
                icon="🍖"
            ),
            "best_friend": Achievement(
                id="best_friend",
                name="Best Friend",
                description="Play with your pet 100 times",
                category=AchievementCategory.SOCIAL,
                xp_reward=300,
                condition="times_played >= 100",
                icon="🎾"
            ),
            "happy_camper": Achievement(
                id="happy_camper",
                name="Happy Camper",
                description="Keep happiness above 90 for a whole day",
                category=AchievementCategory.SOCIAL,
                xp_reward=250,
                condition="happiness >= 90 and total_sessions >= 5",
                icon="😊"
            ),

            # Time Achievements
            "night_owl": Achievement(
                id="night_owl",
                name="Night Owl",
                description="Code past midnight",
                category=AchievementCategory.TIME,
                xp_reward=200,
                condition="session_count >= 1",  # Simplified
                icon="🦉"
            ),
            "early_bird": Achievement(
                id="early_bird",
                name="Early Bird",
                description="Have a coding session before 6 AM",
                category=AchievementCategory.TIME,
                xp_reward=200,
                condition="session_count >= 1",  # Simplified
                icon="🐦"
            ),
            "marathon_session": Achievement(
                id="marathon_session",
                name="Marathon Session",
                description="Complete 25 coding sessions",
                category=AchievementCategory.TIME,
                xp_reward=500,
                condition="total_sessions >= 25",
                icon="🏃"
            ),

            # Special Achievements
            "first_evolution": Achievement(
                id="first_evolution",
                name="Growing Up",
                description="Evolve your pet for the first time",
                category=AchievementCategory.SPECIAL,
                xp_reward=500,
                condition="evolution_stage >= 1",
                icon="🥚"
            ),
            "master_evolver": Achievement(
                id="master_evolver",
                name="Master Evolver",
                description="Reach Ancient stage",
                category=AchievementCategory.SPECIAL,
                xp_reward=2000,
                condition="evolution_stage >= 6",
                icon="🌟"
            ),
            "perfectionist": Achievement(
                id="perfectionist",
                name="Perfectionist",
                description="Reach level 50 with less than 10 errors fixed",
                category=AchievementCategory.SPECIAL,
                xp_reward=1000,
                condition="level >= 50 and errors_fixed < 10",
                icon="💎"
            )
        }

        self.achievements = default_achievements

    def check_achievement(self, achievement_id: str, state) -> bool:
        """Check if an achievement's condition is met."""
        if achievement_id not in self.achievements:
            return False

        achievement = self.achievements[achievement_id]

        try:
            # Create a safe evaluation context
            context = {
                "files_created": state.files_created,
                "files_modified": state.files_modified,
                "commands_run": state.commands_run,
                "errors_fixed": state.errors_fixed,
                "consecutive_successes": state.consecutive_successes,
                "consecutive_failures": state.consecutive_failures,
                "level": state.level,
                "total_sessions": state.total_sessions,
                "times_fed": state.times_fed,
                "times_played": state.times_played,
                "happiness": state.happiness,
                "evolution_stage": state.evolution_stage,
                "xp": state.xp,
                "total_xp": state.total_xp
            }

            return eval(achievement.condition, {"__builtins__": {}}, context)
        except Exception:
            return False

    def check_all_achievements(self, state) -> List[str]:
        """Check all achievements and return list of newly unlocked ones."""
        newly_unlocked = []

        for achievement_id in self.achievements:
            if achievement_id not in state.achievements:
                if self.check_achievement(achievement_id, state):
                    newly_unlocked.append(achievement_id)

        return newly_unlocked

    def unlock_achievement(self, state, achievement_id: str) -> Dict[str, Any]:
        """Unlock an achievement and grant rewards."""
        if achievement_id in state.achievements:
            return {
                "success": False,
                "message": "Achievement already unlocked"
            }

        if achievement_id not in self.achievements:
            return {
                "success": False,
                "message": "Achievement not found"
            }

        achievement = self.achievements[achievement_id]

        # Check condition
        if not self.check_achievement(achievement_id, state):
            return {
                "success": False,
                "message": "Achievement condition not met"
            }

        # Unlock achievement
        state.add_achievement(achievement_id)

        # Grant XP reward
        from xp_system import XPSystem
        xp_system = XPSystem()
        xp_result = xp_system.add_xp(state, achievement.xp_reward)

        return {
            "success": True,
            "achievement": {
                "id": achievement.id,
                "name": achievement.name,
                "description": achievement.description,
                "icon": achievement.icon,
                "xp_reward": achievement.xp_reward
            },
            "xp_gained": achievement.xp_reward,
            "message": f"🏆 Achievement Unlocked: {achievement.icon} {achievement.name}!"
        }

    def get_achievement(self, achievement_id: str) -> Optional[Achievement]:
        """Get an achievement by ID."""
        return self.achievements.get(achievement_id)

    def get_all_achievements(self) -> Dict[str, Achievement]:
        """Get all achievements."""
        return self.achievements

    def get_achievements_by_category(self, category: AchievementCategory) -> List[Achievement]:
        """Get all achievements in a category."""
        return [
            a for a in self.achievements.values()
            if a.category == category
        ]

    def get_unlocked_achievements(self, state) -> List[Achievement]:
        """Get list of unlocked achievements."""
        return [
            self.achievements[aid]
            for aid in state.achievements
            if aid in self.achievements
        ]

    def get_locked_achievements(self, state) -> List[Achievement]:
        """Get list of locked achievements."""
        return [
            a for a in self.achievements.values()
            if a.id not in state.achievements
        ]

    def get_completion_percentage(self, state) -> float:
        """Get achievement completion percentage."""
        total = len(self.achievements)
        unlocked = len(state.achievements)
        return (unlocked / total * 100) if total > 0 else 0


# Convenience functions
def check_and_unlock(state) -> List[Dict[str, Any]]:
    """Check all achievements and unlock any that are ready."""
    system = AchievementSystem()
    newly_unlocked = system.check_all_achievements(state)

    results = []
    for achievement_id in newly_unlocked:
        result = system.unlock_achievement(state, achievement_id)
        results.append(result)

    return results


def get_achievement_summary(state) -> str:
    """Get a text summary of achievements."""
    system = AchievementSystem()
    unlocked = system.get_unlocked_achievements(state)
    total = len(system.achievements)
    percentage = system.get_completion_percentage(state)

    return f"Achievements: {len(unlocked)}/{total} ({percentage:.1f}%)"


def get_recent_achievements(state, count: int = 5) -> List[str]:
    """Get most recently unlocked achievements."""
    return state.achievements[-count:]


if __name__ == "__main__":
    from pet_state import PetState

    # Test achievement system
    state = PetState()
    state.files_created = 1

    system = AchievementSystem()
    print("Testing Achievement System")
    print(f"Total achievements: {len(system.achievements)}")

    # Check first_blood achievement
    if system.check_achievement("first_blood", state):
        result = system.unlock_achievement(state, "first_blood")
        print(f"Unlocked: {result['message']}")

    print(f"\nAchievement summary: {get_achievement_summary(state)}")
