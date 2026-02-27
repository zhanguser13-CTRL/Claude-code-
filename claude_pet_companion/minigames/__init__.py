"""
Claude Code Pet Companion - Minigames System

This module provides:
- Catch game: Catch falling items
- Memory game: Match card pairs
- Game rewards and achievements
- High score tracking
"""
import random
import time
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime


# ============================================================================
# Game Types
# ============================================================================

class GameType(Enum):
    """Types of minigames."""
    CATCH = "catch"
    MEMORY = "memory"
    QUIZ = "quiz"
    PUZZLE = "puzzle"


class GameState(Enum):
    """States of a game."""
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
    WON = "won"
    LOST = "lost"
    QUIT = "quit"


# ============================================================================
# Reward Types
# ============================================================================

@dataclass
class GameReward:
    """Reward for completing a minigame."""
    xp: int = 0
    currency: int = 0
    items: List[str] = field(default_factory=list)
    happiness: int = 0
    achievements: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "xp": self.xp,
            "currency": self.currency,
            "items": self.items,
            "happiness": self.happiness,
            "achievements": self.achievements,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'GameReward':
        """Create from dictionary."""
        return cls(
            xp=data.get("xp", 0),
            currency=data.get("currency", 0),
            items=data.get("items", []),
            happiness=data.get("happiness", 0),
            achievements=data.get("achievements", []),
        )


# ============================================================================
# Catch Game
# ============================================================================

class CatchItemType(Enum):
    """Types of items in catch game."""
    TREAT = "treat"              # Good: +points
    TOY = "toy"                  # Good: +points
    STAR = "star"                # Bonus: ++points
    BOMB = "bomb"                # Bad: -life
    POOP = "poop"                # Bad: -points
    COIN = "coin"                # Bonus: +currency
    GEM = "gem"                  # Rare: +++points


@dataclass
class CatchItem:
    """An item in the catch game."""
    item_type: CatchItemType
    x: float
    y: float
    speed: float = 2.0
    points: int = 10
    caught: bool = False
    missed: bool = False

    def update(self, dt: float, max_y: float) -> bool:
        """
        Update item position.

        Args:
            dt: Time delta
            max_y: Maximum Y position (bottom of screen)

        Returns:
            True if item should be removed
        """
        self.y += self.speed * dt * 60

        if self.y >= max_y:
            self.missed = True
            return True

        return False

    def check_catch(self, catch_x: float, catch_y: float, catch_width: float = 50) -> bool:
        """
        Check if item is caught.

        Args:
            catch_x: X position of catcher
            catch_y: Y position of catcher
            catch_width: Width of catcher

        Returns:
            True if caught
        """
        if self.caught or self.missed:
            return False

        if (abs(self.x - catch_x) < catch_width and
            abs(self.y - catch_y) < 30):
            self.caught = True
            return True

        return False


@dataclass
class CatchGameResult:
    """Result of a catch game."""
    score: int
    items_caught: int
    items_missed: int
    lives_remaining: int
    reward: GameReward

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "score": self.score,
            "items_caught": self.items_caught,
            "items_missed": self.items_missed,
            "lives_remaining": self.lives_remaining,
            "reward": self.reward.to_dict(),
        }


class CatchGame:
    """
    Catch falling items game.

    The player moves a basket/character to catch falling items.
    Good items give points, bad items reduce lives.
    """

    def __init__(self, difficulty: float = 1.0):
        """
        Initialize catch game.

        Args:
            difficulty: Game difficulty multiplier (1.0 = normal)
        """
        self.difficulty = difficulty
        self.state = GameState.IDLE
        self.score = 0
        self.lives = 3
        self.items: List[CatchItem] = []
        self.player_x = 0.5  # 0-1 position across screen
        self.spawn_timer = 0.0
        self.spawn_interval = 1.0
        self.game_duration = 60.0  # seconds
        self.time_elapsed = 0.0
        self.width = 800
        self.height = 600

        # Item weights for random spawning
        self.item_weights = {
            CatchItemType.TREAT: 40,
            CatchItemType.TOY: 30,
            CatchItemType.STAR: 10,
            CatchItemType.BOMB: 10,
            CatchItemType.POOP: 5,
            CatchItemType.COIN: 4,
            CatchItemType.GEM: 1,
        }

    def start(self) -> None:
        """Start the game."""
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = 3
        self.items.clear()
        self.time_elapsed = 0.0
        self.spawn_timer = 0.0

    def update(self, dt: float) -> Optional[CatchGameResult]:
        """
        Update game state.

        Args:
            dt: Time delta in seconds

        Returns:
            Game result if game ended, None otherwise
        """
        if self.state != GameState.PLAYING:
            return None

        self.time_elapsed += dt

        # Check time limit
        if self.time_elapsed >= self.game_duration:
            return self.end_game(won=True)

        # Update spawn timer
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval / self.difficulty:
            self.spawn_timer = 0
            self._spawn_item()

        # Update items
        player_y = self.height - 50
        catch_width = self.width * 0.15

        for item in self.items[:]:
            # Check catch
            player_screen_x = self.player_x * self.width
            if item.check_catch(player_screen_x, player_y, catch_width):
                self._handle_catch(item)
                self.items.remove(item)
                continue

            # Update position
            if item.update(dt, self.height):
                if item.missed:
                    self._handle_miss(item)
                self.items.remove(item)

        # Check lives
        if self.lives <= 0:
            return self.end_game(won=False)

        return None

    def move_player(self, direction: str, dt: float = 0.016) -> None:
        """
        Move the player.

        Args:
            direction: "left" or "right"
            dt: Time delta
        """
        speed = 0.5 * dt * 60
        if direction == "left":
            self.player_x = max(0.1, self.player_x - speed)
        elif direction == "right":
            self.player_x = min(0.9, self.player_x + speed)

    def set_player_position(self, x: float) -> None:
        """Set player position (0-1)."""
        self.player_x = max(0.1, min(0.9, x))

    def _spawn_item(self) -> None:
        """Spawn a new item."""
        item_type = random.choices(
            list(self.item_weights.keys()),
            weights=list(self.item_weights.values())
        )[0]

        item = CatchItem(
            item_type=item_type,
            x=random.uniform(50, self.width - 50),
            y=-30,
            speed=random.uniform(1.5, 3.0) * self.difficulty,
        )

        # Set points based on type
        item.points = {
            CatchItemType.TREAT: 10,
            CatchItemType.TOY: 15,
            CatchItemType.STAR: 50,
            CatchItemType.BOMB: 0,
            CatchItemType.POOP: -20,
            CatchItemType.COIN: 25,
            CatchItemType.GEM: 100,
        }[item_type]

        self.items.append(item)

    def _handle_catch(self, item: CatchItem) -> None:
        """Handle catching an item."""
        self.score += max(0, item.points)

        if item.item_type == CatchItemType.BOMB:
            self.lives -= 1

    def _handle_miss(self, item: CatchItem) -> None:
        """Handle missing an item."""
        if item.item_type in (CatchItemType.TREAT, CatchItemType.TOY, CatchItemType.STAR):
            # Optional: penalty for missing good items
            pass

    def end_game(self, won: bool) -> CatchGameResult:
        """
        End the game and calculate rewards.

        Args:
            won: Whether the player won

        Returns:
            Game result with rewards
        """
        self.state = GameState.WON if won else GameState.LOST

        # Calculate rewards
        reward = GameReward(
            xp=self.score,
            currency=self.score // 10,
            happiness=min(100, self.score // 5),
        )

        # Achievement checks
        if self.score >= 500:
            reward.achievements.append("catch_master")
        if self.lives == 3:
            reward.achievements.append("perfect_catch")

        return CatchGameResult(
            score=self.score,
            items_caught=sum(1 for i in self.items if i.caught) + len([i for i in self.items if i.caught]),
            items_missed=sum(1 for i in self.items if i.missed),
            lives_remaining=self.lives,
            reward=reward,
        )


# ============================================================================
# Memory Game
# ============================================================================

@dataclass
class MemoryCard:
    """A card in the memory game."""
    id: int
    value: Any
    revealed: bool = False
    matched: bool = False

    def flip(self) -> None:
        """Flip the card."""
        if not self.matched:
            self.revealed = not self.revealed

    def reset(self) -> None:
        """Reset card to hidden state."""
        self.revealed = False
        self.matched = False


@dataclass
class MemoryGameResult:
    """Result of a memory game."""
    pairs_found: int
    total_pairs: int
    moves: int
    time_elapsed: float
    won: bool
    reward: GameReward

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "pairs_found": self.pairs_found,
            "total_pairs": self.total_pairs,
            "moves": self.moves,
            "time_elapsed": self.time_elapsed,
            "won": self.won,
            "reward": self.reward.to_dict(),
        }


class MemoryGame:
    """
    Memory card matching game.

    Players flip cards to find matching pairs.
    """

    def __init__(self, grid_size: int = 4):
        """
        Initialize memory game.

        Args:
            grid_size: Size of grid (4 = 4x4 = 16 cards)
        """
        self.grid_size = grid_size
        self.total_cards = grid_size * grid_size
        self.total_pairs = self.total_cards // 2

        self.state = GameState.IDLE
        self.cards: List[MemoryCard] = []
        self.flipped_cards: List[MemoryCard] = []
        self.pairs_found = 0
        self.moves = 0
        self.time_elapsed = 0.0
        self.match_delay = 0.5
        self.match_timer = 0.0
        self.waiting_for_match = False

        # Card symbols
        self.symbols = ["A", "B", "C", "D", "E", "F", "G", "H",
                       "I", "J", "K", "L", "M", "N", "O", "P",
                       "Q", "R", "S", "T", "U", "V", "W", "X"]

    def start(self) -> None:
        """Start the game."""
        self.state = GameState.PLAYING
        self._setup_cards()
        self.pairs_found = 0
        self.moves = 0
        self.time_elapsed = 0.0
        self.flipped_cards.clear()
        self.waiting_for_match = False

    def _setup_cards(self) -> None:
        """Set up and shuffle the cards."""
        # Create pairs
        pairs = []
        for i in range(self.total_pairs):
            symbol = self.symbols[i % len(self.symbols)]
            pairs.extend([symbol, symbol])

        # Shuffle
        random.shuffle(pairs)

        # Create cards
        self.cards = [
            MemoryCard(id=i, value=pairs[i])
            for i in range(self.total_cards)
        ]

    def update(self, dt: float) -> Optional[MemoryGameResult]:
        """
        Update game state.

        Args:
            dt: Time delta in seconds

        Returns:
            Game result if game ended, None otherwise
        """
        if self.state != GameState.PLAYING:
            return None

        self.time_elapsed += dt

        # Handle match delay
        if self.waiting_for_match:
            self.match_timer -= dt
            if self.match_timer <= 0:
                self._resolve_mismatch()

        # Check win condition
        if self.pairs_found >= self.total_pairs:
            return self.end_game(won=True)

        return None

    def flip_card(self, index: int) -> bool:
        """
        Flip a card at the given index.

        Args:
            index: Card index to flip

        Returns:
            True if card was flipped
        """
        if self.state != GameState.PLAYING:
            return False

        if self.waiting_for_match:
            return False

        if index < 0 or index >= len(self.cards):
            return False

        card = self.cards[index]

        if card.revealed or card.matched:
            return False

        card.flip()
        self.flipped_cards.append(card)

        if len(self.flipped_cards) == 2:
            self.moves += 1
            self._check_match()

        return True

    def _check_match(self) -> None:
        """Check if flipped cards match."""
        card1, card2 = self.flipped_cards

        if card1.value == card2.value:
            # Match found
            card1.matched = True
            card2.matched = True
            self.pairs_found += 1
            self.flipped_cards.clear()
        else:
            # No match - wait before flipping back
            self.waiting_for_match = True
            self.match_timer = self.match_delay

    def _resolve_mismatch(self) -> None:
        """Resolve a mismatch by flipping cards back."""
        for card in self.flipped_cards:
            card.flip()
        self.flipped_cards.clear()
        self.waiting_for_match = False

    def end_game(self, won: bool) -> MemoryGameResult:
        """
        End the game and calculate rewards.

        Args:
            won: Whether the player won

        Returns:
            Game result with rewards
        """
        self.state = GameState.WON if won else GameState.LOST

        # Calculate rewards
        base_xp = self.pairs_found * 50
        time_bonus = max(0, (300 - self.time_elapsed) * 2)
        moves_penalty = max(0, (self.moves - self.total_pairs) * 5)

        reward = GameReward(
            xp=int(base_xp + time_bonus - moves_penalty),
            currency=self.pairs_found * 10,
            happiness=min(100, 20 + self.pairs_found * 5),
        )

        # Achievement checks
        if self.moves <= self.total_pairs + 2:
            reward.achievements.append("memory_master")
        if self.time_elapsed < 60:
            reward.achievements.append("speed_matcher")

        return MemoryGameResult(
            pairs_found=self.pairs_found,
            total_pairs=self.total_pairs,
            moves=self.moves,
            time_elapsed=self.time_elapsed,
            won=won,
            reward=reward,
        )

    def get_card_at(self, row: int, col: int) -> Optional[MemoryCard]:
        """Get card at grid position."""
        index = row * self.grid_size + col
        if 0 <= index < len(self.cards):
            return self.cards[index]
        return None


# ============================================================================
# Minigame Manager
# ============================================================================

@dataclass
class GameStats:
    """Statistics for a minigame."""
    games_played: int = 0
    games_won: int = 0
    high_score: int = 0
    total_xp_earned: int = 0
    total_currency_earned: int = 0
    last_played: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "games_played": self.games_played,
            "games_won": self.games_won,
            "high_score": self.high_score,
            "total_xp_earned": self.total_xp_earned,
            "total_currency_earned": self.total_currency_earned,
            "last_played": self.last_played.isoformat() if self.last_played else None,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'GameStats':
        """Create from dictionary."""
        return cls(
            games_played=data.get("games_played", 0),
            games_won=data.get("games_won", 0),
            high_score=data.get("high_score", 0),
            total_xp_earned=data.get("total_xp_earned", 0),
            total_currency_earned=data.get("total_currency_earned", 0),
            last_played=datetime.fromisoformat(data["last_played"]) if data.get("last_played") else None,
        )


class MinigameManager:
    """
    Manager for all minigames.
    """

    def __init__(self):
        self._catch_game: Optional[CatchGame] = None
        self._memory_game: Optional[MemoryGame] = None
        self._stats: Dict[str, GameStats] = {
            GameType.CATCH.value: GameStats(),
            GameType.MEMORY.value: GameStats(),
        }
        self._active_game: Optional[GameType] = None

    def start_catch_game(self, difficulty: float = 1.0) -> CatchGame:
        """Start a new catch game."""
        self._catch_game = CatchGame(difficulty=difficulty)
        self._catch_game.start()
        self._active_game = GameType.CATCH
        return self._catch_game

    def start_memory_game(self, grid_size: int = 4) -> MemoryGame:
        """Start a new memory game."""
        self._memory_game = MemoryGame(grid_size=grid_size)
        self._memory_game.start()
        self._active_game = GameType.MEMORY
        return self._memory_game

    def get_active_game(self) -> Optional[Any]:
        """Get the currently active game."""
        if self._active_game == GameType.CATCH:
            return self._catch_game
        elif self._active_game == GameType.MEMORY:
            return self._memory_game
        return None

    def update_active_game(self, dt: float) -> Optional[Any]:
        """Update the active game and return result if ended."""
        game = self.get_active_game()
        if game:
            result = game.update(dt)
            if result is not None:
                self._record_game_result(self._active_game, result)
            return result
        return None

    def _record_game_result(self, game_type: GameType, result: Any) -> None:
        """Record game result in statistics."""
        stats = self._stats.get(game_type.value, GameStats())
        stats.games_played += 1
        stats.last_played = datetime.now()

        if hasattr(result, 'reward'):
            stats.total_xp_earned += result.reward.xp
            stats.total_currency_earned += result.reward.currency

        if hasattr(result, 'won'):
            if result.won:
                stats.games_won += 1

        if hasattr(result, 'score'):
            stats.high_score = max(stats.high_score, result.score)

        self._stats[game_type.value] = stats

    def get_stats(self, game_type: GameType) -> GameStats:
        """Get statistics for a game type."""
        return self._stats.get(game_type.value, GameStats())

    def get_all_stats(self) -> Dict[str, GameStats]:
        """Get all game statistics."""
        return self._stats.copy()

    def save_state(self) -> Dict:
        """Get serializable state."""
        return {
            "stats": {
                game_type: stats.to_dict()
                for game_type, stats in self._stats.items()
            },
        }

    def load_state(self, state: Dict) -> None:
        """Load state from dictionary."""
        stats_data = state.get("stats", {})
        for game_type, stats_dict in stats_data.items():
            self._stats[game_type] = GameStats.from_dict(stats_dict)


__all__ = [
    # Enums
    "GameType",
    "GameState",
    "CatchItemType",
    # Classes
    "GameReward",
    "CatchItem",
    "CatchGameResult",
    "CatchGame",
    "MemoryCard",
    "MemoryGameResult",
    "MemoryGame",
    "GameStats",
    "MinigameManager",
]
