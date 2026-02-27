"""
UI Animation System for Claude Pet Companion

Provides smooth animations for UI elements with:
- Easing functions (linear, ease-in, ease-out, elastic, bounce)
- Tween engine
- Animation sequences and groups
- Property animations
- Transition effects
"""

import math
import time
import tkinter as tk
from typing import Dict, List, Tuple, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import threading


class EasingType(Enum):
    """Types of easing functions."""
    LINEAR = "linear"
    EASE_IN = "ease-in"
    EASE_OUT = "ease-out"
    EASE_IN_OUT = "ease-in-out"
    EASE_IN_QUAD = "ease-in-quad"
    EASE_OUT_QUAD = "ease-out-quad"
    EASE_IN_OUT_QUAD = "ease-in-out-quad"
    EASE_IN_CUBIC = "ease-in-cubic"
    EASE_OUT_CUBIC = "ease-out-cubic"
    EASE_IN_OUT_CUBIC = "ease-in-out-cubic"
    EASE_IN_QUART = "ease-in-quart"
    EASE_OUT_QUART = "ease-out-quart"
    EASE_IN_OUT_QUART = "ease-in-out-quart"
    EASE_IN_QUINT = "ease-in-quint"
    EASE_OUT_QUINT = "ease-out-quint"
    EASE_IN_OUT_QUINT = "ease-in-out-quint"
    EASE_IN_SINE = "ease-in-sine"
    EASE_OUT_SINE = "ease-out-sine"
    EASE_IN_OUT_SINE = "ease-in-out-sine"
    EASE_IN_EXPO = "ease-in-expo"
    EASE_OUT_EXPO = "ease-out-expo"
    EASE_IN_OUT_EXPO = "ease-in-out-expo"
    EASE_IN_CIRC = "ease-in-circ"
    EASE_OUT_CIRC = "ease-out-circ"
    EASE_IN_OUT_CIRC = "ease-in-out-circ"
    EASE_IN_BACK = "ease-in-back"
    EASE_OUT_BACK = "ease-out-back"
    EASE_IN_OUT_BACK = "ease-in-out-back"
    ELASTIC = "elastic"
    BOUNCE = "bounce"


class EasingFunctions:
    """Collection of easing functions."""

    @staticmethod
    def linear(t: float) -> float:
        """Linear interpolation."""
        return t

    @staticmethod
    def ease_in_quad(t: float) -> float:
        """Quadratic ease-in."""
        return t * t

    @staticmethod
    def ease_out_quad(t: float) -> float:
        """Quadratic ease-out."""
        return t * (2 - t)

    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """Quadratic ease-in-out."""
        return 2 * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 2) / 2

    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """Cubic ease-in."""
        return t * t * t

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Cubic ease-out."""
        return 1 - math.pow(1 - t, 3)

    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Cubic ease-in-out."""
        return 4 * t * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 3) / 2

    @staticmethod
    def ease_in_quart(t: float) -> float:
        """Quartic ease-in."""
        return t * t * t * t

    @staticmethod
    def ease_out_quart(t: float) -> float:
        """Quartic ease-out."""
        return 1 - math.pow(1 - t, 4)

    @staticmethod
    def ease_in_out_quart(t: float) -> float:
        """Quartic ease-in-out."""
        return 8 * t * t * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 4) / 2

    @staticmethod
    def ease_in_quint(t: float) -> float:
        """Quintic ease-in."""
        return t * t * t * t * t

    @staticmethod
    def ease_out_quint(t: float) -> float:
        """Quintic ease-out."""
        return 1 - math.pow(1 - t, 5)

    @staticmethod
    def ease_in_out_quint(t: float) -> float:
        """Quintic ease-in-out."""
        return 16 * t * t * t * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 5) / 2

    @staticmethod
    def ease_in_sine(t: float) -> float:
        """Sine ease-in."""
        return 1 - math.cos((t * math.pi) / 2)

    @staticmethod
    def ease_out_sine(t: float) -> float:
        """Sine ease-out."""
        return math.sin((t * math.pi) / 2)

    @staticmethod
    def ease_in_out_sine(t: float) -> float:
        """Sine ease-in-out."""
        return -(math.cos(math.pi * t) - 1) / 2

    @staticmethod
    def ease_in_expo(t: float) -> float:
        """Exponential ease-in."""
        return 0 if t == 0 else math.pow(2, 10 * t - 10)

    @staticmethod
    def ease_out_expo(t: float) -> float:
        """Exponential ease-out."""
        return 1 if t == 1 else 1 - math.pow(2, -10 * t)

    @staticmethod
    def ease_in_out_expo(t: float) -> float:
        """Exponential ease-in-out."""
        if t == 0:
            return 0
        if t == 1:
            return 1
        if t < 0.5:
            return math.pow(2, 20 * t - 10) / 2
        return (2 - math.pow(2, -20 * t + 10)) / 2

    @staticmethod
    def ease_in_circ(t: float) -> float:
        """Circular ease-in."""
        return 1 - math.sqrt(1 - t * t)

    @staticmethod
    def ease_out_circ(t: float) -> float:
        """Circular ease-out."""
        return math.sqrt(1 - math.pow(t - 1, 2))

    @staticmethod
    def ease_in_out_circ(t: float) -> float:
        """Circular ease-in-out."""
        if t < 0.5:
            return (1 - math.sqrt(1 - 4 * t * t)) / 2
        return (math.sqrt(1 - math.pow(-2 * t + 2, 2)) + 1) / 2

    @staticmethod
    def ease_in_back(t: float) -> float:
        """Back ease-in."""
        c1 = 1.70158
        c3 = c1 + 1
        return c3 * t * t * t - c1 * t * t

    @staticmethod
    def ease_out_back(t: float) -> float:
        """Back ease-out."""
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * math.pow(t - 1, 3) + c1 * math.pow(t - 1, 2)

    @staticmethod
    def ease_in_out_back(t: float) -> float:
        """Back ease-in-out."""
        c1 = 1.70158
        c2 = c1 * 1.525
        if t < 0.5:
            return (math.pow(2 * t, 2) * ((c2 + 1) * 2 * t - c2)) / 2
        return (math.pow(2 * t - 2, 2) * ((c2 + 1) * (t * 2 - 2) + c2) + 2) / 2

    @staticmethod
    def elastic(t: float) -> float:
        """Elastic easing."""
        c4 = (2 * math.pi) / 3
        return 0 if t == 0 else 1 if t == 1 else -math.pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * c4)

    @staticmethod
    def bounce(t: float) -> float:
        """Bounce easing."""
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

    @classmethod
    def get(cls, easing: EasingType) -> Callable[[float], float]:
        """Get easing function by type."""
        mapping = {
            EasingType.LINEAR: cls.linear,
            EasingType.EASE_IN_QUAD: cls.ease_in_quad,
            EasingType.EASE_OUT_QUAD: cls.ease_out_quad,
            EasingType.EASE_IN_OUT_QUAD: cls.ease_in_out_quad,
            EasingType.EASE_IN_CUBIC: cls.ease_in_cubic,
            EasingType.EASE_OUT_CUBIC: cls.ease_out_cubic,
            EasingType.EASE_IN_OUT_CUBIC: cls.ease_in_out_cubic,
            EasingType.EASE_IN_QUART: cls.ease_in_quart,
            EasingType.EASE_OUT_QUART: cls.ease_out_quart,
            EasingType.EASE_IN_OUT_QUART: cls.ease_in_out_quart,
            EasingType.EASE_IN_QUINT: cls.ease_in_quint,
            EasingType.EASE_OUT_QUINT: cls.ease_out_quint,
            EasingType.EASE_IN_OUT_QUINT: cls.ease_in_out_quint,
            EasingType.EASE_IN_SINE: cls.ease_in_sine,
            EasingType.EASE_OUT_SINE: cls.ease_out_sine,
            EasingType.EASE_IN_OUT_SINE: cls.ease_in_out_sine,
            EasingType.EASE_IN_EXPO: cls.ease_in_expo,
            EasingType.EASE_OUT_EXPO: cls.ease_out_expo,
            EasingType.EASE_IN_OUT_EXPO: cls.ease_in_out_expo,
            EasingType.EASE_IN_CIRC: cls.ease_in_circ,
            EasingType.EASE_OUT_CIRC: cls.ease_out_circ,
            EasingType.EASE_IN_OUT_CIRC: cls.ease_in_out_circ,
            EasingType.EASE_IN_BACK: cls.ease_in_back,
            EasingType.EASE_OUT_BACK: cls.ease_out_back,
            EasingType.EASE_IN_OUT_BACK: cls.ease_in_out_back,
            EasingType.ELASTIC: cls.elastic,
            EasingType.BOUNCE: cls.bounce,
        }

        # Handle aliases
        aliases = {
            EasingType.EASE_IN: cls.ease_in_quad,
            EasingType.EASE_OUT: cls.ease_out_quad,
            EasingType.EASE_IN_OUT: cls.ease_in_out_quad,
        }

        return mapping.get(easing, aliases.get(easing, cls.linear))


@dataclass
class TweenConfig:
    """Configuration for a tween animation."""
    duration: float = 1.0  # Seconds
    easing: EasingType = EasingType.EASE_OUT
    delay: float = 0.0
    repeat: int = 1  # Number of times to repeat (0 = infinite)
    yoyo: bool = False  # Reverse animation on repeat
    on_start: Optional[Callable] = None
    on_update: Optional[Callable[[float], None]] = None  # Called with progress (0-1)
    on_complete: Optional[Callable] = None


@dataclass
class PropertyTween:
    """Animates a specific property of an object."""

    target: Any
    property_name: str
    start_value: Union[float, Tuple[float, ...]]
    end_value: Union[float, Tuple[float, ...]]
    config: TweenConfig = field(default_factory=TweenConfig)

    # Internal state
    _current_time: float = 0.0
    _repeat_count: int = 0
    _reversed: bool = False
    _playing: bool = True
    _completed: bool = False

    def start(self):
        """Start the animation."""
        self._current_time = 0.0
        self._repeat_count = 0
        self._reversed = False
        self._playing = True
        self._completed = False

        if self.config.on_start:
            self.config.on_start()

    def update(self, dt: float) -> bool:
        """
        Update animation. Returns False if animation is complete.

        Args:
            dt: Delta time in seconds
        """
        if self._completed or not self._playing:
            return False

        # Handle delay
        if self._current_time < self.config.delay:
            self._current_time += dt
            return True

        # Calculate actual animation time
        anim_time = self._current_time - self.config.delay
        progress = min(anim_time / self.config.duration, 1.0)

        # Apply easing
        easing_func = EasingFunctions.get(self.config.easing)
        eased = easing_func(progress)

        # Handle yoyo
        if self._reversed:
            eased = 1.0 - eased

        # Calculate current value
        current_value = self._interpolate(self.start_value, self.end_value, eased)

        # Apply to target
        setattr(self.target, self.property_name, current_value)

        # Call update callback
        if self.config.on_update:
            self.config.on_update(eased)

        # Check completion
        if progress >= 1.0:
            if self.config.yoyo:
                self._reversed = not self._reversed

            if self.config.repeat > 0:
                self._repeat_count += 1
                if self._repeat_count >= self.config.repeat:
                    self._completed = True
                    if self.config.on_complete:
                        self.config.on_complete()
                    return False
                else:
                    self._current_time = self.config.delay
                    return True
            elif self.config.repeat == 0:
                # Infinite repeat
                self._current_time = self.config.delay
                return True
            else:
                self._completed = True
                if self.config.on_complete:
                    self.config.on_complete()
                return False

        self._current_time += dt
        return True

    def _interpolate(self, start: Union[float, Tuple], end: Union[float, Tuple], t: float) -> Any:
        """Interpolate between start and end values."""
        if isinstance(start, (tuple, list)) and isinstance(end, (tuple, list)):
            return tuple(s + (e - s) * t for s, e in zip(start, end))
        return start + (end - start) * t

    def stop(self):
        """Stop the animation."""
        self._playing = False

    def is_complete(self) -> bool:
        """Check if animation is complete."""
        return self._completed

    def is_playing(self) -> bool:
        """Check if animation is playing."""
        return self._playing and not self._completed


class TweenEngine:
    """Manages and updates multiple tween animations."""

    def __init__(self):
        self.tweens: List[PropertyTween] = []
        self._running = False

    def add(self, tween: PropertyTween) -> PropertyTween:
        """Add a tween to the engine."""
        self.tweens.append(tween)
        tween.start()
        return tween

    def remove(self, tween: PropertyTween):
        """Remove a tween from the engine."""
        if tween in self.tweens:
            self.tweens.remove(tween)

    def update(self, dt: float) -> int:
        """
        Update all tweens.

        Returns:
            Number of active tweens
        """
        active_tweens = []
        for tween in self.tweens:
            if tween.update(dt):
                active_tweens.append(tween)

        self.tweens = active_tweens
        return len(self.tweens)

    def clear(self):
        """Remove all tweens."""
        self.tweens.clear()

    def count(self) -> int:
        """Get number of active tweens."""
        return len(self.tweens)


class Transition:
    """High-level transition for UI elements."""

    @staticmethod
    def fade(widget: tk.Widget, target_alpha: float,
             duration: float = 0.3,
             easing: EasingType = EasingType.EASE_OUT) -> PropertyTween:
        """
        Create a fade animation for a widget.

        Note: Tkinter doesn't support alpha on widgets natively.
        This simulates fade by changing stipple or works with canvas items.
        """
        # For canvas items, we can use alpha
        # For regular widgets, we'd need platform-specific approaches
        pass

    @staticmethod
    def slide(widget: tk.Widget, offset: Tuple[float, float],
              duration: float = 0.3,
              easing: EasingType = EasingType.EASE_OUT) -> PropertyTween:
        """Create a slide animation using place geometry."""
        current_x = widget.winfo_x()
        current_y = widget.winfo_y()

        target_x = current_x + offset[0]
        target_y = current_y + offset[1]

        # Store position in widget for animation
        widget._anim_x = current_x
        widget._anim_y = current_y

        config = TweenConfig(duration=duration, easing=easing)

        def update_pos(x, y):
            if widget.winfo_manager() == 'place':
                widget.place(x=x, y=y)
            else:
                widget._anim_x = x
                widget._anim_y = y

        # Create custom tween that handles place geometry
        return PropertyTween(
            target=widget,
            property_name='_anim_x',
            start_value=float(current_x),
            end_value=float(target_x),
            config=config
        )

    @staticmethod
    def scale(widget: tk.Widget, scale: float,
              duration: float = 0.3,
              easing: EasingType = EasingType.EASE_OUT) -> List[PropertyTween]:
        """Create a scale animation."""
        current_w = widget.winfo_width()
        current_h = widget.winfo_height()

        target_w = current_w * scale
        target_h = current_h * scale

        config = TweenConfig(duration=duration, easing=easing)

        tweens = []

        # We need to animate the widget's size
        # This requires custom handling based on the widget's pack/place/grid geometry
        return tweens

    @staticmethod
    def shake(widget: tk.Widget, intensity: float = 10.0,
              duration: float = 0.5) -> PropertyTween:
        """Create a shake animation."""
        current_x = widget.winfo_x()

        config = TweenConfig(
            duration=duration,
            easing=EasingType.EASE_OUT_SINE
        )

        # Custom shake animation
        return PropertyTween(
            target=widget,
            property_name='_anim_offset',
            start_value=0.0,
            end_value=0.0,
            config=config
        )


class AnimationSequence:
    """Sequence of animations played in order."""

    def __init__(self):
        self.animations: List[PropertyTween] = []
        self._current_index = 0
        self._completed = False

    def add(self, tween: PropertyTween) -> 'AnimationSequence':
        """Add an animation to the sequence."""
        self.animations.append(tween)
        return self

    def start(self):
        """Start the sequence."""
        self._current_index = 0
        self._completed = False

        if self.animations:
            self.animations[0].start()

    def update(self, dt: float) -> bool:
        """Update the current animation. Returns False if sequence complete."""
        if self._completed or not self.animations:
            return False

        current = self.animations[self._current_index]

        if current.update(dt):
            return True

        # Current animation complete, move to next
        self._current_index += 1

        if self._current_index >= len(self.animations):
            self._completed = False
            return False

        # Start next animation
        self.animations[self._current_index].start()
        return True

    def is_complete(self) -> bool:
        """Check if sequence is complete."""
        return self._completed


class AnimationGroup:
    """Group of animations played simultaneously."""

    def __init__(self):
        self.animations: List[PropertyTween] = []
        self._all_complete = False

    def add(self, tween: PropertyTween) -> 'AnimationGroup':
        """Add an animation to the group."""
        self.animations.append(tween)
        return self

    def start(self):
        """Start all animations in the group."""
        self._all_complete = False
        for tween in self.animations:
            tween.start()

    def update(self, dt: float) -> bool:
        """Update all animations. Returns False if all complete."""
        if self._all_complete:
            return False

        any_playing = False
        for tween in self.animations:
            if tween.update(dt):
                any_playing = True

        if not any_playing:
            self._all_complete = True
            return False

        return True

    def is_complete(self) -> bool:
        """Check if all animations are complete."""
        return all(t.is_complete() for t in self.animations)


# Convenience functions

def tween_to(target: Any, property_name: str, end_value: Any,
             duration: float = 1.0,
             easing: EasingType = EasingType.EASE_OUT,
             delay: float = 0.0,
             on_complete: Optional[Callable] = None) -> PropertyTween:
    """Create a simple tween animation."""
    start_value = getattr(target, property_name, end_value)

    config = TweenConfig(
        duration=duration,
        easing=easing,
        delay=delay,
        on_complete=on_complete
    )

    return PropertyTween(
        target=target,
        property_name=property_name,
        start_value=start_value,
        end_value=end_value,
        config=config
)


def animate(widget: tk.Widget, **kwargs) -> List[PropertyTween]:
    """
    Animate a widget with specified properties.

    Supported kwargs:
        x, y: Position
        width, height: Size
        alpha: Opacity (limited support in Tkinter)
        scale: Scale multiplier
    """
    tweens = []

    for prop, end_value in kwargs.items():
        if prop in ('x', 'y', 'width', 'height'):
            current = getattr(widget, f'_{prop}', widget.winfo_getattr(prop))
            tweens.append(tween_to(widget, prop, end_value))

    return tweens


if __name__ == "__main__":
    # Test animation system
    print("Testing UI Animation System")

    # Test easing functions
    import matplotlib.pyplot as plt
    import numpy as np

    t = np.linspace(0, 1, 100)

    fig, axes = plt.subplots(2, 2, figsize=(10, 10))

    easing_types = [
        (EasingType.LINEAR, axes[0, 0]),
        (EasingType.EASE_OUT_CUBIC, axes[0, 1]),
        (EasingType.ELASTIC, axes[1, 0]),
        (EasingType.BOUNCE, axes[1, 1]),
    ]

    for easing_type, ax in easing_types:
        func = EasingFunctions.get(easing_type)
        y = [func(val) for val in t]
        ax.plot(t, y)
        ax.set_title(easing_type.value)
        ax.grid(True)

    plt.tight_layout()
    plt.savefig('easing_test.png')
    print("Easing functions plotted to easing_test.png")

    # Test tween engine
    class TestObject:
        def __init__(self):
            self.value = 0.0

    obj = TestObject()
    tween = tween_to(obj, 'value', 100.0, duration=1.0, easing=EasingType.EASE_OUT_CUBIC)

    engine = TweenEngine()
    engine.add(tween)

    print("\nSimulating tween:")
    for i in range(65):
        engine.update(0.016)  # ~60 FPS
        if i % 10 == 0:
            print(f"  Frame {i}: value = {obj.value:.2f}")

    print("UI Animation System test passed!")
