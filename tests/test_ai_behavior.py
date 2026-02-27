"""
Unit Tests for AI Behavior System

Tests the behavior tree AI system.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pet_companion.ai.behavior_tree import (
    BehaviorContext,
    BehaviorTree,
    BehaviorNode,
    Selector,
    Sequence,
    Parallel,
    Condition,
    Action,
    Inverter,
    Repeater,
    Retry,
    Cooldown,
    Probability,
    BehaviorTreeBuilder,
    create_pet_behavior_tree,
    hunger_is_critical,
    hunger_is_low,
    energy_is_low,
    eat_action,
    sleep_action,
    play_action,
    idle_action
)


class TestBehaviorContext:
    """Test behavior context."""

    def test_creation(self):
        """Test creating a context."""
        context = BehaviorContext()
        assert context.hunger == 50.0
        assert context.energy == 50.0

    def test_get_most_urgent_need(self):
        """Test getting most urgent need."""
        context = BehaviorContext()
        context.hunger = 10
        context.energy = 80
        context.happiness = 30

        need, value = context.get_most_urgent_need()
        assert need == "hunger"
        assert value == 10.0

    def test_add_event(self):
        """Test adding events."""
        context = BehaviorContext()
        context.add_event("played")

        assert "played" in context.recent_events

    def test_set_need(self):
        """Test setting need values."""
        context = BehaviorContext()
        context.set_need("hunger", 25)

        assert context.hunger == 25

    def test_set_need_clamping(self):
        """Test that need values are clamped."""
        context = BehaviorContext()
        context.set_need("hunger", 150)

        assert context.hunger == 100
        context.set_need("hunger", -10)

        assert context.hunger == 0


class TestBehaviorNodes:
    """Test individual behavior nodes."""

    def test_selector_finds_first_success(self):
        """Test selector stops at first successful child."""
        root = Selector("test_selector")

        # Add three conditions
        child1 = Condition(lambda ctx: False)
        child2 = Condition(lambda ctx: True)
        child3 = Condition(lambda ctx: True)

        root.add_child(child1)
        root.add_child(child2)
        root.add_child(child3)

        context = BehaviorContext()
        status = root.tick(context)

        assert status.value == "success"  # Second child succeeds
        # First child was never executed (it would fail)

    def test_selector_fails_when_all_fail(self):
        """Test selector fails when all children fail."""
        root = Selector("test_selector")

        all_false = Condition(lambda ctx: False)
        root.add_child(all_false)
        root.add_child(all_false)

        context = BehaviorContext()
        status = root.tick(context)

        assert status.value == "failure"

    def test_sequence_all_success(self):
        """Test sequence succeeds when all children succeed."""
        root = Sequence("test_sequence")

        root.add_child(Condition(lambda ctx: True))
        root.add_child(Condition(lambda ctx: True))

        context = BehaviorContext()
        status = root.tick(context)

        assert status.value == "success"

    def test_sequence_fails_on_failure(self):
        """Test sequence fails on first failure."""
        root = Sequence("test_sequence")

        root.add_child(Condition(lambda ctx: True))
        root.add_child(Condition(lambda ctx: False))
        root.add_child(Condition(lambda ctx: True))

        context = BehaviorContext()
        status = root.tick(context)

        assert status.value == "failure"

    def test_action_executes(self):
        """Test action node executes function."""
        executed = []

        def test_action_fn(ctx):
            executed.append(ctx)
            return NodeStatus.SUCCESS

        action = Action(test_action_fn)
        context = BehaviorContext()

        status = action.tick(context)

        assert status.value == "success"
        assert len(executed) == 1
        assert executed[0] is context

    def test_inverter_inverts(self):
        """Test inverter inverts condition."""
        context = BehaviorContext()
        context.hunger = 50

        condition = Condition(lambda ctx: ctx.hunger < 30)
        inverter = Inverter(condition)
        status = inverter.tick(context)

        assert status.value == "success"  # Condition is False, inverted to True

    def test_repeater_repeats(self):
        """Test repeater repeats child N times."""
        call_count = [0]

        def test_action_fn(ctx):
            call_count[0] += 1
            return NodeStatus.SUCCESS

        action = Action(test_action_fn)
        repeater = Repeater(action, repeat_count=3)
        repeater.tick(BehaviorContext())

        assert call_count[0] == 3

    def test_retry_retries_on_failure(self):
        """Test retry retries on failure."""
        attempts = [0]

        def failing_action_fn(ctx):
            attempts[0] += 1
            if attempts[0] < 2:
                return NodeStatus.FAILURE
            return NodeStatus.SUCCESS

        action = Action(failing_action_fn)
        retry = Retry(action, max_attempts=3)
        context = BehaviorContext()

        status = retry.tick(context)

        assert status.value == "success"
        assert attempts[0] == 2


class TestBehaviorTree:
    """Test complete behavior trees."""

    def test_pet_tree_structure(self):
        """Test pet behavior tree has correct structure."""
        tree = create_pet_behavior_tree()

        assert isinstance(tree.root, (Selector, Sequence))

    def test_pet_tree_updates(self):
        """Test pet tree can be updated."""
        tree = create_pet_behavior_tree()
        tree.context.hunger = 5

        # Should trigger eat action
        tree.update()

        # Check hunger was restored
        assert tree.context.hunger > 5

    def test_behavior_tree_conditions(self):
        """Test behavior tree conditions work correctly."""
        tree = create_pet_behavior_tree()

        # Set critical hunger
        tree.context.hunger = 15
        tree.context.energy = 80
        tree.context.happiness = 70

        # Should result in eat action
        initial_hunger = tree.context.hunger
        tree.update()

        # Hunger should increase (eat action restores hunger)
        assert tree.context.hunger > initial_hunger

    def test_behavior_tree_sleep(self):
        """Test behavior tree handles sleep correctly."""
        tree = create_pet_behavior_tree()

        # Set conditions for sleep
        tree.context.energy = 20
        tree.context.time_of_day = "night"

        # Should result in sleep action
        initial_energy = tree.context.energy
        tree.update()

        # Energy should increase (sleep restores energy)
        assert tree.context.energy >= initial_energy

    def test_behavior_tree_play(self):
        """Test behavior tree handles play correctly."""
        tree = create_pet_behavior_tree()

        # Set conditions for play
        tree.context.hunger = 80
        tree.context.energy = 80
        tree.context.happiness = 40
        tree.context.time_of_day = "day"
        tree.context.owner_present = True

        # Should result in play action
        initial_happiness = tree.context.happiness
        tree.update()

        # Happiness should increase (play increases happiness)
        assert tree.context.happiness > initial_happiness

    def test_behavior_tree_idle(self):
        """Test behavior tree falls back to idle."""
        tree = create_pet_behavior_tree()

        # Set all needs satisfied
        tree.context.hunger = 90
        tree.context.energy = 90
        tree.context.happiness = 90

        # Should result in idle or wander
        tree.update()

        # Pet should still be alive


class TestBehaviorTreeBuilder:
    """Test behavior tree builder."""

    def test_simple_selector(self):
        """Test building a simple selector."""
        tree = (BehaviorTreeBuilder()
                 .selector("root")
                 .condition(lambda ctx: ctx.hunger < 30)
                 .action(lambda ctx: setattr(ctx, 'hunger', ctx.hunger + 10))
                 .build())

        context = BehaviorContext(hunger=20)
        tree.context = context

        status = tree.root.tick(context)

        assert status.value == "success"
        assert context.hunger == 30

    def test_simple_sequence(self):
        """Test building a simple sequence."""
        executed = []

        tree = (BehaviorTreeBuilder()
                 .sequence("root")
                 .action(lambda ctx: executed.append("step1"))
                 .action(lambda ctx: executed.append("step2"))
                 .build())

        context = BehaviorContext()
        tree.context = context

        status = tree.root.tick(context)

        assert status.value == "success"
        assert executed == ["step1", "step2"]

    def test_decorator_chain(self):
        """Test chaining decorators."""
        tree = (BehaviorTreeBuilder()
                 .selector("root")
                 .condition(lambda ctx: ctx.hunger > 50)
                 .retry(max_attempts=3)
                 .cooldown(seconds=1.0)
                 .action(lambda ctx: setattr(ctx, 'hunger', ctx.hunger + 5))
                 .build())

        context = BehaviorContext(hunger=70)
        tree.context = context

        status = tree.root.tick(context)

        # Should succeed (condition is True)
        assert status.value == "success"
        assert context.hunger == 75


# Test helper functions

class TestHelperFunctions:
    """Test helper functions."""

    def test_hunger_conditions(self):
        """Test hunger condition functions."""
        assert not hunger_is_critical({"hunger": 50})
        assert hunger_is_critical({"hunger": 15})
        assert hunger_is_low({"hunger": 30})

    def test_energy_conditions(self):
        """Test energy condition functions."""
        assert not energy_is_low({"energy": 50})
        assert energy_is_low({"energy": 20})

    def test_action_functions(self):
        """Test action functions."""
        context = BehaviorContext(hunger=50, energy=50)

        result = eat_action(context)
        assert result.value == "success"

        result = sleep_action(context)
        assert result.value == "success"

        result = play_action(context)
        assert result.value == "success"

        result = idle_action(context)
        assert result.value == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
