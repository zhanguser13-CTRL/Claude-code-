"""
Rock Paper Scissors Minigame

A classic game with strategy AI opponent (the pet).
Features:
- Pattern recognition AI
- Randomness with bias
- Win streaks and combos
- Pet reactions based on outcome
"""

import random
import logging
from typing import Dict, List, Tuple, Optional, Literal
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RPSMove(Enum):
    """Possible moves in Rock Paper Scissors."""
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"

    def __str__(self):
        return self.value

    @classmethod
    def random(cls) -> 'RPSMove':
        """Get a random move."""
        return random.choice(list(cls))

    def emoji(self) -> str:
        """Get emoji representation."""
        return {
            RPSMove.ROCK: "🪨",
            RPSMove.PAPER: "📄",
            RPSMove.SCISSORS: "✂️"
        }[self]

    def beats(self, other: 'RPSMove') -> bool:
        """Check if this move beats the other."""
        return (
            (self == RPSMove.ROCK and other == RPSMove.SCISSORS) or
            (self == RPSMove.PAPER and other == RPSMove.ROCK) or
            (self == RPSMove.SCISSORS and other == RPSMove.PAPER)
        )

    def ties_with(self, other: 'RPSMove') -> bool:
        """Check if this move ties with the other."""
        return self == other


class GameOutcome(Enum):
    """Possible game outcomes."""
    WIN = "win"
    LOSE = "lose"
    TIE = "tie"


class PetReaction(Enum):
    """Pet reactions to game outcomes."""
    WIN_HAPPY = "win_happy"
    WIN_CHEER = "win_cheer"
    WIN_DANCE = "win_dance"
    LOSE_SAD = "lose_sad"
    LOSE_POUT = "lose_pout"
    LOSE_CRY = "lose_cry"
    TIE_THINK = "tie_think"
    TIE_NEUTRAL = "tie_neutral"


@dataclass
class RoundResult:
    """Result of a single round."""
    player_move: RPSMove
    pet_move: RPSMove
    outcome: GameOutcome
    timestamp: float = field(default_factory=lambda: 0)  # Placeholder

    def __str__(self):
        return f"{self.player_move.emoji()} vs {self.pet_move.emoji()} = {self.outcome.value}"


@dataclass
class GameStats:
    """Statistics for a game session."""
    rounds_played: int = 0
    player_wins: int = 0
    pet_wins: int = 0
    ties: int = 0
    current_streak: int = 0  # Positive for player, negative for pet
    best_streak: int = 0
    player_move_history: List[RPSMove] = field(default_factory=list)
    pet_move_history: List[RPSMove] = field(default_factory=list)
    outcome_history: List[GameOutcome] = field(default_factory=list)

    def get_win_rate(self) -> float:
        """Get player win rate (0-1)."""
        if self.rounds_played == 0:
            return 0.0
        return self.player_wins / self.rounds_played

    def get_most_common_player_move(self) -> Optional[RPSMove]:
        """Get the player's most common move."""
        if not self.player_move_history:
            return None
        from collections import Counter
        counter = Counter(self.player_move_history)
        return counter.most_common(1)[0][0]


class AIStrategy(Enum):
    """AI difficulty levels."""
    RANDOM = "random"           # Pure random
    PATTERN = "pattern"         # Detects player patterns
    PSYCHOLOGICAL = "psych"     # Uses psychological tricks
    ADAPTIVE = "adaptive"       # Adapts to player behavior
    EXPERT = "expert"           # Advanced strategy


class PatternAnalyzer:
    """Analyzes player move patterns."""

    def __init__(self, history_length: int = 10):
        self.history_length = history_length

    def predict_next_move(self, history: List[RPSMove]) -> Optional[RPSMove]:
        """Predict player's next move based on history."""
        if len(history) < 3:
            return None

        recent = history[-self.history_length:]

        # Check for simple repetition pattern
        if len(recent) >= 3:
            if recent[-1] == recent[-2] == recent[-3]:
                # Player tends to repeat - predict same move
                return recent[-1]

        # Check for alternating pattern
        if len(recent) >= 4:
            if (recent[-1] != recent[-2] and
                recent[-2] != recent[-3] and
                recent[-3] != recent[-4]):
                # Alternating pattern
                return recent[-1]

        # Check for response pattern (what they play after each move)
        response_patterns = {}
        for i in range(len(recent) - 1):
            current = recent[i]
            next_move = recent[i + 1]
            if current not in response_patterns:
                response_patterns[current] = {}
            if next_move not in response_patterns[current]:
                response_patterns[current][next_move] = 0
            response_patterns[current][next_move] += 1

        if recent and recent[-1] in response_patterns:
            patterns = response_patterns[recent[-1]]
            if patterns:
                # Return most likely response
                return max(patterns.items(), key=lambda x: x[1])[0]

        return None

    def get_counter_move(self, predicted_move: RPSMove) -> RPSMove:
        """Get the move that beats the predicted move."""
        counters = {
            RPSMove.ROCK: RPSMove.PAPER,
            RPSMove.PAPER: RPSMove.SCISSORS,
            RPSMove.SCISSORS: RPSMove.ROCK
        }
        return counters.get(predicted_move, RPSMove.random())


class RockPaperScissorsGame:
    """Main Rock Paper Scissors game class."""

    def __init__(self, ai_strategy: AIStrategy = AIStrategy.PATTERN):
        self.ai_strategy = ai_strategy
        self.stats = GameStats()
        self.analyzer = PatternAnalyzer()

        # AI state
        self.ai_confidence = 0.5  # How confident the AI is in its predictions
        self.lose_intentionally = 0.0  # Chance to let player win

    def play_round(self, player_move: RPSMove) -> RoundResult:
        """
        Play a single round.

        Args:
            player_move: The player's move

        Returns:
            RoundResult with outcome
        """
        # Record player move
        self.stats.player_move_history.append(player_move)

        # Determine AI move
        pet_move = self._get_ai_move()

        # Determine outcome
        if player_move.beats(pet_move):
            outcome = GameOutcome.WIN
            self.stats.player_wins += 1
            self.stats.current_streak = max(1, self.stats.current_streak + 1)
        elif pet_move.beats(player_move):
            outcome = GameOutcome.LOSE
            self.stats.pet_wins += 1
            self.stats.current_streak = min(-1, self.stats.current_streak - 1)
        else:
            outcome = GameOutcome.TIE
            self.stats.ties += 1

        # Update stats
        self.stats.rounds_played += 1
        self.stats.best_streak = max(self.stats.best_streak, abs(self.stats.current_streak))
        self.stats.pet_move_history.append(pet_move)
        self.stats.outcome_history.append(outcome)

        # Update AI confidence
        self._update_ai_confidence(outcome)

        return RoundResult(player_move, pet_move, outcome)

    def _get_ai_move(self) -> RPSMove:
        """Determine AI's move based on strategy."""
        if self.ai_strategy == AIStrategy.RANDOM:
            return RPSMove.random()

        elif self.ai_strategy == AIStrategy.PATTERN:
            return self._pattern_strategy_move()

        elif self.ai_strategy == AIStrategy.PSYCHOLOGICAL:
            return self._psychological_strategy_move()

        elif self.ai_strategy == AIStrategy.ADAPTIVE:
            return self._adaptive_strategy_move()

        elif self.ai_strategy == AIStrategy.EXPERT:
            return self._expert_strategy_move()

        return RPSMove.random()

    def _pattern_strategy_move(self) -> RPSMove:
        """Pattern-based AI."""
        # Try to predict player's move
        predicted = self.analyzer.predict_next_move(self.stats.player_move_history)

        if predicted and random.random() < self.ai_confidence:
            # Counter the predicted move
            return self.analyzer.get_counter_move(predicted)

        # Maybe lose intentionally if player is losing too much
        if self.stats.current_streak <= -3:
            if random.random() < 0.5:
                return self._get_losing_move()

        return RPSMove.random()

    def _psychological_strategy_move(self) -> RPSMove:
        """Psychological strategy - plays mind games."""
        history = self.stats.player_move_history

        if not history:
            return RPSMove.PAPER  # Start with paper (beats most common rock)

        # Many players play rock after winning with rock
        if len(history) >= 2:
            last_outcome = self.stats.outcome_history[-1]
            if last_outcome == GameOutcome.WIN:
                # If player won, they might repeat their move
                # Play to beat their last move
                return self.analyzer.get_counter_move(history[-1])

        # After a tie, players often switch
        if len(history) >= 2:
            last_outcome = self.stats.outcome_history[-1]
            if last_outcome == GameOutcome.TIE:
                # They'll likely switch to beat what they just played
                # So play to beat that
                last_move = history[-1]
                if last_move == RPSMove.ROCK:
                    return RPSMove.SCISSORS  # They might play paper
                elif last_move == RPSMove.PAPER:
                    return RPSMove.ROCK  # They might play scissors
                else:  # scissors
                    return RPSMove.PAPER  # They might play rock

        return RPSMove.random()

    def _adaptive_strategy_move(self) -> RPSMove:
        """Adaptive strategy that changes based on player behavior."""
        # Get player's most common move
        most_common = self.stats.get_most_common_player_move()

        if most_common:
            # Counter their most common move
            counter = self.analyzer.get_counter_move(most_common)

            # Add some randomness
            if random.random() < 0.7:
                return counter

        return RPSMove.random()

    def _expert_strategy_move(self) -> RPSMove:
        """Expert strategy using multiple techniques."""
        # Try pattern prediction first
        predicted = self.analyzer.predict_next_move(self.stats.player_move_history)

        if predicted and self.ai_confidence > 0.6:
            return self.analyzer.get_counter_move(predicted)

        # Use Markov chain prediction
        markov_move = self._markov_predict()
        if markov_move:
            return self.analyzer.get_counter_move(markov_move)

        # Fall back to psychological
        return self._psychological_strategy_move()

    def _markov_predict(self) -> Optional[RPSMove]:
        """Markov chain prediction."""
        if len(self.stats.player_move_history) < 5:
            return None

        # Build transition matrix
        transitions = {}
        for i in range(len(self.stats.player_move_history) - 1):
            current = self.stats.player_move_history[i]
            next_move = self.stats.player_move_history[i + 1]
            if current not in transitions:
                transitions[current] = {}
            if next_move not in transitions[current]:
                transitions[current][next_move] = 0
            transitions[current][next_move] += 1

        # Predict next move based on last move
        last_move = self.stats.player_move_history[-1]
        if last_move in transitions:
            return max(transitions[last_move].items(), key=lambda x: x[1])[0]

        return None

    def _get_losing_move(self) -> RPSMove:
        """Get a move that will likely lose."""
        # Predict player's move and play what loses to it
        predicted = self.analyzer.predict_next_move(self.stats.player_move_history)
        if predicted:
            # Play what loses to predicted
            loses_to = {
                RPSMove.ROCK: RPSMove.SCISSORS,
                RPSMove.PAPER: RPSMove.ROCK,
                RPSMove.SCISSORS: RPSMove.PAPER
            }
            return loses_to.get(predicted, RPSMove.random())
        return RPSMove.random()

    def _update_ai_confidence(self, outcome: GameOutcome):
        """Update AI confidence based on outcome."""
        if outcome == GameOutcome.LOSE:
            # AI predicted wrong or strategy failed
            self.ai_confidence = max(0.3, self.ai_confidence - 0.1)
        elif outcome == GameOutcome.WIN:
            # AI predicted correctly
            self.ai_confidence = min(0.9, self.ai_confidence + 0.05)

    def get_pet_reaction(self, result: RoundResult) -> PetReaction:
        """Get the pet's reaction to a round result."""
        if result.outcome == GameOutcome.WIN:
            reactions = [PetReaction.WIN_HAPPY, PetReaction.WIN_CHEER, PetReaction.WIN_DANCE]
            return random.choice(reactions)
        elif result.outcome == GameOutcome.LOSE:
            if self.stats.current_streak <= -3:
                return PetReaction.LOSE_CRY
            reactions = [PetReaction.LOSE_SAD, PetReaction.LOSE_POUT]
            return random.choice(reactions)
        else:
            reactions = [PetReaction.TIE_THINK, PetReaction.TIE_NEUTRAL]
            return random.choice(reactions)

    def get_pet_message(self, reaction: PetReaction) -> str:
        """Get pet's message based on reaction."""
        messages = {
            PetReaction.WIN_HAPPY: ["I won! 🎉", "Hehe, I'm good!", "Victory!"],
            PetReaction.WIN_CHEER: ["Yay!", "Woohoo!", "Best pet ever!"],
            PetReaction.WIN_DANCE: ["*happy dance*", "*spins around*", "Dance party!"],
            PetReaction.LOSE_SAD: ["Aww...", "Oh no...", "*looks sad*"],
            PetReaction.LOSE_POUT: ["Hey!", "*pouts*", "Not fair!"],
            PetReaction.LOSE_CRY: ["*whimper*", "You're too good...", "*sad eyes*"],
            PetReaction.TIE_THINK: ["Hmm...", "*thinking face*", "Interesting..."],
            PetReaction.TIE_NEUTRAL: ["Again!", "Tie game!", "Let's go again!"],
        }
        return random.choice(messages.get(reaction, ["Interesting..."]))

    def reset_stats(self):
        """Reset game statistics."""
        self.stats = GameStats()
        self.ai_confidence = 0.5

    def get_summary(self) -> Dict:
        """Get game summary."""
        return {
            'rounds': self.stats.rounds_played,
            'player_wins': self.stats.player_wins,
            'pet_wins': self.stats.pet_wins,
            'ties': self.stats.ties,
            'win_rate': f"{self.stats.get_win_rate() * 100:.1f}%",
            'current_streak': self.stats.current_streak,
            'best_streak': self.stats.best_streak,
            'ai_strategy': self.ai_strategy.value,
        }


class RPSTournament:
    """Tournament mode for Rock Paper Scissors."""

    def __init__(self, rounds: int = 5):
        self.total_rounds = rounds
        self.current_round = 0
        self.player_score = 0
        self.pet_score = 0
        self.game = RockPaperScissorsGame(ai_strategy=AIStrategy.EXPERT)
        self.round_results: List[RoundResult] = []

    def play_round(self, player_move: RPSMove) -> RoundResult:
        """Play a tournament round."""
        if self.current_round >= self.total_rounds:
            raise ValueError("Tournament is over!")

        result = self.game.play_round(player_move)
        self.round_results.append(result)
        self.current_round += 1

        if result.outcome == GameOutcome.WIN:
            self.player_score += 1
        elif result.outcome == GameOutcome.LOSE:
            self.pet_score += 1

        return result

    def is_over(self) -> bool:
        """Check if tournament is over."""
        return self.current_round >= self.total_rounds

    def get_winner(self) -> Optional[str]:
        """Get tournament winner if over."""
        if not self.is_over():
            return None

        if self.player_score > self.pet_score:
            return "player"
        elif self.pet_score > self.player_score:
            return "pet"
        return "tie"

    def get_summary(self) -> Dict:
        """Get tournament summary."""
        return {
            'rounds_played': self.current_round,
            'total_rounds': self.total_rounds,
            'player_score': self.player_score,
            'pet_score': self.pet_score,
            'winner': self.get_winner(),
        }


# Convenience functions

def play_game(player_move: str) -> Tuple[str, str, str]:
    """Quick play a round."""
    game = RockPaperScissorsGame()
    move = RPSMove(player_move.lower())
    result = game.play_round(move)
    return (str(result.player_move), str(result.pet_move), result.outcome.value)


if __name__ == "__main__":
    # Test the game
    print("Testing Rock Paper Scissors")

    game = RockPaperScissorsGame(ai_strategy=AIStrategy.PATTERN)

    print("\nPlaying 10 rounds:")
    for i in range(10):
        player_move = RPSMove.random()
        result = game.play_round(player_move)
        reaction = game.get_pet_reaction(result)
        message = game.get_pet_message(reaction)
        print(f"  Round {i+1}: {result} - {message}")

    print(f"\n{game.get_summary()}")

    # Test tournament
    print("\nTournament mode:")
    tournament = RPSTournament(rounds=5)

    moves = [RPSMove.ROCK, RPSMove.PAPER, RPSMove.SCISSORS,
             RPSMove.ROCK, RPSMove.PAPER]

    for move in moves:
        if not tournament.is_over():
            result = tournament.play_round(move)
            print(f"  {result}")

    print(f"\nTournament result: {tournament.get_summary()}")

    print("\nRock Paper Scissors test passed!")
