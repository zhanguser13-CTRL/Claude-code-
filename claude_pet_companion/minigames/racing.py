"""
Racing Minigame for Claude Pet Companion

A fun pet racing game with:
- Multiple pets with different stats
- Track with obstacles and power-ups
- Betting system
- Race commentary
"""

import random
import logging
import time
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TrackType(Enum):
    """Types of race tracks."""
    GRASS = "grass"         # Normal speed
    DIRT = "dirt"          # Slower but good traction
    SAND = "sand"          # Slow
    WATER = "water"        # Swimming
    AIR = "air"            # Flying


class ObstacleType(Enum):
    """Types of obstacles."""
    NONE = "none"
    HURDLE = "hurdle"      # Jump over
    MUD = "mud"           # Slow down
    WATER_PUDDLE = "puddle"  # Swimmable, need water affinity
    BOOST = "boost"       # Speed up
    SHORTCUT = "shortcut" # Skip section


@dataclass
class PetRacer:
    """A pet participating in a race."""
    name: str
    base_speed: float = 10.0  # Base speed stat
    acceleration: float = 1.0
    stamina: float = 100.0
    jumping: float = 0.5  # 0-1, ability to jump
    swimming: float = 0.5  # 0-1, ability to swim
    flying: float = 0.0    # 0-1, ability to fly

    # Race state
    position: float = 0.0  # Distance along track
    current_speed: float = 0.0
    stamina_used: float = 0.0
    finished: bool = False
    finish_time: float = 0.0
    lane: int = 0

    # Visual
    emoji: str = "🐾"

    def get_effective_speed(self, track_type: TrackType) -> float:
        """Get speed considering track type."""
        speed = self.base_speed

        if track_type == TrackType.GRASS:
            return speed
        elif track_type == TrackType.DIRT:
            return speed * 0.9
        elif track_type == TrackType.SAND:
            return speed * 0.7
        elif track_type == TrackType.WATER:
            return speed * (0.5 + self.swimming * 0.5)
        elif track_type == TrackType.AIR:
            return speed * (0.5 + self.flying * 0.5)

        return speed

    def can_jump(self, obstacle_height: float = 1.0) -> bool:
        """Check if pet can jump an obstacle."""
        return self.jumping >= obstacle_height * 0.5

    def can_swim(self) -> bool:
        """Check if pet can swim."""
        return self.swimming > 0.3

    def can_fly(self) -> bool:
        """Check if pet can fly."""
        return self.flying > 0.5


@dataclass
class TrackObstacle:
    """An obstacle on the track."""
    position: float  # Distance along track (0-1)
    obstacle_type: ObstacleType
    severity: float = 1.0  # How severe the effect is


@dataclass
class PowerUp:
    """A power-up on the track."""
    position: float  # Distance along track (0-1)
    effect_type: str  # "speed_boost", "stamina", "shield"
    duration: float = 2.0  # How long the effect lasts
    magnitude: float = 1.5  # Effect multiplier


@dataclass
class RaceTrack:
    """A race track configuration."""
    name: str = "Default Track"
    length: float = 100.0  # meters
    track_type: TrackType = TrackType.GRASS
    num_lanes: int = 4
    obstacles: List[TrackObstacle] = field(default_factory=list)
    power_ups: List[PowerUp] = field(default_factory=list)
    difficulty: float = 0.5  # 0-1

    def get_description(self) -> str:
        """Get track description."""
        return f"{self.name} ({self.track_type.value}, {self.length}m)"


class RaceCommentator:
    """Provides race commentary."""

    def __init__(self):
        self.phrases_start = [
            "And they're off!",
            "The race begins!",
            "Here we go!",
            "Let the race begin!",
        ]

        self.phrases_mid = [
            "What an exciting race!",
            "It's neck and neck!",
            "The competition is fierce!",
            "Look at that speed!",
        ]

        self.phrases_finish = [
            "And that's the race!",
            "What a finish!",
            "Incredible performance!",
        ]

        self.phrases_obstacle = [
            "Oh! A tricky obstacle!",
            "Can they make it over?",
            "Smooth navigation!",
            "A bit of trouble there!",
        ]

    def get_start_comment(self) -> str:
        """Get starting comment."""
        return random.choice(self.phrases_start)

    def get_mid_race_comment(self, positions: Dict[PetRacer, float]) -> str:
        """Get mid-race comment."""
        base = random.choice(self.phrases_mid)

        # Add leader info
        if positions:
            leader = max(positions.items(), key=lambda x: x[1])
            base += f" {leader[0].name} is in the lead!"

        return base

    def get_obstacle_comment(self, racer: PetRacer, success: bool) -> str:
        """Get obstacle comment."""
        if success:
            return f"{racer.name} clears it beautifully!"
        else:
            return f"{racer.name} is having trouble!"

    def get_finish_comment(self, winner: PetRacer) -> str:
        """Get finish comment."""
        base = random.choice(self.phrases_finish)
        return f"{base} {winner.name} takes the victory!"


@dataclass
class RaceResult:
    """Result of a race."""
    racer: PetRacer
    position: int  # 1 = first
    time: float
    disqualified: bool = False


class RacingGame:
    """Main racing game class."""

    def __init__(self, track: RaceTrack = None):
        self.track = track or RaceTrack()
        self.racers: List[PetRacer] = []
        self.commentator = RaceCommentator()
        self.race_time = 0.0
        self.race_running = False
        self.race_finished = False
        self.results: List[RaceResult] = []

        # Betting
        self.bets: Dict[str, PetRacer] = {}  # player_id -> racer

        # Callbacks
        on_position_update: Optional[Callable] = None
        on_commentary: Optional[Callable[[str], None]] = None

    def add_racer(self, racer: PetRacer) -> int:
        """Add a racer to the race."""
        racer.lane = len(self.racers)
        self.racers.append(racer)
        return len(self.racers) - 1

    def place_bet(self, player_id: str, racer: PetRacer) -> bool:
        """Place a bet on a racer."""
        if racer in self.racers:
            self.bets[player_id] = racer
            return True
        return False

    def start_race(self) -> str:
        """Start the race."""
        if len(self.racers) < 2:
            return "Need at least 2 racers!"

        self.race_running = True
        self.race_time = 0.0
        self.race_finished = False
        self.results.clear()

        # Reset racers
        for racer in self.racers:
            racer.position = 0.0
            racer.current_speed = 0.0
            racer.stamina_used = 0.0
            racer.finished = False
            racer.finish_time = 0.0

        comment = self.commentator.get_start_comment()
        if self.on_commentary:
            self.on_commentary(comment)

        return comment

    def update(self, dt: float) -> Tuple[bool, List[str]]:
        """
        Update race state.

        Returns:
            (race_finished, comments)
        """
        if not self.race_running or self.race_finished:
            return (True, ["Race not started or already finished"])

        self.race_time += dt
        comments = []

        # Update each racer
        for racer in self.racers:
            if racer.finished:
                continue

            # Get effective speed
            base_speed = racer.get_effective_speed(self.track.track_type)

            # Apply acceleration
            if racer.current_speed < base_speed:
                racer.current_speed += racer.acceleration * dt

            # Check stamina
            if racer.stamina_used >= racer.stamina:
                # Fatigue sets in
                racer.current_speed *= 0.8

            # Check for obstacles
            for obstacle in self.track.obstacles:
                obstacle_pos = obstacle.position * self.track.length
                if abs(racer.position - obstacle_pos) < 2.0:
                    # At obstacle
                    if obstacle.obstacle_type == ObstacleType.HURDLE:
                        if racer.can_jump():
                            # Successfully jump (small speed penalty)
                            racer.current_speed *= 0.8
                        else:
                            # Failed jump (larger speed penalty)
                            racer.current_speed *= 0.4
                            comments.append(self.commentator.get_obstacle_comment(racer, False))

                    elif obstacle.obstacle_type == ObstacleType.MUD:
                        racer.current_speed *= 0.5

                    elif obstacle.obstacle_type == ObstacleType.WATER_PUDDLE:
                        if not racer.can_swim():
                            racer.current_speed *= 0.3
                        else:
                            racer.current_speed *= 0.7

            # Check for power-ups
            for power_up in self.track.power_ups:
                power_up_pos = power_up.position * self.track.length
                if abs(racer.position - power_up_pos) < 1.0:
                    # At power-up
                    if power_up.effect_type == "speed_boost":
                        racer.current_speed *= power_up.magnitude

            # Move racer
            move_distance = racer.current_speed * dt
            racer.position += move_distance
            racer.stamina_used += move_distance * 0.1

            # Check for finish
            if racer.position >= self.track.length:
                racer.position = self.track.length
                racer.finished = True
                racer.finish_time = self.race_time

                results = len([r for r in self.racers if r.finished])
                if results == 1:
                    winner_comment = self.commentator.get_finish_comment(racer)
                    comments.append(winner_comment)
                    if self.on_commentary:
                        self.on_commentary(winner_comment)

        # Check if race is over
        if all(racer.finished for racer in self.racers):
            self._finish_race()
            return (True, comments)

        # Mid-race commentary
        if int(self.race_time * 2) % 5 == 0:  # Every ~5 seconds
            positions = {r: r.position for r in self.racers}
            mid_comment = self.commentator.get_mid_race_comment(positions)
            if self.on_commentary:
                self.on_commentary(mid_comment)
            comments.append(mid_comment)

        return (False, comments)

    def _finish_race(self):
        """Finalize race results."""
        self.race_finished = True
        self.race_running = False

        # Sort by finish time
        finished_racers = [r for r in self.racers if r.finished]
        finished_racers.sort(key=lambda r: r.finish_time)

        self.results = [
            RaceResult(
                racer=racer,
                position=i + 1,
                time=racer.finish_time,
                disqualified=False
            )
            for i, racer in enumerate(finished_racers)
        ]

    def get_leaderboard(self) -> List[Tuple[int, PetRacer, float]]:
        """Get current race standings."""
        sorted_racers = sorted(
            self.racers,
            key=lambda r: (r.position, -r.finish_time if r.finished else float('inf')),
            reverse=True
        )
        return [(i + 1, r, r.position) for i, r in enumerate(sorted_racers)]

    def get_winner(self) -> Optional[PetRacer]:
        """Get the race winner."""
        if self.results:
            return self.results[0].racer
        return None

    def check_bet_result(self, player_id: str) -> Tuple[bool, int]:
        """
        Check if a player's bet won.

        Returns:
            (won, position)
        """
        if player_id not in self.bets:
            return (False, -1)

        bet_racer = self.bets[player_id]

        for i, result in enumerate(self.results):
            if result.racer == bet_racer:
                return (i == 0, i + 1)

        return (False, -1)


# Preset tracks

class PresetTracks:
    """Preset race tracks."""

    @staticmethod
    def grassland() -> RaceTrack:
        """Simple grass track."""
        return RaceTrack(
            name="Green Grassland",
            length=100.0,
            track_type=TrackType.GRASS,
            num_lanes=4,
            difficulty=0.3,
            obstacles=[
                TrackObstacle(25.0, ObstacleType.HURDLE, 0.5),
                TrackObstacle(50.0, ObstacleType.HURDLE, 0.6),
                TrackObstacle(75.0, ObstacleType.HURDLE, 0.5),
            ]
        )

    @staticmethod
    def dirt_track() -> RaceTrack:
        """Dirt track with mud."""
        return RaceTrack(
            name="Dusty Dirt Track",
            length=120.0,
            track_type=TrackType.DIRT,
            num_lanes=6,
            difficulty=0.5,
            obstacles=[
                TrackObstacle(30.0, ObstacleType.MUD, 0.7),
                TrackObstacle(60.0, ObstacleType.HURDLE, 0.6),
                TrackObstacle(90.0, ObstacleType.MUD, 0.8),
            ],
            power_ups=[
                PowerUp(40.0, "speed_boost", 2.0, 1.3),
                PowerUp(80.0, "speed_boost", 2.0, 1.3),
            ]
        )

    @staticmethod
    def water_course() -> RaceTrack:
        """Track with water sections."""
        return RaceTrack(
            name="Aqua Circuit",
            length=150.0,
            track_type=TrackType.WATER,
            num_lanes=4,
            difficulty=0.7,
            obstacles=[
                TrackObstacle(0.2, ObstacleType.WATER_PUDDLE, 1.0),
                TrackObstacle(0.5, ObstacleType.WATER_PUDDLE, 1.0),
                TrackObstacle(0.8, ObstacleType.WATER_PUDDLE, 1.0),
            ]
        )

    @staticmethod
    def championship() -> RaceTrack:
        """Championship track."""
        return RaceTrack(
            name="Championship Circuit",
            length=200.0,
            track_type=TrackType.GRASS,
            num_lanes=8,
            difficulty=0.9,
            obstacles=[
                TrackObstacle(0.1, ObstacleType.HURDLE, 0.5),
                TrackObstacle(0.2, ObstacleType.MUD, 0.6),
                TrackObstacle(0.3, ObstacleType.HURDLE, 0.7),
                TrackObstacle(0.4, ObstacleType.WATER_PUDDLE, 0.5),
                TrackObstacle(0.5, ObstacleType.HURDLE, 0.8),
                TrackObstacle(0.6, ObstacleType.MUD, 0.7),
                TrackObstacle(0.7, ObstacleType.HURDLE, 0.9),
                TrackObstacle(0.8, ObstacleType.MUD, 0.6),
                TrackObstacle(0.9, ObstacleType.HURDLE, 0.7),
            ],
            power_ups=[
                PowerUp(0.25, "speed_boost", 3.0, 1.5),
                PowerUp(0.55, "speed_boost", 3.0, 1.4),
                PowerUp(0.85, "speed_boost", 3.0, 1.5),
            ]
        )


# Preset racers

class PresetRacers:
    """Preset pet racers."""

    @staticmethod
    def speedy() -> PetRacer:
        """Fast but low stamina."""
        return PetRacer(
            name="Speedy",
            base_speed=15.0,
            acceleration=1.5,
            stamina=60.0,
            jumping=0.7,
            swimming=0.3,
            emoji="⚡"
        )

    @staticmethod
    def steady() -> PetRacer:
        """Balanced stats."""
        return PetRacer(
            name="Steady",
            base_speed=10.0,
            acceleration=1.0,
            stamina=100.0,
            jumping=0.5,
            swimming=0.5,
            emoji="🐾"
        )

    @staticmethod
    def jumper() -> PetRacer:
        """Great at jumping."""
        return PetRacer(
            name="Jumper",
            base_speed=9.0,
            acceleration=0.9,
            stamina=90.0,
            jumping=0.95,
            swimming=0.4,
            emoji="🦘"
        )

    @staticmethod
    def swimmer() -> PetRacer:
        """Great at swimming."""
        return PetRacer(
            name="Swimmer",
            base_speed=8.0,
            acceleration=0.8,
            stamina=95.0,
            jumping=0.3,
            swimming=0.95,
            emoji="🐟"
        )

    @staticmethod
    def flyboy() -> PetRacer:
        """Can fly over obstacles."""
        return PetRacer(
            name="Flyboy",
            base_speed=11.0,
            acceleration=1.2,
            stamina=70.0,
            jumping=0.6,
            swimming=0.3,
            flying=0.9,
            emoji="🕊️"
        )

    @staticmethod
    def tank() -> PetRacer:
        """Slow but unstoppable."""
        return PetRacer(
            name="Tank",
            base_speed=7.0,
            acceleration=0.5,
            stamina=150.0,
            jumping=0.4,
            swimming=0.6,
            emoji="🛡️"
        )


def create_race(track_name: str = "grassland") -> RacingGame:
    """Create a race with preset track and racers."""
    track_getter = getattr(PresetTracks, track_name, None)
    if track_getter:
        track = track_getter()
    else:
        track = PresetTracks.grassland()

    game = RacingGame(track)

    # Add preset racers
    for racer_getter in [PresetRacers.speedy, PresetRacers.steady,
                        PresetRacers.jumper, PresetRacers.swimmer]:
        racer = racer_getter()
        game.add_racer(racer)

    return game


if __name__ == "__main__":
    # Test racing game
    print("Testing Racing Game")

    race = create_race("grassland")

    print(f"\nTrack: {race.track.get_description()}")
    print("Racers:")
    for i, racer in enumerate(race.racers):
        print(f"  {i+1}. {racer.name} ({racer.emoji}) - Speed: {racer.base_speed}")

    # Start race
    start_comment = race.start_race()
    print(f"\n{start_comment}")

    # Simulate race
    print("\nRace progress:")
    finished = False
    total_time = 0

    while not finished:
        finished, comments = race.update(0.1)
        total_time += 0.1

        # Print progress every second
        if int(total_time * 10) % 10 == 0:
            leaderboard = race.get_leaderboard()
            leader = leaderboard[0]
            print(f"  t={total_time:.1f}s: Leader is {leader[1].name} at {leader[2]:.1f}m")

        for comment in comments:
            print(f"  Comment: {comment}")

    # Print results
    print("\nFinal Results:")
    for result in race.results:
        print(f"  {result.position}. {result.racer.name} - {result.time:.2f}s")

    print("\nRacing game test passed!")
