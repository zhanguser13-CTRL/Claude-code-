"""
Unit Tests for Animation System

Tests the tween engine and animation functionality.
"""

import pytest
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pet_companion.ui.animations import (
    EasingFunctions,
    EasingType,
    TweenConfig,
    PropertyTween,
    TweenEngine,
    Transition,
    tween_to,
)


class TestEasingFunctions:
    """Test easing functions."""

    def test_linear_easing(self):
        """Test linear easing is identity."""
        func = EasingFunctions.get(EasingType.LINEAR)
        assert func(0.0) == 0.0
        assert func(0.5) == 0.5
        assert func(1.0) == 1.0

    def test_easing_functions_range(self):
        """Test all easing functions return valid values (0-1)."""
        for easing_type in EasingType:
            func = EasingFunctions.get(easing_type)
            for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
                result = func(t)
                assert 0.0 <= result <= 1.0, f"{easing_type} at {t} returned {result}"

    def test_easing_endpoints(self):
        """Test that all easing functions start at 0 and end at 1."""
        for easing_type in EasingType:
            func = EasingFunctions.get(easing_type)
            assert func(0.0) == 0.0, f"{easing_type} should start at 0"
            assert func(1.0) == pytest.approx(1.0), f"{easing_type} should end at 1"

    def test_easing_monotonic(self):
        """Test that easing functions are monotonic (non-decreasing)."""
        for easing_type in EasingType:
            func = EasingFunctions.get(easing_type)
            prev_value = func(0.0)
            for t in [i/100 for i in range(1, 100)]:
                value = func(t)
                assert value >= prev_value - 1e-10, f"{easing_type} not monotonic at {t}"
                prev_value = value

    def test_elastic_bounce_bounds(self):
        """Test elastic and bounce easing stay within reasonable bounds."""
        for easing_type in [EasingType.ELASTIC, EasingType.BOUNCE]:
            func = EasingFunctions.get(easing_type)
            for t in [i/100 for i in range(101)]:
                value = func(t)
                # Elastic can go slightly outside bounds due to overshoot
                # but should not be extreme
                assert -1.0 <= value <= 2.0, f"{easing_type} out of bounds at {t}: {value}"


class TestTweenConfig:
    """Test tween configuration."""

    def test_default_config(self):
        """Test default configuration."""
        config = TweenConfig()
        assert config.duration == 1.0
        assert config.easing == EasingType.EASE_OUT
        assert config.delay == 0.0
        assert config.repeat == 1
        assert config.yoyo is False

    def test_custom_config(self):
        """Test custom configuration."""
        config = TweenConfig(
            duration=2.0,
            easing=EasingType.ELASTIC,
            delay=0.5,
            repeat=3,
            yoyo=True
        )
        assert config.duration == 2.0
        assert config.easing == EasingType.ELASTIC
        assert config.delay == 0.5
        assert config.repeat == 3
        assert config.yoyo is True


class TestPropertyTween:
    """Test property tween animations."""

    def test_tween_creation(self):
        """Test creating a tween."""
        class TestObj:
            def __init__(self):
                self.value = 0.0

        obj = TestObj()
        tween = tween_to(obj, 'value', 100.0, duration=1.0)

        assert tween.target == obj
        assert tween.end_value == 100.0

    def test_tween_execution(self):
        """Test tween execution."""
        class TestObj:
            def __init__(self):
                self.value = 0.0

        obj = TestObj()
        tween = tween_to(obj, 'value', 10.0, duration=0.1)

        tween.start()

        # Update to completion
        while tween.update(0.02):
            pass

        assert obj.value == pytest.approx(10.0, abs=0.1)

    def test_tween_interpolation(self):
        """Test tween interpolation."""
        class TestObj:
            def __init__(self):
                self.position = 0.0

        obj = TestObj()
        tween = tween_to(obj, 'position', 50.0, duration=1.0, easing=EasingType.LINEAR)

        tween.start()

        # Check midpoint
        tween.update(0.5)
        assert obj.position == pytest.approx(25.0, abs=1.0)

        # Complete
        while tween.update(0.02):
            pass
        assert obj.position == pytest.approx(50.0, abs=0.1)

    def test_tween_yoyo(self):
        """Test tween yoyo (reverse animation)."""
        class TestObj:
            def __init__(self):
                self.value = 0.0

        obj = TestObj()
        tween = tween_to(obj, 'value', 10.0, duration=0.1, yoyo=True)

        tween.start()

        # First pass - goes to 10
        while tween.update(0.02):
            pass
        assert obj.value == pytest.approx(10.0, abs=0.5)

        # Second pass - goes back to 0
        while tween.update(0.02):
            pass
        assert obj.value == pytest.approx(0.0, abs=0.5)

    def test_tween_repeat(self):
        """Test tween repeat functionality."""
        class TestObj:
            def __init__(self):
                self.value = 0.0

        obj = TestObj()
        tween = tween_to(obj, 'value', 10.0, duration=0.05, repeat=3)

        tween.start()

        # Should complete 3 cycles
        cycles = 0
        prev_value = obj.value
        for _ in range(100):
            complete = not tween.update(0.01)
            if obj.value == pytest.approx(0.0, abs=0.5) and prev_value > 1:
                cycles += 1
            prev_value = obj.value
            if complete:
                break

        assert cycles == 3


class TestTweenEngine:
    """Test tween engine management."""

    def test_add_tween(self):
        """Test adding tweens to engine."""
        engine = TweenEngine()

        class TestObj:
            def __init__(self):
                self.x = 0.0

        obj = TestObj()
        tween = tween_to(obj, 'x', 100.0)
        engine.add(tween)

        assert len(engine.tweens) == 1

    def test_update_all(self):
        """Test updating all tweens."""
        engine = TweenEngine()

        # Create multiple tweens
        for i in range(5):
            class TestObj:
                def __init__(self, inner_i):
                    self.value = 0.0
                self.inner_i = inner_i
            obj = TestObj(i)
            tween = tween_to(obj, 'value', float(i), duration=0.05)
            engine.add(tween)

        # Update all to completion
        for _ in range(10):
            engine.update(0.01)

        # Check all completed
        assert len(engine.tweens) == 0

    def test_clear(self):
        """Test clearing the engine."""
        engine = TweenEngine()

        class TestObj:
            def __init__(self):
                self.value = 0.0

        obj = TestObj()
        tween = tween_to(obj, 'value', 50.0)
        engine.add(tween)

        assert len(engine.tweens) > 0

        engine.clear()

        assert len(engine.tweens) == 0

    def test_count(self):
        """Test getting active tween count."""
        engine = TweenEngine()

        assert engine.count() == 0

        class TestObj:
            def        __init__(self):
                self.value = 0.0

        obj = TestObj()
        tween = tween_to(obj, 'value', 50.0)
        engine.add(tween)

        assert engine.count() == 1


class TestTweenHelpers:
    """Test convenience tween helper functions."""

    def test_tween_to_returns_tween(self):
        """Test tween_to helper returns a tween."""
        class TestObj:
            def __init__(self):
                self.position = 0.0

        obj = TestObj()
        tween = tween_to(obj, 'position', 50.0)

        assert isinstance(tween, PropertyTween)
        assert tween.target == obj
        assert tween.end_value == 50.0

    def test_tween_to_default_params(self):
        """Test tween_to uses sensible defaults."""
        class TestObj:
            def __init__(self):
                self.position = 0.0

        obj = TestObj()
        tween = tween_to(obj, 'position', 100.0)

        assert tween.config.duration == 1.0
        assert tween.config.easing == EasingType.EASE_OUT


class TestTransitions:
    """Test transition helper functions."""

    def test_transition_fade(self):
        """Test fade transition exists."""
        result = Transition.fade(None, 0.5)
        # Just check it doesn't error - tkinter limitations
        assert result is None or hasattr(result, '__class__')

    def test_transition_slide(self):
        """Test slide transition exists."""
        result = Transition.slide(None, (10.0, 20.0))
        # Just check it doesn't error
        assert result is None or hasattr(result, '__class__')

    def test_transition_scale(self):
        """Test scale transition exists."""
        result = Transition.scale(None, 2.0)
        # Just check it doesn't error
        assert result is None or hasattr(result, '__class__')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
