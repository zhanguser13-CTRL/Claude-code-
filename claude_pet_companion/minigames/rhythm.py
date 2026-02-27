"""
Rhythm Game for Claude Pet Companion

A musical rhythm game with:
- Beat detection and timing
- Combo system
- Multiple difficulty levels
- Various songs/patterns
- Visual and audio feedback
"""

import random
import logging
import time
import math
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class NoteType(Enum):
    """Types of rhythm notes."""
    TAP = "tap"           # Simple tap
    HOLD = "hold"         # Hold down
    SLIDE = "slide"       # Slide in a direction
    SPIN = "spin"         # Spin gesture
    DOUBLE = "double"     # Tap twice quickly


class Direction(Enum):
    """Directions for slide notes."""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"


class Difficulty(Enum):
    """Difficulty levels."""
    EASY = "easy"         # Slow, simple patterns
    NORMAL = "normal"     # Medium speed
    HARD = "hard"         # Fast, complex patterns
    EXPERT = "expert"     # Very fast, very complex


@dataclass
class Note:
    """A single note in the rhythm game."""
    note_type: NoteType
    time: float  # When the note occurs (seconds from start)
    direction: Direction = Direction.CENTER
    duration: float = 0.5  # For hold notes
    points: int = 100

    def __str__(self):
        return f"{self.note_type.value} {self.direction.value} @ {self.time:.2f}s"


@dataclass
class HitResult:
    """Result of hitting a note."""
    accuracy: float  # 0-1, how close to perfect timing
    hit: bool  # Whether the note was hit
    early: bool = False  # True if hit was too early
    late: bool = False  # True if hit was too late
    score: int = 0

    def get_rating(self) -> str:
        """Get text rating of the hit."""
        if not self.hit:
            return "MISS"
        if self.accuracy >= 0.95:
            return "PERFECT"
        elif self.accuracy >= 0.85:
            return "GREAT"
        elif self.accuracy >= 0.7:
            return "GOOD"
        elif self.accuracy >= 0.5:
            return "OK"
        else:
            return "BAD"


@dataclass
class Combo:
    """Combo tracking."""
    count: int = 0
    max_count: int = 0
    multiplier: float = 1.0

    def add_hit(self, rating: str) -> int:
        """Add a hit to combo. Returns score multiplier."""
        if rating in ("PERFECT", "GREAT", "GOOD", "OK"):
            self.count += 1
            self.max_count = max(self.max_count, self.count)

            # Update multiplier
            if self.count >= 50:
                self.multiplier = 8.0
            elif self.count >= 30:
                self.multiplier = 4.0
            elif self.count >= 20:
                self.multiplier = 3.0
            elif self.count >= 10:
                self.multiplier = 2.0
            else:
                self.multiplier = 1.0
        else:
            self.count = 0
            self.multiplier = 1.0

        return int(self.multiplier)


@dataclass
class Song:
    """A song with rhythm pattern."""
    name: str
    bpm: float  # Beats per minute
    duration: float  # Song duration in seconds
    notes: List[Note] = field(default_factory=list)

    def get_beat_duration(self) -> float:
        """Get duration of one beat in seconds."""
        return 60.0 / self.bpm

    def generate_notes(self, difficulty: Difficulty = Difficulty.NORMAL,
                     density: float = 0.5):
        """Generate notes based on difficulty."""
        self.notes.clear()

        beat_duration = self.get_beat_duration()
        total_beats = int(self.duration / beat_duration)

        # Determine note spacing based on difficulty
        if difficulty == Difficulty.EASY:
            note_interval = 4  # Every 4 beats
            max_complexity = 1
        elif difficulty == Difficulty.NORMAL:
            note_interval = 2
            max_complexity = 2
        elif difficulty == Difficulty.HARD:
            note_interval = 1
            max_complexity = 3
        else:  # EXPERT
            note_interval = 1
            max_complexity = 4

        # Generate notes
        for beat in range(0, total_beats, note_interval):
            if random.random() < density:
                # Determine note type
                note_type = NoteType.TAP
                direction = random.choice(list(Direction))

                if max_complexity >= 2:
                    note_type = random.choice([
                        NoteType.TAP,
                        NoteType.TAP,
                        NoteType.HOLD,
                        NoteType.SLIDE
                    ])

                if max_complexity >= 3:
                    note_type = random.choice([
                        NoteType.TAP,
                        NoteType.TAP,
                        NoteType.HOLD,
                        NoteType.SLIDE,
                        NoteType.SLIDE,
                        NoteType.DOUBLE
                    ])

                if max_complexity >= 4:
                    note_type = random.choice([
                        NoteType.TAP,
                        NoteType.HOLD,
                        NoteType.SLIDE,
                        NoteType.DOUBLE,
                        NoteType.SPIN
                    ])

                # Create note
                note = Note(
                    note_type=note_type,
                    time=beat * beat_duration,
                    direction=direction,
                    duration=beat_duration * 2 if note_type == NoteType.HOLD else 0.5
                )

                # Adjust points based on difficulty
                note.points = 100 * (difficulty.value.count('') + 1)
                self.notes.append(note)


class RhythmGame:
    """Main rhythm game class."""

    def __init__(self, song: Song = None, difficulty: Difficulty = Difficulty.NORMAL):
        self.song = song or Song("Default", 120.0, 60.0)
        self.difficulty = difficulty

        # Game state
        self.current_time = 0.0
        self.is_playing = False
        self.is_paused = False

        # Scoring
        self.score = 0
        self.combo = Combo()
        self.max_combo = 0
        self.notes_hit = 0
        self.notes_missed = 0
        self.perfect_hits = 0
        self.great_hits = 0
        self.good_hits = 0
        self.ok_hits = 0
        self.bad_hits = 0
        self.misses = 0

        # Hit window (milliseconds)
        self.perfect_window = 30
        self.great_window = 60
        self.good_window = 100
        self.ok_window = 150

        # Note tracking
        self.next_note_index = 0
        self.active_notes: List[Tuple[int, Note]] = []  # (original_index, note)
        self.hit_notes: List[int] = []

        # Callbacks
        on_note_hit: Optional[Callable[[Note, HitResult], None]] = None
        on_note_miss: Optional[Callable[[Note], None]] = None
        on_combo_change: Optional[Callable[[int], None]] = None

    def start(self):
        """Start the game."""
        self.current_time = 0.0
        self.is_playing = True
        self.is_paused = False
        self.next_note_index = 0
        self.active_notes = []
        self.hit_notes = []

        # Generate notes if needed
        if not self.song.notes:
            self.song.generate_notes(self.difficulty)

    def pause(self):
        """Pause the game."""
        self.is_paused = True

    def resume(self):
        """Resume the game."""
        self.is_paused = False

    def stop(self):
        """Stop the game."""
        self.is_playing = False
        self.is_paused = False

    def update(self, dt: float) -> List[Note]:
        """
        Update game state.

        Returns:
            List of notes that are now active (within hit window)
        """
        if not self.is_playing or self.is_paused:
            return []

        self.current_time += dt

        # Find notes that are now active
        newly_active = []

        while self.next_note_index < len(self.song.notes):
            note = self.song.notes[self.next_note_index]
            time_until = note.time - self.current_time

            # Add note if it's within the hit window
            if time_until <= self.ok_window / 1000.0:
                self.active_notes.append((self.next_note_index, note))
                self.next_note_index += 1
                newly_active.append(note)
            elif time_until < -self.ok_window / 1000.0:
                # Note was missed
                self._miss_note(note)
                self.next_note_index += 1
            else:
                # No more notes to activate
                break

        # Clean up old active notes
        self.active_notes = [
            (idx, note) for idx, note in self.active_notes
            if note.time + note.duration + self.ok_window / 1000.0 >= self.current_time
            and idx not in self.hit_notes
        ]

        return newly_active

    def handle_input(self, input_type: str, direction: Direction = Direction.CENTER) -> HitResult:
        """
        Handle player input.

        Args:
            input_type: Type of input ("tap", "hold", "slide", "spin")
            direction: Direction of the input

        Returns:
            HitResult for the input
        """
        if not self.active_notes:
            return HitResult(accuracy=0, hit=False, score=0)

        # Find closest note
        closest_note = None
        closest_idx = -1
        closest_diff = float('inf')

        for idx, note in self.active_notes:
            time_diff = abs(note.time - self.current_time)
            if time_diff < closest_diff:
                closest_diff = time_diff
                closest_note = note
                closest_idx = idx

        if closest_note:
            # Check if input matches note type
            input_matches = (
                input_type == closest_note.note_type.value or
                (input_type == "tap" and closest_note.note_type in (NoteType.TAP, NoteType.DOUBLE))
            )

            if input_matches:
                # Calculate accuracy
                time_diff_ms = closest_diff * 1000
                accuracy = 1.0 - (time_diff_ms / self.ok_window)
                accuracy = max(0, min(1, accuracy))

                # Determine rating
                if time_diff_ms <= self.perfect_window:
                    rating = "PERFECT"
                elif time_diff_ms <= self.great_window:
                    rating = "GREAT"
                elif time_diff_ms <= self.good_window:
                    rating = "GOOD"
                elif time_diff_ms <= self.ok_window:
                    rating = "OK"
                else:
                    rating = "MISS"

                hit = rating != "MISS"
                result = HitResult(
                    accuracy=accuracy,
                    hit=hit,
                    early=closest_note.time > self.current_time,
                    late=closest_note.time < self.current_time,
                    score=closest_note.points if hit else 0
                )

                if hit:
                    self._hit_note(closest_note, result, closest_idx)
                else:
                    self._miss_note(closest_note)

                return result

        # No matching note
        return HitResult(accuracy=0, hit=False, score=0)

    def _hit_note(self, note: Note, result: HitResult, note_idx: int):
        """Process a hit note."""
        rating = result.get_rating()

        # Update combo
        multiplier = self.combo.add_hit(rating)

        # Calculate score
        base_score = note.points
        final_score = int(base_score * multiplier * result.accuracy)
        result.score = final_score

        # Update stats
        self.score += final_score
        self.notes_hit += 1
        self.hit_notes.append(note_idx)

        if rating == "PERFECT":
            self.perfect_hits += 1
        elif rating == "GREAT":
            self.great_hits += 1
        elif rating == "GOOD":
            self.good_hits += 1
        elif rating == "OK":
            self.ok_hits += 1
        else:
            self.bad_hits += 1

        # Remove from active notes
        self.active_notes = [(idx, n) for idx, n in self.active_notes if idx != note_idx]

        # Callback
        if self.on_note_hit:
            self.on_note_hit(note, result)

        if self.on_combo_change and self.combo.count % 10 == 0:
            self.on_combo_change(self.combo.count)

    def _miss_note(self, note: Note):
        """Process a missed note."""
        self.combo.count = 0
        self.combo.multiplier = 1.0
        self.notes_missed += 1
        self.misses += 1

        if self.on_note_miss:
            self.on_note_miss(note)

        if self.on_combo_change:
            self.on_combo_change(0)

    def is_finished(self) -> bool:
        """Check if the song is finished."""
        return self.current_time >= self.song.duration

    def get_stats(self) -> Dict[str, Any]:
        """Get game statistics."""
        total_notes = self.notes_hit + self.notes_missed
        accuracy = (self.notes_hit / total_notes * 100) if total_notes > 0 else 0

        # Calculate letter grade
        if accuracy >= 95:
            grade = "S"
        elif accuracy >= 90:
            grade = "A"
        elif accuracy >= 80:
            grade = "B"
        elif accuracy >= 70:
            grade = "C"
        else:
            grade = "D"

        return {
            'score': self.score,
            'combo': self.combo.count,
            'max_combo': self.combo.max_count,
            'notes_hit': self.notes_hit,
            'notes_missed': self.notes_missed,
            'accuracy': f"{accuracy:.1f}%",
            'grade': grade,
            'perfect_hits': self.perfect_hits,
            'great_hits': self.great_hits,
            'good_hits': self.good_hits,
            'ok_hits': self.ok_hits,
            'misses': self.misses,
        }

    def reset(self):
        """Reset the game."""
        self.score = 0
        self.combo = Combo()
        self.max_combo = 0
        self.notes_hit = 0
        self.notes_missed = 0
        self.perfect_hits = 0
        self.great_hits = 0
        self.good_hits = 0
        self.ok_hits = 0
        self.bad_hits = 0
        self.misses = 0
        self.current_time = 0.0
        self.next_note_index = 0
        self.active_notes = []
        self.hit_notes = []


# Preset songs

class PresetSongs:
    """Preset songs for the rhythm game."""

    @staticmethod
    def simple_beat() -> Song:
        """Simple beat pattern."""
        return Song(
            name="Simple Beat",
            bpm=100.0,
            duration=30.0
        )

    @staticmethod
    def energetic() -> Song:
        """Energetic fast-paced song."""
        return Song(
            name="Energetic",
            bpm=140.0,
            duration=45.0
        )

    @staticmethod
    def chill() -> Song:
        """Chill slow song."""
        return Song(
            name="Chill Vibes",
            bpm=80.0,
            duration=60.0
        )

    @staticmethod
    def extreme() -> Song:
        """Extreme difficulty song."""
        return Song(
            name="Extreme Challenge",
            bpm=180.0,
            duration=30.0
        )


def create_game(song_name: str = "simple_beat",
               difficulty: Difficulty = Difficulty.NORMAL) -> RhythmGame:
    """Create a rhythm game with preset song."""
    song_getter = getattr(PresetSongs, song_name, None)
    if song_getter:
        song = song_getter()
    else:
        song = PresetSongs.simple_beat()

    game = RhythmGame(song, difficulty)
    game.start()
    return game


if __name__ == "__main__":
    # Test rhythm game
    print("Testing Rhythm Game")

    game = create_game("simple_beat", Difficulty.NORMAL)

    print(f"\nSong: {game.song.name}")
    print(f"BPM: {game.song.bpm}")
    print(f"Duration: {game.song.duration}s")
    print(f"Notes: {len(game.song.notes)}")

    # Simulate gameplay
    print("\nSimulating gameplay:")
    game.start()

    simulated_time = 0
    while simulated_time < game.song.duration:
        dt = 0.1
        active = game.update(dt)
        simulated_time += dt

        # Simulate hitting some notes
        if active:
            # Hit first active note 70% of the time
            if random.random() < 0.7:
                result = game.handle_input("tap", random.choice(list(Direction)))
                if result.hit:
                    print(f"  t={simulated_time:.1f}s: {result.get_rating()} - Score: {result.score}")

    print(f"\nFinal Stats: {game.get_stats()}")

    print("\nRhythm game test passed!")
