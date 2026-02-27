"""
Claude Code Pet Companion - Animation Library

This module provides:
- Animation type definitions
- Keyframe animation system
- Predefined animation sequences
- Easing functions for smooth transitions
"""
from enum import Enum
from typing import Dict, List, Optional, Callable, Tuple, Any
from dataclasses import dataclass, field
import math
import time


# ============================================================================
# Animation Types
# ============================================================================

class AnimationType(Enum):
    """Types of animations."""
    IDLE = "idle"
    WALK = "walk"
    JUMP = "jump"
    EAT = "eat"
    SLEEP = "sleep"
    PLAY = "play"
    EVOLUTION = "evolution"
    LEVEL_UP = "level_up"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SURPRISED = "surprised"
    BOUNCE = "bounce"
    SHAKE = "shake"
    SPIN = "spin"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    GROW = "grow"
    SHRINK = "shrink"
    DANCE = "dance"
    WAVE = "wave"


# ============================================================================
# Easing Functions
# ============================================================================

class Easing(Enum):
    """Easing function types for animation interpolation."""

    @staticmethod
    def linear(t: float) -> float:
        """Linear easing."""
        return max(0.0, min(1.0, t))

    @staticmethod
    def ease_in_quad(t: float) -> float:
        """Quadratic ease in."""
        return t * t

    @staticmethod
    def ease_out_quad(t: float) -> float:
        """Quadratic ease out."""
        return t * (2 - t)

    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """Quadratic ease in and out."""
        return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2

    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """Cubic ease in."""
        return t * t * t

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Cubic ease out."""
        return 1 - pow(1 - t, 3)

    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Cubic ease in and out."""
        return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2

    @staticmethod
    def ease_in_bounce(t: float) -> float:
        """Bounce ease in."""
        return 1 - Easing.ease_out_bounce(1 - t)

    @staticmethod
    def ease_out_bounce(t: float) -> float:
        """Bounce ease out."""
        n1 = 7.5625
        d1 = 2.75
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375

    @staticmethod
    def ease_in_elastic(t: float) -> float:
        """Elastic ease in."""
        return -math.pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * ((2 * math.pi) / 3))

    @staticmethod
    def ease_out_elastic(t: float) -> float:
        """Elastic ease out."""
        return math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * ((2 * math.pi) / 3)) if t != 0 else 0

    @staticmethod
    def ease_out_back(t: float) -> float:
        """Back ease out."""
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)


# ============================================================================
# Keyframe System
# ============================================================================

@dataclass
class Keyframe:
    """A single keyframe in an animation."""
    time: float                           # Time position (0-1)
    properties: Dict[str, Any]            # Property values at this keyframe
    easing: Callable[[float], float] = Easing.linear

    def interpolate(self, other: 'Keyframe', t: float) -> Dict[str, Any]:
        """
        Interpolate between this keyframe and another.

        Args:
            other: Next keyframe to interpolate to
            t: Progress between keyframes (0-1)

        Returns:
            Interpolated properties
        """
        result = {}
        all_keys = set(self.properties.keys()) | set(other.properties.keys())

        for key in all_keys:
            start_val = self.properties.get(key, 0)
            end_val = other.properties.get(key, 0)

            # Apply easing
            eased_t = self.easing(t)

            # Interpolate based on type
            if isinstance(start_val, (int, float)) and isinstance(end_val, (int, float)):
                result[key] = start_val + (end_val - start_val) * eased_t
            else:
                # For non-numeric values, just use the end value
                result[key] = end_val if eased_t > 0.5 else start_val

        return result


# ============================================================================
# Animation Definition
# ============================================================================

@dataclass
class Animation:
    """An animation sequence with keyframes."""
    name: str
    animation_type: AnimationType
    duration: float                        # Duration in seconds
    keyframes: List[Keyframe] = field(default_factory=list)
    loop: bool = False
    loop_delay: float = 0.0

    def get_properties_at(self, elapsed: float) -> Dict[str, Any]:
        """
        Get animated property values at a given time.

        Args:
            elapsed: Time elapsed since animation start

        Returns:
            Dictionary of property values
        """
        # Handle looping
        if self.loop and elapsed > self.duration:
            cycle_time = self.duration + self.loop_delay
            elapsed = elapsed % cycle_time

        # Clamp to duration
        t = min(elapsed / self.duration, 1.0) if self.duration > 0 else 1.0

        # Find surrounding keyframes
        if not self.keyframes:
            return {}

        if len(self.keyframes) == 1:
            return self.keyframes[0].properties.copy()

        # Find the keyframe pair
        for i in range(len(self.keyframes) - 1):
            kf_start = self.keyframes[i]
            kf_end = self.keyframes[i + 1]

            if kf_start.time <= t <= kf_end.time:
                # Calculate local t between keyframes
                local_duration = kf_end.time - kf_start.time
                local_t = (t - kf_start.time) / local_duration if local_duration > 0 else 0

                return kf_start.interpolate(kf_end, local_t)

        # Return last keyframe if past end
        return self.keyframes[-1].properties.copy()

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.animation_type.value,
            "duration": self.duration,
            "loop": self.loop,
            "loop_delay": self.loop_delay,
            "keyframes": [
                {
                    "time": kf.time,
                    "properties": kf.properties,
                }
                for kf in self.keyframes
            ],
        }


# ============================================================================
# Animation Builder
# ============================================================================

class AnimationBuilder:
    """Builder for creating animations more easily."""

    def __init__(self, name: str, animation_type: AnimationType, duration: float):
        self.name = name
        self.animation_type = animation_type
        self.duration = duration
        self.keyframes: List[Keyframe] = []
        self.loop = False
        self.loop_delay = 0.0

    def add_keyframe(self, time: float, properties: Dict[str, Any],
                     easing: Callable[[float], float] = Easing.linear) -> 'AnimationBuilder':
        """Add a keyframe."""
        self.keyframes.append(Keyframe(time=time, properties=properties, easing=easing))
        return self

    def set_loop(self, loop: bool, delay: float = 0.0) -> 'AnimationBuilder':
        """Set loop settings."""
        self.loop = loop
        self.loop_delay = delay
        return self

    def build(self) -> Animation:
        """Build the animation."""
        # Sort keyframes by time
        self.keyframes.sort(key=lambda kf: kf.time)
        return Animation(
            name=self.name,
            animation_type=self.animation_type,
            duration=self.duration,
            keyframes=self.keyframes,
            loop=self.loop,
            loop_delay=self.loop_delay,
        )


# ============================================================================
# Predefined Animations
# ============================================================================

def create_idle_animation() -> Animation:
    """Create a gentle idle breathing animation."""
    return (AnimationBuilder("idle", AnimationType.IDLE, 2.0)
            .add_keyframe(0.0, {"scale_y": 1.0, "offset_y": 0})
            .add_keyframe(0.5, {"scale_y": 1.05, "offset_y": -2}, Easing.ease_in_out_quad)
            .add_keyframe(1.0, {"scale_y": 1.0, "offset_y": 0}, Easing.ease_in_out_quad)
            .set_loop(True)
            .build())


def create_bounce_animation() -> Animation:
    """Create a bouncing animation."""
    return (AnimationBuilder("bounce", AnimationType.BOUNCE, 0.5)
            .add_keyframe(0.0, {"offset_y": 0, "scale_y": 1.0, "scale_x": 1.0})
            .add_keyframe(0.3, {"offset_y": -20, "scale_y": 1.1, "scale_x": 0.9}, Easing.ease_out_quad)
            .add_keyframe(0.5, {"offset_y": 0, "scale_y": 0.95, "scale_x": 1.05}, Easing.ease_in_quad)
            .add_keyframe(0.7, {"offset_y": 5, "scale_y": 1.0, "scale_x": 1.0}, Easing.ease_out_quad)
            .add_keyframe(1.0, {"offset_y": 0, "scale_y": 1.0, "scale_x": 1.0}, Easing.linear)
            .build())


def create_walk_animation() -> Animation:
    """Create a walking animation."""
    return (AnimationBuilder("walk", AnimationType.WALK, 0.6)
            .add_keyframe(0.0, {"offset_y": 0, "rotation": 0})
            .add_keyframe(0.25, {"offset_y": -5, "rotation": 5}, Easing.ease_in_out_quad)
            .add_keyframe(0.5, {"offset_y": 0, "rotation": 0}, Easing.ease_in_out_quad)
            .add_keyframe(0.75, {"offset_y": -5, "rotation": -5}, Easing.ease_in_out_quad)
            .add_keyframe(1.0, {"offset_y": 0, "rotation": 0}, Easing.ease_in_out_quad)
            .set_loop(True)
            .build())


def create_eat_animation() -> Animation:
    """Create an eating animation."""
    return (AnimationBuilder("eat", AnimationType.EAT, 1.0)
            .add_keyframe(0.0, {"scale_x": 1.0, "scale_y": 1.0, "rotation": 0})
            .add_keyframe(0.2, {"scale_x": 1.1, "scale_y": 0.9, "rotation": 5}, Easing.ease_in_out_quad)
            .add_keyframe(0.4, {"scale_x": 1.0, "scale_y": 1.0, "rotation": -5}, Easing.ease_in_out_quad)
            .add_keyframe(0.6, {"scale_x": 1.1, "scale_y": 0.9, "rotation": 5}, Easing.ease_in_out_quad)
            .add_keyframe(0.8, {"scale_x": 1.0, "scale_y": 1.0, "rotation": 0}, Easing.ease_out_quad)
            .add_keyframe(1.0, {"scale_x": 1.0, "scale_y": 1.0, "rotation": 0})
            .build())


def create_sleep_animation() -> Animation:
    """Create a sleeping animation."""
    return (AnimationBuilder("sleep", AnimationType.SLEEP, 3.0)
            .add_keyframe(0.0, {"scale_x": 1.0, "scale_y": 1.0, "alpha": 1.0})
            .add_keyframe(0.5, {"scale_x": 1.0, "scale_y": 0.8, "alpha": 0.8}, Easing.ease_in_out_quad)
            .add_keyframe(1.0, {"scale_x": 1.0, "scale_y": 1.0, "alpha": 1.0}, Easing.ease_in_out_quad)
            .set_loop(True, 0.5)
            .build())


def create_level_up_animation() -> Animation:
    """Create a level up animation."""
    return (AnimationBuilder("level_up", AnimationType.LEVEL_UP, 2.0)
            .add_keyframe(0.0, {"scale": 1.0, "alpha": 1.0, "rotation": 0})
            .add_keyframe(0.2, {"scale": 0.5, "alpha": 1.0, "rotation": 0}, Easing.ease_in_back)
            .add_keyframe(0.5, {"scale": 1.3, "alpha": 1.0, "rotation": 180}, Easing.ease_out_elastic)
            .add_keyframe(0.8, {"scale": 1.0, "alpha": 1.0, "rotation": 360}, Easing.ease_out_quad)
            .add_keyframe(1.0, {"scale": 1.0, "alpha": 1.0, "rotation": 0})
            .build())


def create_evolution_animation() -> Animation:
    """Create an evolution animation."""
    return (AnimationBuilder("evolution", AnimationType.EVOLUTION, 3.0)
            .add_keyframe(0.0, {"scale": 1.0, "alpha": 1.0, "rotation": 0, "glow": 0})
            .add_keyframe(0.2, {"scale": 0.8, "alpha": 0.8, "rotation": 0, "glow": 0.2}, Easing.ease_in_quad)
            .add_keyframe(0.4, {"scale": 1.2, "alpha": 0.5, "rotation": 90, "glow": 0.5}, Easing.ease_in_out_quad)
            .add_keyframe(0.6, {"scale": 0.1, "alpha": 0, "rotation": 180, "glow": 1.0}, Easing.ease_in_cubic)
            .add_keyframe(0.8, {"scale": 1.5, "alpha": 1.0, "rotation": 360, "glow": 0.8}, Easing.ease_out_elastic)
            .add_keyframe(1.0, {"scale": 1.0, "alpha": 1.0, "rotation": 0, "glow": 0}, Easing.ease_out_quad)
            .build())


def create_happy_animation() -> Animation:
    """Create a happy animation."""
    return (AnimationBuilder("happy", AnimationType.HAPPY, 0.8)
            .add_keyframe(0.0, {"offset_y": 0, "rotation": 0})
            .add_keyframe(0.2, {"offset_y": -10, "rotation": -10}, Easing.ease_out_quad)
            .add_keyframe(0.4, {"offset_y": 0, "rotation": 10}, Easing.ease_in_out_quad)
            .add_keyframe(0.6, {"offset_y": -5, "rotation": -5}, Easing.ease_in_out_quad)
            .add_keyframe(0.8, {"offset_y": 0, "rotation": 0}, Easing.ease_out_quad)
            .build())


def create_shake_animation() -> Animation:
    """Create a shake animation."""
    return (AnimationBuilder("shake", AnimationType.SHAKE, 0.4)
            .add_keyframe(0.0, {"offset_x": 0})
            .add_keyframe(0.1, {"offset_x": -10}, Easing.linear)
            .add_keyframe(0.2, {"offset_x": 10}, Easing.linear)
            .add_keyframe(0.3, {"offset_x": -10}, Easing.linear)
            .add_keyframe(0.4, {"offset_x": 0}, Easing.ease_out_quad)
            .build())


def create_spin_animation() -> Animation:
    """Create a spin animation."""
    return (AnimationBuilder("spin", AnimationType.SPIN, 0.8)
            .add_keyframe(0.0, {"rotation": 0, "scale": 1.0})
            .add_keyframe(0.5, {"rotation": 360, "scale": 0.8}, Easing.ease_in_out_quad)
            .add_keyframe(1.0, {"rotation": 720, "scale": 1.0}, Easing.ease_out_quad)
            .build())


def create_fade_in_animation(duration: float = 0.5) -> Animation:
    """Create a fade in animation."""
    return (AnimationBuilder("fade_in", AnimationType.FADE_IN, duration)
            .add_keyframe(0.0, {"alpha": 0.0})
            .add_keyframe(1.0, {"alpha": 1.0}, Easing.ease_out_quad)
            .build())


def create_fade_out_animation(duration: float = 0.5) -> Animation:
    """Create a fade out animation."""
    return (AnimationBuilder("fade_out", AnimationType.FADE_OUT, duration)
            .add_keyframe(0.0, {"alpha": 1.0})
            .add_keyframe(1.0, {"alpha": 0.0}, Easing.ease_in_quad)
            .build())


def create_dance_animation() -> Animation:
    """Create a dance animation."""
    return (AnimationBuilder("dance", AnimationType.DANCE, 2.0)
            .add_keyframe(0.0, {"offset_y": 0, "offset_x": 0, "rotation": 0, "scale": 1.0})
            .add_keyframe(0.2, {"offset_y": -15, "offset_x": 10, "rotation": 15, "scale": 1.1}, Easing.ease_in_out_quad)
            .add_keyframe(0.4, {"offset_y": 0, "offset_x": 0, "rotation": 0, "scale": 1.0}, Easing.ease_in_out_quad)
            .add_keyframe(0.6, {"offset_y": -15, "offset_x": -10, "rotation": -15, "scale": 1.1}, Easing.ease_in_out_quad)
            .add_keyframe(0.8, {"offset_y": 0, "offset_x": 0, "rotation": 0, "scale": 1.0}, Easing.ease_in_out_quad)
            .add_keyframe(1.0, {"offset_y": -10, "offset_x": 0, "rotation": 0, "scale": 1.05}, Easing.ease_in_out_quad)
            .add_keyframe(1.2, {"offset_y": 0, "offset_x": 0, "rotation": 360, "scale": 1.0}, Easing.ease_in_out_cubic)
            .set_loop(True, 0.3)
            .build())


def create_wave_animation() -> Animation:
    """Create a waving animation."""
    return (AnimationBuilder("wave", AnimationType.WAVE, 1.0)
            .add_keyframe(0.0, {"rotation": 0, "offset_x": 0})
            .add_keyframe(0.2, {"rotation": 0, "offset_x": 0})
            .add_keyframe(0.4, {"rotation": 20, "offset_x": 5}, Easing.ease_in_out_quad)
            .add_keyframe(0.6, {"rotation": -10, "offset_x": 5}, Easing.ease_in_out_quad)
            .add_keyframe(0.8, {"rotation": 20, "offset_x": 5}, Easing.ease_in_out_quad)
            .add_keyframe(1.0, {"rotation": 0, "offset_x": 0}, Easing.ease_out_quad)
            .build())


# ============================================================================
# Animation Library
# ============================================================================

class AnimationLibrary:
    """
    Library of predefined animations.
    """

    def __init__(self):
        self._animations: Dict[str, Animation] = {}
        self._register_defaults()

    def _register_defaults(self):
        """Register default animations."""
        defaults = [
            create_idle_animation(),
            create_bounce_animation(),
            create_walk_animation(),
            create_eat_animation(),
            create_sleep_animation(),
            create_level_up_animation(),
            create_evolution_animation(),
            create_happy_animation(),
            create_shake_animation(),
            create_spin_animation(),
            create_fade_in_animation(),
            create_fade_out_animation(),
            create_dance_animation(),
            create_wave_animation(),
        ]

        for anim in defaults:
            self._animations[anim.name] = anim

    def register(self, animation: Animation) -> None:
        """Register a custom animation."""
        self._animations[animation.name] = animation

    def get(self, name: str) -> Optional[Animation]:
        """Get an animation by name."""
        return self._animations.get(name)

    def get_by_type(self, anim_type: AnimationType) -> List[Animation]:
        """Get all animations of a specific type."""
        return [a for a in self._animations.values() if a.animation_type == anim_type]

    def get_all(self) -> List[Animation]:
        """Get all registered animations."""
        return list(self._animations.values())

    def create_custom(self, name: str, anim_type: AnimationType, duration: float) -> AnimationBuilder:
        """Create a custom animation using the builder."""
        return AnimationBuilder(name, anim_type, duration)


# Global animation library
_default_library: Optional[AnimationLibrary] = None


def get_animation_library() -> AnimationLibrary:
    """Get the global animation library."""
    global _default_library
    if _default_library is None:
        _default_library = AnimationLibrary()
    return _default_library


__all__ = [
    # Enums
    "AnimationType",
    "Easing",
    # Classes
    "Keyframe",
    "Animation",
    "AnimationBuilder",
    "AnimationLibrary",
    # Animation creators
    "create_idle_animation",
    "create_bounce_animation",
    "create_walk_animation",
    "create_eat_animation",
    "create_sleep_animation",
    "create_level_up_animation",
    "create_evolution_animation",
    "create_happy_animation",
    "create_shake_animation",
    "create_spin_animation",
    "create_fade_in_animation",
    "create_fade_out_animation",
    "create_dance_animation",
    "create_wave_animation",
    # Functions
    "get_animation_library",
]
