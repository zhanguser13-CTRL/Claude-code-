"""
XPSystem - Experience points and leveling system

Handles XP calculation, leveling, and rewards.
"""
from typing import Dict, List, Optional
from enum import Enum


class ActivityType(Enum):
    """Types of activities that grant XP."""
    WRITE_FILE = "write_file"
    EDIT_FILE = "edit_file"
    BASH_SUCCESS = "bash_success"
    BASH_FAILURE = "bash_failure"
    SESSION_COMPLETE = "session_complete"
    FEED_PET = "feed_pet"
    PLAY_PET = "play_pet"
    ACHIEVEMENT = "achievement"
    ERROR_FIXED = "error_fixed"


class XPSystem:
    """Manages XP gains and leveling for the pet."""

    # Base XP amounts for different activities
    BASE_XP = {
        ActivityType.WRITE_FILE: 10,
        ActivityType.EDIT_FILE: 10,
        ActivityType.BASH_SUCCESS: 5,
        ActivityType.BASH_FAILURE: 0,
        ActivityType.SESSION_COMPLETE: 50,
        ActivityType.FEED_PET: 5,
        ActivityType.PLAY_PET: 15,
        ActivityType.ERROR_FIXED: 25,
    }

    # Streak multipliers for consecutive successes
    STREAK_MULTIPLIERS = {
        3: 1.25,   # 3 in a row = 25% bonus
        5: 1.5,    # 5 in a row = 50% bonus
        10: 2.0,   # 10 in a row = 100% bonus (double!)
        20: 3.0,   # 20 in a row = 200% bonus (triple!)
    }

    # Level up milestones
    MILESTONE_REWARDS = {
        5: {"message": "Your pet is growing stronger!", "bonus_xp": 50},
        10: {"message": "Evolution available! Your pet can evolve!", "evolution": True},
        20: {"message": "Your pet has become a Teen!", "evolution": True},
        30: {"message": "Your pet has reached adulthood!", "evolution": True},
        50: {"message": "Your pet is a wise Adult!", "evolution": True},
        75: {"message": "Your pet is an Elder!", "evolution": True},
        100: {"message": "LEGENDARY! Your pet has reached max level!", "evolution": True}
    }

    def __init__(self):
        """Initialize XP system."""
        self.xp_gains_today = 0
        self.daily_xp_limit = 1000

    def calculate_xp(self, activity: ActivityType, state=None) -> int:
        """Calculate XP for an activity including bonuses."""
        base_xp = self.BASE_XP.get(activity, 0)

        # Apply streak multiplier if state provided
        multiplier = 1.0
        if state and activity in [ActivityType.WRITE_FILE, ActivityType.EDIT_FILE,
                                   ActivityType.BASH_SUCCESS]:
            multiplier = self._get_streak_multiplier(state.consecutive_successes)

        final_xp = int(base_xp * multiplier)
        return final_xp

    def _get_streak_multiplier(self, consecutive_successes: int) -> float:
        """Get the streak multiplier based on consecutive successes."""
        multiplier = 1.0
        for streak_threshold, streak_multiplier in sorted(self.STREAK_MULTIPLIERS.items()):
            if consecutive_successes >= streak_threshold:
                multiplier = streak_multiplier
        return multiplier

    def add_xp(self, state, amount: int) -> Dict[str, any]:
        """Add XP to state and check for level up."""
        old_level = state.level
        leveled_up = state.add_xp(amount)

        result = {
            "xp_gained": amount,
            "total_xp": state.total_xp,
            "current_xp": state.xp,
            "xp_to_next_level": state.xp_to_next_level,
            "leveled_up": leveled_up,
            "old_level": old_level,
            "new_level": state.level,
            "messages": []
        }

        if leveled_up:
            result["messages"].append(f"🎉 Level Up! {state.name} is now Level {state.level}!")

            # Check for milestone rewards
            if state.level in self.MILESTONE_REWARDS:
                milestone = self.MILESTONE_REWARDS[state.level]
                result["messages"].append(f"🏆 {milestone['message']}")
                result["milestone"] = milestone

        return result

    def grant_activity_xp(self, state, activity: ActivityType) -> Dict[str, any]:
        """Grant XP for an activity and return the result."""
        xp_amount = self.calculate_xp(activity, state)
        return self.add_xp(state, xp_amount)

    def get_level_progress(self, state) -> Dict[str, any]:
        """Get level progress information."""
        return {
            "level": state.level,
            "current_xp": state.xp,
            "xp_to_next_level": state.xp_to_next_level,
            "total_xp": state.total_xp,
            "progress_percent": int((state.xp / state.xp_to_next_level) * 100)
        }

    def get_xp_bar(self, state, width: int = 20) -> str:
        """Get a visual XP bar."""
        filled = int((state.xp / state.xp_to_next_level) * width)
        empty = width - filled
        return f"[{'█' * filled}{' ' * empty}] {state.xp}/{state.xp_to_next_level}"

    def reset_daily_xp(self):
        """Reset daily XP counter."""
        self.xp_gains_today = 0


# Convenience functions
def grant_xp(state, activity: ActivityType) -> Dict[str, any]:
    """Grant XP for an activity."""
    system = XPSystem()
    return system.grant_activity_xp(state, activity)


def check_level_up(state) -> Optional[Dict[str, any]]:
    """Check and process level up if needed."""
    system = XPSystem()
    if state.xp >= state.xp_to_next_level:
        return system.add_xp(state, 0)  # This will trigger level up
    return None


def get_level_info(state) -> str:
    """Get formatted level information."""
    system = XPSystem()
    progress = system.get_level_progress(state)
    return f"Level {state.level} | {system.get_xp_bar(state)}"


# Activity-specific functions
def award_file_activity(state, is_new_file: bool = False) -> Dict[str, any]:
    """Award XP for file creation or editing."""
    activity = ActivityType.WRITE_FILE if is_new_file else ActivityType.EDIT_FILE
    return grant_xp(state, activity)


def award_command_activity(state, success: bool = True) -> Dict[str, any]:
    """Award XP for command execution."""
    activity = ActivityType.BASH_SUCCESS if success else ActivityType.BASH_FAILURE
    return grant_xp(state, activity)


def award_session_completion(state) -> Dict[str, any]:
    """Award XP for completing a session."""
    return grant_xp(state, ActivityType.SESSION_COMPLETE)


def award_error_fix(state) -> Dict[str, any]:
    """Award XP for fixing an error."""
    state.errors_fixed += 1
    return grant_xp(state, ActivityType.ERROR_FIXED)


if __name__ == "__main__":
    from pet_state import PetState

    # Test XP system
    state = PetState()
    xp_system = XPSystem()

    print("Testing XP System")
    print(f"Initial: Level {state.level}, XP: {state.xp}/{state.xp_to_next_level}")

    # Test file activity
    result = xp_system.grant_activity_xp(state, ActivityType.WRITE_FILE)
    print(f"After file write: +{result['xp_gained']} XP")

    # Test streak
    state.consecutive_successes = 10
    result = xp_system.grant_activity_xp(state, ActivityType.EDIT_FILE)
    print(f"With 10 streak: +{result['xp_gained']} XP")

    print(f"Progress: {xp_system.get_xp_bar(state)}")
