"""
Leaderboard System for Claude Pet Companion

Tracks rankings across various categories:
- Level rankings
- Battle rankings
- Mini-game high scores
- Collection completion
- Social stats
"""

import random
import logging
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class LeaderboardType(Enum):
    """Types of leaderboards."""
    LEVEL = "level"              # Highest level
    BATTLE_WINS = "battle_wins"  # Most battle wins
    BATTLE_RATIO = "battle_ratio"  # Best win/loss ratio
    COLLECTION = "collection"    # Most cards collected
    RHYTHM_SCORE = "rhythm"     # Rhythm game high score
    RACING_WINS = "racing"      # Most race wins
    PLAYTIME = "playtime"        # Total time played
    ACHIEVEMENTS = "achievements" # Most achievements unlocked


@dataclass
class LeaderboardEntry:
    """An entry on the leaderboard."""
    user_id: str
    username: str
    score: int  # The value being ranked
    secondary_score: int = 0  # Tiebreaker
    pet_name: str = ""
    pet_emoji: str = "🐾"
    last_updated: float = field(default_factory=time.time)

    def __lt__(self, other: 'LeaderboardEntry'):
        """Compare entries for sorting."""
        if self.score != other.score:
            return self.score < other.score
        return self.secondary_score < other.secondary_score

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'score': self.score,
            'secondary_score': self.secondary_score,
            'pet_name': self.pet_name,
            'pet_emoji': self.pet_emoji,
            'last_updated': self.last_updated,
        }


@dataclass
class PlayerScore:
    """A player's score for a leaderboard."""
    user_id: str
    username: str
    pet_name: str = ""
    pet_emoji: str = "🐾"

    # Scores by type
    level: int = 1
    battle_wins: int = 0
    battle_losses: int = 0
    cards_collected: int = 0
    rhythm_high_score: int = 0
    racing_wins: int = 0
    total_playtime: int = 0  # minutes
    achievements_unlocked: int = 0

    def get_score(self, board_type: LeaderboardType) -> int:
        """Get score for a specific leaderboard."""
        scores = {
            LeaderboardType.LEVEL: self.level,
            LeaderboardType.BATTLE_WINS: self.battle_wins,
            LeaderboardType.BATTLE_RATIO: self.battle_wins * 100 - self.battle_losses,
            LeaderboardType.COLLECTION: self.cards_collected,
            LeaderboardType.RHYTHM_SCORE: self.rhythm_high_score,
            LeaderboardType.RACING_WINS: self.racing_wins,
            LeaderboardType.PLAYTIME: self.total_playtime,
            LeaderboardType.ACHIEVEMENTS: self.achievements_unlocked,
        }
        return scores.get(board_type, 0)

    def get_secondary_score(self, board_type: LeaderboardType) -> int:
        """Get secondary score for tiebreaking."""
        if board_type == LeaderboardType.BATTLE_RATIO:
            return self.battle_wins  # More wins is better even with same ratio
        return 0

    def update_score(self, board_type: LeaderboardType, score: int):
        """Update a specific score."""
        if board_type == LeaderboardType.LEVEL:
            self.level = score
        elif board_type == LeaderboardType.BATTLE_WINS:
            self.battle_wins = score
        elif board_type == LeaderboardType.BATTLE_RATIO:
            # Externally managed
            pass
        elif board_type == LeaderboardType.COLLECTION:
            self.cards_collected = score
        elif board_type == LeaderboardType.RHYTHM_SCORE:
            self.rhythm_high_score = max(self.rhythm_high_score, score)
        elif board_type == LeaderboardType.RACING_WINS:
            self.racing_wins = score
        elif board_type == LeaderboardType.PLAYTIME:
            self.total_playtime = score
        elif board_type == LeaderboardType.ACHIEVEMENTS:
            self.achievements_unlocked = score

    def add_battle_result(self, won: bool):
        """Record a battle result."""
        if won:
            self.battle_wins += 1
        else:
            self.battle_losses += 1

    def add_playtime(self, minutes: int):
        """Add playtime."""
        self.total_playtime += minutes


class Leaderboard:
    """A single leaderboard."""

    def __init__(self, board_type: LeaderboardType, name: str = "",
                 max_entries: int = 100, refresh_interval: int = 60):
        self.board_type = board_type
        self.name = name or f"{board_type.value.title()} Rankings"
        self.max_entries = max_entries
        self.refresh_interval = refresh_interval  # minutes
        self.last_refresh = time.time()
        self.entries: List[LeaderboardEntry] = []
        self.player_scores: Dict[str, PlayerScore] = {}

    def update_player_score(self, user_id: str, username: str,
                            score: int, secondary_score: int = 0,
                            pet_name: str = "", pet_emoji: str = "🐾"):
        """Update a player's score on this leaderboard."""
        # Update player score
        if user_id not in self.player_scores:
            self.player_scores[user_id] = PlayerScore(
                user_id=user_id,
                username=username,
                pet_name=pet_name,
                pet_emoji=pet_emoji
            )

        player = self.player_scores[user_id]
        player.username = username  # Update in case it changed
        player.pet_name = pet_name
        player.pet_emoji = pet_emoji

        # Update specific score
        if self.board_type == LeaderboardType.BATTLE_RATIO:
            player.add_battle_result(score > 0)
            actual_score = player.get_score(self.board_type)
            actual_secondary = player.battle_wins
        else:
            player.update_score(self.board_type, score)
            actual_score = player.get_score(self.board_type)
            actual_secondary = secondary_score

        # Update or add entry
        entry = None
        for e in self.entries:
            if e.user_id == user_id:
                entry = e
                break

        if entry:
            entry.score = actual_score
            entry.secondary_score = actual_secondary
            entry.username = username
            entry.pet_name = pet_name
            entry.pet_emoji = pet_emoji
            entry.last_updated = time.time()
        else:
            entry = LeaderboardEntry(
                user_id=user_id,
                username=username,
                score=actual_score,
                secondary_score=actual_secondary,
                pet_name=pet_name,
                pet_emoji=pet_emoji
            )
            self.entries.append(entry)

        # Sort and trim
        self.entries.sort(reverse=True)
        self.entries = self.entries[:self.max_entries]

        self.last_refresh = time.time()

    def get_rank(self, user_id: str) -> Optional[int]:
        """Get a user's rank on this leaderboard."""
        for i, entry in enumerate(self.entries):
            if entry.user_id == user_id:
                return i + 1
        return None

    def get_top_entries(self, limit: int = 10) -> List[LeaderboardEntry]:
        """Get top entries."""
        return self.entries[:limit]

    def get_entries_around(self, user_id: str, count: int = 5
                          ) -> Tuple[List[LeaderboardEntry], List[LeaderboardEntry]]:
        """Get entries around a user's rank."""
        user_rank = self.get_rank(user_id)

        if user_rank is None:
            return ([], self.get_top_entries(count))

        start = max(0, user_rank - count - 1)
        end = min(len(self.entries), user_rank + count)

        above = self.entries[start:user_rank - 1]
        below = self.entries[user_rank:end]

        return (above, below)

    def is_valid(self) -> bool:
        """Check if leaderboard needs refresh."""
        return time.time() - self.last_refresh < self.refresh_interval * 60

    def refresh(self):
        """Mark leaderboard as refreshed."""
        self.last_refresh = time.time()

    def get_summary(self) -> Dict:
        """Get leaderboard summary."""
        if not self.entries:
            return {
                'name': self.name,
                'type': self.board_type.value,
                'total_players': 0,
                'top_score': 0,
            }

        return {
            'name': self.name,
            'type': self.board_type.value,
            'total_players': len(self.entries),
            'top_score': self.entries[0].score,
            'top_player': self.entries[0].username,
        }


class LeaderboardManager:
    """Manages multiple leaderboards."""

    def __init__(self):
        self.boards: Dict[str, Leaderboard] = {}
        self.player_scores: Dict[str, PlayerScore] = {}  # Shared scores

        # Create default boards
        self._create_default_boards()

    def _create_default_boards(self):
        """Create default leaderboards."""
        board_types = [
            (LeaderboardType.LEVEL, "Level Rankings"),
            (LeaderboardType.BATTLE_WINS, "Battle Victories"),
            (LeaderboardType.BATTLE_RATIO, "Battle Win Rate"),
            (LeaderboardType.COLLECTION, "Collection"),
            (LeaderboardType.RHYTHM_SCORE, "Rhythm High Scores"),
            (LeaderboardType.RACING_WINS, "Racing Victories"),
            (LeaderboardType.PLAYTIME, "Total Playtime"),
            (LeaderboardType.ACHIEVEMENTS, "Achievements Unlocked"),
        ]

        for board_type, name in board_types:
            self.boards[board_type.value] = Leaderboard(board_type, name)

    def get_board(self, board_type: LeaderboardType) -> Optional[Leaderboard]:
        """Get a leaderboard by type."""
        return self.boards.get(board_type.value)

    def get_board_by_name(self, name: str) -> Optional[Leaderboard]:
        """Get a leaderboard by name."""
        for board in self.boards.values():
            if board.name == name:
                return board
        return None

    def update_score(self, user_id: str, username: str,
                    board_type: LeaderboardType, score: int,
                    secondary_score: int = 0,
                    pet_name: str = "", pet_emoji: str = "🐾"):
        """Update a player's score on a leaderboard."""
        board = self.get_board(board_type)
        if board:
            board.update_player_score(
                user_id, username, score, secondary_score,
                pet_name, pet_emoji
            )

    def get_global_rank(self, user_id: str, board_type: LeaderboardType) -> Optional[int]:
        """Get a user's global rank across a board type."""
        board = self.get_board(board_type)
        if board:
            return board.get_rank(user_id)
        return None

    def get_all_summaries(self) -> List[Dict]:
        """Get summaries for all leaderboards."""
        return [board.get_summary() for board in self.boards.values()]

    def register_player(self, user_id: str, username: str,
                       pet_name: str = "", pet_emoji: str = "🐾"):
        """Register a player in the system."""
        if user_id not in self.player_scores:
            self.player_scores[user_id] = PlayerScore(
                user_id=user_id,
                username=username,
                pet_name=pet_name,
                pet_emoji=pet_emoji
            )

    def get_player_scores(self, user_id: str) -> Optional[PlayerScore]:
        """Get all scores for a player."""
        return self.player_scores.get(user_id)

    def simulate_players(self, count: int = 50):
        """Add simulated players for testing."""
        names = [
            "PetLover", "CatFan", "DogMaster", "Whiskers", "Buddy",
            "Sparky", "Fluffy", "Shadow", "Luna", "Max",
            "Bella", "Charlie", "Rocky", "Coco", "Daisy",
            "Duke", "Elvis", "Felix", "Ginger", "Hunter",
        ]

        elements = ["🐱", "🐕", "🐰", "🐹", "🐻", "🐼", "🐨", "🐯"]

        for i in range(count):
            user_id = f"bot_{i}"
            username = f"{random.choice(names)}{random.randint(1, 999)}"
            pet_name = f"{random.choice(names)} Jr."
            pet_emoji = random.choice(elements)

            # Generate scores
            level = random.randint(1, 100)
            battle_wins = random.randint(0, 500)
            battle_losses = random.randint(0, battle_wins)
            cards_collected = random.randint(10, 500)
            rhythm_score = random.randint(100, 10000)
            racing_wins = random.randint(0, 100)
            playtime = random.randint(60, 10000)
            achievements = random.randint(0, 37)

            # Update each board
            self.register_player(user_id, username, pet_name, pet_emoji)
            self.update_score(user_id, username, LeaderboardType.LEVEL, level, pet_name=pet_name, pet_emoji=pet_emoji)
            self.update_score(user_id, username, LeaderboardType.BATTLE_WINS, battle_wins, pet_name=pet_name, pet_emoji=pet_emoji)
            self.update_score(user_id, username, LeaderboardType.COLLECTION, cards_collected, pet_name=pet_name, pet_emoji=pet_emoji)
            self.update_score(user_id, username, LeaderboardType.RHYTHM_SCORE, rhythm_score, pet_name=pet_name, pet_emoji=pet_emoji)
            self.update_score(user_id, username, LeaderboardType.RACING_WINS, racing_wins, pet_name=pet_name, pet_emoji=pet_emoji)
            self.update_score(user_id, username, LeaderboardType.PLAYTIME, playtime, pet_name=pet_name, pet_emoji=pet_emoji)
            self.update_score(user_id, username, LeaderboardType.ACHIEVEMENTS, achievements, pet_name=pet_name, pet_emoji=pet_emoji)

            # Update ratio
            player = self.player_scores[user_id]
            player.add_battle_result(random.choice([True, False]))
            self.update_score(user_id, username, LeaderboardType.BATTLE_RATIO, 0, player.battle_wins, pet_name=pet_name, pet_emoji=pet_emoji)


if __name__ == "__main__":
    # Test leaderboard system
    print("Testing Leaderboard System")

    manager = LeaderboardManager()

    # Add simulated players
    manager.simulate_players(20)

    # Register a test player
    manager.register_player("test_user", "TestPlayer", "Buddy", "🐕")

    # Update some scores
    manager.update_score("test_user", "TestPlayer", LeaderboardType.LEVEL, 25)
    manager.update_score("test_user", "TestPlayer", LeaderboardType.BATTLE_WINS, 15)

    # Get summaries
    print("\nLeaderboard Summaries:")
    for summary in manager.get_all_summaries()[:3]:
        print(f"\n{summary['name']}:")
        print(f"  Top: {summary.get('top_player', 'N/A')} with {summary.get('top_score', 0)}")

    # Get rank
    rank = manager.get_global_rank("test_user", LeaderboardType.LEVEL)
    print(f"\nTest Player Level Rank: {rank}")

    # Get top entries
    level_board = manager.get_board(LeaderboardType.LEVEL)
    print(f"\nTop 5 Level Rankings:")
    for entry in level_board.get_top_entries(5):
        print(f"  {entry.rank if hasattr(entry, 'rank') else '?'} {entry.username}: {entry.score} - {entry.pet_name}")

    print("\nLeaderboard system test passed!")
