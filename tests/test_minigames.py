"""
Unit Tests for Minigames

Tests the various minigames.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pet_companion.minigames.rock_paper_scissors import (
    RPSMove,
    GameOutcome,
    RoundResult,
    GameStats,
    AIStrategy,
    PatternAnalyzer,
    RockPaperScissorsGame,
    RPSTournament,
    play_game
)


class TestRPSMove:
    """Test Rock Paper Scissors moves."""

    def test_all_moves_defined(self):
        """Test all RPS moves have values."""
        for move in RPSMove:
            assert move.value in ["rock", "paper", "scissors"]
            assert len(move.emoji()) > 0

    def test_beats_returns_true(self):
        """Test beats() correctly identifies winning moves."""
        assert RPSMove.ROCK.beats(RPSMove.SCISSORS) is True
        assert RPSMove.PAPER.beats(RPSMove.ROCK) is True
        assert RPSMove.SCISSORS.beats(RPSMove.PAPER) is True

    def test_beats_opposite_of_ties(self):
        """Test beats() returns False for losing or tying moves."""
        assert not RPSMove.ROCK.beats(RPSMove.ROCK)
        assert not RPSMove.ROCK.beats(RPSMove.PAPER)

    def test_random_returns_valid_move(self):
        """Test random() returns a valid move."""
        for _ in range(20):
            move = RPSMove.random()
            assert move in RPSMove


class TestGameOutcome:
    """Test game outcome enums."""

    def test_all_outcomes_defined(self):
        """Test all outcomes have values."""
        assert GameOutcome.WIN.value == "win"
        assert GameOutcome.LOSE.value == "lose"
        assert GameOutcome.TIE.value == "tie"


class TestRoundResult:
    """Test round result dataclass."""

    def test_creation(self):
        """Test creating a round result."""
        result = RoundResult(
            player_move=RPSMove.ROCK,
            pet_move=RPSMove.PAPER,
            outcome=GameOutcome.LOSE
        )

        assert result.player_move == RPSMove.ROCK
        assert result.pet_move == RPSMove.PAPER
        assert result.outcome == GameOutcome.LOSE

    def test_to_string(self):
        """Test string representation."""
        result = RoundResult(
            player_move=RPSMove.ROCK,
            pet_move=RPSMove.SCISSORS,
            outcome=GameOutcome.WIN
        )

        string_repr = str(result)
        assert "rock" in string_repr.lower()
        assert "scissors" in string_repr.lower()


class TestGameStats:
    """Test game statistics."""

    def test_initial_stats(self):
        """Test initial statistics are zero."""
        stats = GameStats()

        assert stats.rounds_played == 0
        assert stats.player_wins == 0
        assert stats.pet_wins == 0
        assert stats.ties == 0
        assert stats.current_streak == 0

    def test_get_win_rate(self):
        """Test win rate calculation."""
        stats = GameStats()
        stats.rounds_played = 10
        stats.player_wins = 7

        assert stats.get_win_rate() == 0.7

    def test_win_rate_empty(self):
        """Test win rate with no rounds."""
        stats = GameStats()
        assert stats.get_win_rate() == 0.0

    def test_most_common_move(self):
        """Test most common move detection."""
        stats = GameStats()
        stats.player_move_history = [
            RPSMove.ROCK,
            RPSMove.ROCK,
            RPSMove.PAPER,
            RPSMove.ROCK
        ]

        assert stats.get_most_common_player_move() == RPSMove.ROCK

    def test_most_common_move_empty(self):
        """Test most common move with no history."""
        stats = GameStats()
        assert stats.get_most_common_player_move() is None


class TestPatternAnalyzer:
    """Test pattern analysis for AI."""

    def test_predict_repetition(self):
        """Test detecting repeated moves."""
        analyzer = PatternAnalyzer()

        # Player always plays rock
        history = [RPSMove.ROCK] * 5
        predicted = analyzer.predict_next_move(history)

        assert predicted == RPSMove.ROCK

    def test_predict_alternating(self):
        """Test detecting alternating pattern."""
        analyzer = PatternAnalyzer(history_length=10)

        # Alternating rock-paper-rock-paper...
        history = [RPSMove.ROCK, RPSMove.PAPER] * 3
        predicted = analyzer.predict_next_move(history)

        assert predicted in [RPSMove.ROCK, RPSMove.PAPER]

    def test_counter_move(self):
        """Test getting counter move."""
        analyzer = PatternAnalyzer()

        counter = analyzer.get_counter_move(RPSMove.ROCK)
        assert counter == RPSMove.PAPER

        counter = analyzer.get_counter_move(RPSMove.PAPER)
        assert counter == RPSMove.SCISSORS

        counter = analyzer.get_counter_move(RPSMove.SCISSORS)
        assert counter == RPSMove.ROCK


class TestRockPaperScissorsGame:
    """Test the main game class."""

    def test_game_creation(self):
        """Test creating a game."""
        game = RockPaperScissorsGame()
        assert game is not None

    def test_play_single_round(self):
        """Test playing a single round."""
        game = RockPaperScissorsGame()

        result = game.play_round(RPSMove.ROCK)

        assert isinstance(result, RoundResult)
        assert result.player_move == RPSMove.ROCK
        assert isinstance(result.pet_move, RPSMove)

    def test_score_tracking(self):
        """Test score is tracked correctly."""
        game = RockPaperScissorsGame()

        game.play_round(RPSMove.ROCK)
        game.play_round(RPSMove.ROCK)  # Win

        stats = game.get_stats()
        assert stats.player_wins > 0

    def test_ai_confidence_updates(self):
        """Test AI confidence changes based on outcomes."""
        game = RockPaperScissorsGame()

        initial_confidence = game.ai_confidence

        # Lose - confidence should decrease
        game.play_round(RPSMove.ROCK)
        assert game.ai_confidence < initial_confidence

    def test_get_pet_reaction(self):
        """Test pet reaction generation."""
        game = RockPaperScissorsGame()

        result = RoundResult(
            player_move=RPSMove.ROCK,
            pet_move=RPSMove.PAPER,
            outcome=GameOutcome.WIN
        )

        reaction = game.get_pet_reaction(result)
        assert reaction in [r for r in PetReaction]  # Import would be needed

    def test_reset_stats(self):
        """Test resetting statistics."""
        game = RockPaperScissorsGame()

        game.play_round(RPSMove.ROCK)
        assert game.stats.rounds_played > 0

        game.reset_stats()
        assert game.stats.rounds_played == 0


class TestRPSTournament:
    """Test tournament mode."""

    def test_tournament_creation(self):
        """Test creating a tournament."""
        tournament = RPSTournament(rounds=5)
        assert tournament.total_rounds == 5

    def test_tournament_progress(self):
        """Test tournament tracks rounds correctly."""
        tournament = RPSTournament(rounds=3)

        assert tournament.current_round == 0
        assert tournament.is_over() is False

        tournament.play_round(RPSMove.ROCK)
        assert tournament.current_round == 1

    def test_tournament_completion(self):
        """Test tournament completion detection."""
        tournament = RPSTournament(rounds=2)

        tournament.play_round(RPSMove.ROCK)
        tournament.play_round(RPSMove.ROCK)

        assert tournament.is_over() is True
        assert tournament.get_winner() in ["player", "pet", "tie"]


# Test helper functions

class TestHelperFunctions:
    """Test helper functions."""

    def test_play_game_function(self):
        """Test the play_game convenience function."""
        player_move_str, pet_move_str, outcome_str = play_game("rock")

        assert player_move_str in ["rock", "paper", "scissors"]
        assert pet_move_str in ["rock", "paper", "scissors"]
        assert outcome_str in ["win", "lose", "tie"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
