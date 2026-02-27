"""
Social Module for Claude Pet Companion

Provides:
- Friends system with online status and activities
- Arena/PVP battles with elemental type advantages
- Leaderboards for tracking rankings across categories
"""

from .friends import (
    Friend,
    FriendStatus,
    OnlineStatus,
    FriendRequest,
    SocialActivity,
    FriendsSystem,
)

from .arena import (
    ElementType,
    MoveCategory,
    Move,
    BattlePet,
    BattleAction,
    BattleResult,
    BattleArena,
    Battle,
    MoveLibrary,
    PresetPets,
)

from .leaderboard import (
    LeaderboardType,
    LeaderboardEntry,
    Leaderboard,
    PlayerScore,
    LeaderboardManager,
)

# Version info
__version__ = "2.3.4"

# Public API
__all__ = [
    # Friends module
    "Friend",
    "FriendStatus",
    "OnlineStatus",
    "FriendRequest",
    "SocialActivity",
    "FriendsSystem",
    # Arena module
    "ElementType",
    "MoveCategory",
    "Move",
    "BattlePet",
    "BattleAction",
    "BattleResult",
    "BattleArena",
    "Battle",
    "MoveLibrary",
    "PresetPets",
    # Leaderboard module
    "LeaderboardType",
    "LeaderboardEntry",
    "PlayerScore",
    "Leaderboard",
    "LeaderboardManager",
]

# Module-level convenience functions
def create_friends_system(user_id: str = "player") -> FriendsSystem:
    """Create a new friends system instance."""
    return FriendsSystem(user_id)


def create_arena() -> BattleArena:
    """Create a new battle arena."""
    return BattleArena()


def create_leaderboard_manager() -> LeaderboardManager:
    """Create a new leaderboard manager."""
    return LeaderboardManager()


# Default element types for convenience
DEFAULT_ELEMENTS = {
    "normal": ElementType.NORMAL,
    "fire": ElementType.FIRE,
    "water": ElementType.WATER,
    "grass": ElementType.GRASS,
    "electric": ElementType.ELECTRIC,
    "ice": ElementType.ICE,
    "fighting": ElementType.FIGHTING,
    "poison": ElementType.POISON,
    "ground": ElementType.GROUND,
    "flying": ElementType.FLYING,
    "psychic": ElementType.PSYCHIC,
    "bug": ElementType.BUG,
    "rock": ElementType.ROCK,
    "ghost": ElementType.GHOST,
    "dragon": ElementType.DRAGON,
    "dark": ElementType.DARK,
    "steel": ElementType.STEEL,
    "fairy": ElementType.FAIRY,
}
