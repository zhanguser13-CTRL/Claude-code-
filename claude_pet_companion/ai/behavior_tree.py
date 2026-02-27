"""
Behavior Tree AI System for Claude Pet Companion

Provides intelligent, hierarchical AI decision-making with:
- Behavior tree nodes (selector, sequence, decorator, action, condition)
- Priority-based behavior selection
- Reactive and goal-oriented behaviors
- Extensible node types
- State management
"""

import logging
import random
import time
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class NodeStatus(Enum):
    """Status of a behavior node execution."""
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"
    INVALID = "invalid"


@dataclass
class BehaviorContext:
    """Context passed to behavior nodes."""
    # Pet state
    pet: Any = None  # Reference to pet object

    # Environment
    time_of_day: str = "day"  # morning, day, evening, night
    weather: str = "clear"

    # Last action
    last_action: str = ""
    last_action_time: float = 0

    # Current needs
    hunger: float = 50.0  # 0-100
    happiness: float = 50.0
    energy: float = 50.0
    health: float = 100.0

    # Social state
    owner_present: bool = False
    owner_attention: float = 0.0

    # Memory
    recent_events: List[str] = field(default_factory=list)

    # User data for custom behaviors
    blackboard: Dict[str, Any] = field(default_factory=dict)

    def get_need(self, need: str) -> float:
        """Get a need value (0-100)."""
        return getattr(self, need, 50.0)

    def set_need(self, need: str, value: float):
        """Set a need value (clamped 0-100)."""
        setattr(self, need, max(0, min(100, value)))

    def get_most_urgent_need(self) -> Tuple[str, float]:
        """Get the most urgent need (lowest value)."""
        needs = {
            'hunger': self.hunger,
            'happiness': self.happiness,
            'energy': self.energy,
            'health': self.health
        }
        most_urgent = min(needs.items(), key=lambda x: x[1])
        return most_urgent

    def add_event(self, event: str):
        """Add an event to recent history."""
        self.recent_events.append(event)
        if len(self.recent_events) > 20:
            self.recent_events.pop(0)


class BehaviorNode(ABC):
    """Base class for all behavior tree nodes."""

    def __init__(self, name: str = ""):
        self.name = name or self.__class__.__name__
        self.parent: Optional['BehaviorNode'] = None
        self.children: List['BehaviorNode'] = []

    @abstractmethod
    def tick(self, context: BehaviorContext) -> NodeStatus:
        """Execute the node's behavior."""
        pass

    def add_child(self, child: 'BehaviorNode') -> 'BehaviorNode':
        """Add a child node."""
        child.parent = self
        self.children.append(child)
        return self

    def remove_child(self, child: 'BehaviorNode'):
        """Remove a child node."""
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    def reset(self):
        """Reset node state."""
        for child in self.children:
            child.reset()


class Selector(BehaviorNode):
    """
    Selector node: tries children in order until one succeeds.
    Returns: SUCCESS if any child succeeds, FAILURE if all fail
    """

    def __init__(self, name: str = "Selector"):
        super().__init__(name)
        self.current_child = 0

    def tick(self, context: BehaviorContext) -> NodeStatus:
        for i in range(self.current_child, len(self.children)):
            child = self.children[i]
            status = child.tick(context)

            if status == NodeStatus.RUNNING:
                self.current_child = i
                return NodeStatus.RUNNING

            if status == NodeStatus.SUCCESS:
                self.current_child = 0
                return NodeStatus.SUCCESS

        self.current_child = 0
        return NodeStatus.FAILURE

    def reset(self):
        self.current_child = 0
        super().reset()


class Sequence(BehaviorNode):
    """
    Sequence node: runs children in order until one fails.
    Returns: SUCCESS if all children succeed, FAILURE if any fail
    """

    def __init__(self, name: str = "Sequence"):
        super().__init__(name)
        self.current_child = 0

    def tick(self, context: BehaviorContext) -> NodeStatus:
        for i in range(self.current_child, len(self.children)):
            child = self.children[i]
            status = child.tick(context)

            if status == NodeStatus.RUNNING:
                self.current_child = i
                return NodeStatus.RUNNING

            if status == NodeStatus.FAILURE:
                self.current_child = 0
                return NodeStatus.FAILURE

        self.current_child = 0
        return NodeStatus.SUCCESS

    def reset(self):
        self.current_child = 0
        super().reset()


class Parallel(BehaviorNode):
    """
    Parallel node: runs all children simultaneously.
    Returns: SUCCESS if threshold children succeed, FAILURE if threshold fail
    """

    def __init__(self, name: str = "Parallel", success_threshold: int = 1):
        super().__init__(name)
        self.success_threshold = success_threshold

    def tick(self, context: BehaviorContext) -> NodeStatus:
        success_count = 0
        failure_count = 0
        running_count = 0

        for child in self.children:
            status = child.tick(context)

            if status == NodeStatus.SUCCESS:
                success_count += 1
            elif status == NodeStatus.FAILURE:
                failure_count += 1
            else:
                running_count += 1

        if success_count >= self.success_threshold:
            return NodeStatus.SUCCESS
        if failure_count > len(self.children) - self.success_threshold:
            return NodeStatus.FAILURE
        return NodeStatus.RUNNING


class Condition(BehaviorNode):
    """Condition node: checks a condition and returns SUCCESS or FAILURE."""

    def __init__(self, predicate: Callable[[BehaviorContext], bool],
                 name: str = "Condition"):
        super().__init__(name)
        self.predicate = predicate

    def tick(self, context: BehaviorContext) -> NodeStatus:
        if self.predicate(context):
            return NodeStatus.SUCCESS
        return NodeStatus.FAILURE


class Action(BehaviorNode):
    """Action node: performs an action."""

    def __init__(self, action_fn: Callable[[BehaviorContext], NodeStatus],
                 name: str = "Action"):
        super().__init__(name)
        self.action_fn = action_fn
        self.started = False
        self.start_time = 0

    def tick(self, context: BehaviorContext) -> NodeStatus:
        if not self.started:
            self.start_time = time.time()
            self.started = True

        return self.action_fn(context)

    def reset(self):
        self.started = False
        self.start_time = 0
        super().reset()


class Decorator(BehaviorNode):
    """Base decorator node that wraps a single child."""

    def __init__(self, child: BehaviorNode = None, name: str = "Decorator"):
        super().__init__(name)
        if child:
            self.add_child(child)

    @abstractmethod
    def tick(self, context: BehaviorContext) -> NodeStatus:
        pass


class Inverter(Decorator):
    """Inverts the result of its child."""

    def tick(self, context: BehaviorContext) -> NodeStatus:
        if not self.children:
            return NodeStatus.FAILURE

        status = self.children[0].tick(context)

        if status == NodeStatus.SUCCESS:
            return NodeStatus.FAILURE
        if status == NodeStatus.FAILURE:
            return NodeStatus.SUCCESS
        return status


class Repeater(Decorator):
    """Repeats its child N times or indefinitely."""

    def __init__(self, child: BehaviorNode = None, repeat_count: int = -1,
                 name: str = "Repeater"):
        super().__init__(child, name)
        self.repeat_count = repeat_count
        self.current_count = 0

    def tick(self, context: BehaviorContext) -> NodeStatus:
        if not self.children:
            return NodeStatus.FAILURE

        while True:
            status = self.children[0].tick(context)

            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING

            if status == NodeStatus.FAILURE:
                self.current_count = 0
                return NodeStatus.FAILURE

            self.current_count += 1

            if self.repeat_count > 0 and self.current_count >= self.repeat_count:
                self.current_count = 0
                return NodeStatus.SUCCESS

    def reset(self):
        self.current_count = 0
        super().reset()


class Retry(Decorator):
    """Retries child on failure up to N times."""

    def __init__(self, child: BehaviorNode = None, max_attempts: int = 3,
                 name: str = "Retry"):
        super().__init__(child, name)
        self.max_attempts = max_attempts
        self.current_attempt = 0

    def tick(self, context: BehaviorContext) -> NodeStatus:
        if not self.children:
            return NodeStatus.FAILURE

        while self.current_attempt < self.max_attempts:
            status = self.children[0].tick(context)

            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING

            if status == NodeStatus.SUCCESS:
                self.current_attempt = 0
                return NodeStatus.SUCCESS

            self.current_attempt += 1

        self.current_attempt = 0
        return NodeStatus.FAILURE

    def reset(self):
        self.current_attempt = 0
        super().reset()


class Cooldown(Decorator):
    """Adds cooldown between child executions."""

    def __init__(self, child: BehaviorNode = None, cooldown: float = 1.0,
                 name: str = "Cooldown"):
        super().__init__(child, name)
        self.cooldown = cooldown
        self.last_execution = 0

    def tick(self, context: BehaviorContext) -> NodeStatus:
        if not self.children:
            return NodeStatus.FAILURE

        now = time.time()
        if now - self.last_execution < self.cooldown:
            return NodeStatus.FAILURE

        status = self.children[0].tick(context)

        if status != NodeStatus.RUNNING:
            self.last_execution = now

        return status


class Probability(Decorator):
    """Randomly succeeds or fails before running child."""

    def __init__(self, child: BehaviorNode = None, success_chance: float = 0.5,
                 name: str = "Probability"):
        super().__init__(child, name)
        self.success_chance = success_chance

    def tick(self, context: BehaviorContext) -> NodeStatus:
        if random.random() > self.success_chance:
            return NodeStatus.FAILURE

        if not self.children:
            return NodeStatus.SUCCESS

        return self.children[0].tick(context)


class BehaviorTree:
    """Main behavior tree class."""

    def __init__(self, root: BehaviorNode, name: str = "BehaviorTree"):
        self.root = root
        self.name = name
        self.context = BehaviorContext()
        self.last_update = 0

    def update(self, dt: float = 0) -> NodeStatus:
        """Update the behavior tree."""
        self.last_update = time.time()
        return self.root.tick(self.context)

    def reset(self):
        """Reset the behavior tree."""
        self.root.reset()

    def set_context(self, **kwargs):
        """Update context values."""
        for key, value in kwargs.items():
            setattr(self.context, key, value)


# Common behavior conditions

def hunger_is_critical(context: BehaviorContext) -> bool:
    """Check if hunger is critically low."""
    return context.hunger < 20


def hunger_is_low(context: BehaviorContext) -> bool:
    """Check if hunger is low."""
    return context.hunger < 40


def energy_is_low(context: BehaviorContext) -> bool:
    """Check if energy is low."""
    return context.energy < 30


def happiness_is_low(context: BehaviorContext) -> bool:
    """Check if happiness is low."""
    return context.happiness < 30


def health_is_low(context: BehaviorContext) -> bool:
    """Check if health is low."""
    return context.health < 50


def owner_is_present(context: BehaviorContext) -> bool:
    """Check if owner is present."""
    return context.owner_present


def is_nighttime(context: BehaviorContext) -> bool:
    """Check if it's nighttime."""
    return context.time_of_day in ("evening", "night")


def is_daytime(context: BehaviorContext) -> bool:
    """Check if it's daytime."""
    return context.time_of_day in ("morning", "day")


# Common behavior actions

def eat_action(context: BehaviorContext) -> NodeStatus:
    """Eat to restore hunger."""
    context.hunger = min(100, context.hunger + 30)
    context.add_event("ate_food")
    logger.info(f"{context.pet.name if context.pet else 'Pet'} ate food. Hunger: {context.hunger}")
    return NodeStatus.SUCCESS


def sleep_action(context: BehaviorContext) -> NodeStatus:
    """Sleep to restore energy."""
    context.energy = min(100, context.energy + 20)
    context.add_event("slept")
    logger.info(f"{context.pet.name if context.pet else 'Pet'} slept. Energy: {context.energy}")
    return NodeStatus.SUCCESS


def play_action(context: BehaviorContext) -> NodeStatus:
    """Play to increase happiness."""
    context.happiness = min(100, context.happiness + 15)
    context.energy = max(0, context.energy - 10)
    context.add_event("played")
    logger.info(f"{context.pet.name if context.pet else 'Pet'} played. Happiness: {context.happiness}")
    return NodeStatus.SUCCESS


def rest_action(context: BehaviorContext) -> NodeStatus:
    """Rest to slightly restore energy."""
    context.energy = min(100, context.energy + 5)
    context.add_event("rested")
    return NodeStatus.SUCCESS


def seek_attention_action(context: BehaviorContext) -> NodeStatus:
    """Seek attention from owner."""
    context.owner_attention = min(100, context.owner_attention + 20)
    context.happiness = min(100, context.happiness + 10)
    context.add_event("sought_attention")
    return NodeStatus.SUCCESS


def idle_action(context: BehaviorContext) -> NodeStatus:
    """Do nothing (idle)."""
    return NodeStatus.SUCCESS


def wander_action(context: BehaviorContext) -> NodeStatus:
    """Wander around randomly."""
    context.add_event("wandered")
    return NodeStatus.SUCCESS


# Preset behavior trees

def create_pet_behavior_tree() -> BehaviorTree:
    """Create a standard pet behavior tree."""

    # Survival behaviors (highest priority)
    survival = Selector("Survival")

    # Health critical
    health_check = Sequence("HealthCheck")
    health_check.add_child(Condition(health_is_low, "HealthLow"))
    health_check.add_child(Action(rest_action, "Rest"))
    survival.add_child(health_check)

    # Hunger critical
    hunger_critical = Sequence("HungerCritical")
    hunger_critical.add_child(Condition(hunger_is_critical, "HungerCritical"))
    hunger_critical.add_child(Action(eat_action, "Eat"))
    survival.add_child(hunger_critical)

    # Energy critical
    energy_critical = Sequence("EnergyCritical")
    energy_critical.add_child(Condition(energy_is_low, "EnergyLow"))
    energy_critical.add_child(Condition(is_nighttime, "IsNight"))
    energy_critical.add_child(Action(sleep_action, "Sleep"))
    survival.add_child(energy_critical)

    # Daily needs (medium priority)
    daily_needs = Selector("DailyNeeds")

    # Normal hunger
    normal_hunger = Sequence("NormalHunger")
    normal_hunger.add_child(Condition(hunger_is_low, "HungerLow"))
    normal_hunger.add_child(Action(eat_action, "Eat"))
    daily_needs.add_child(normal_hunger)

    # Social needs
    social = Selector("Social")

    seek_attention = Sequence("SeekAttention")
    seek_attention.add_child(Condition(happiness_is_low, "HappyLow"))
    seek_attention.add_child(Condition(owner_is_present, "OwnerPresent"))
    seek_attention.add_child(Action(seek_attention_action, "SeekAttention"))
    social.add_child(seek_attention)

    # Play time
    play = Sequence("Play")
    play.add_child(Condition(is_daytime, "IsDay"))
    play.add_child(Condition(owner_is_present, "OwnerPresent"))
    play.add_child(Action(play_action, "Play"))
    social.add_child(play)

    daily_needs.add_child(social)

    # Default behaviors (lowest priority)
    default = Selector("Default")
    default.add_child(Action(wander_action, "Wander"))
    default.add_child(Action(idle_action, "Idle"))

    # Main tree: try survival, then daily needs, then default
    main = Selector("MainBehavior")
    main.add_child(survival)
    main.add_child(daily_needs)
    main.add_child(default)

    return BehaviorTree(main, "PetBehaviorTree")


class BehaviorTreeBuilder:
    """Builder for creating complex behavior trees."""

    def __init__(self):
        self.root = None
        self.current = None
        self.stack = []

    def selector(self, name: str = "Selector") -> 'BehaviorTreeBuilder':
        """Start a selector node."""
        node = Selector(name)
        self._add_node(node)
        return self

    def sequence(self, name: str = "Sequence") -> 'BehaviorTreeBuilder':
        """Start a sequence node."""
        node = Sequence(name)
        self._add_node(node)
        return self

    def parallel(self, name: str = "Parallel", success_threshold: int = 1) -> 'BehaviorTreeBuilder':
        """Start a parallel node."""
        node = Parallel(name, success_threshold)
        self._add_node(node)
        return self

    def condition(self, predicate: Callable, name: str = "Condition") -> 'BehaviorTreeBuilder':
        """Add a condition node."""
        node = Condition(predicate, name)
        self._add_node(node)
        return self

    def action(self, action_fn: Callable, name: str = "Action") -> 'BehaviorTreeBuilder':
        """Add an action node."""
        node = Action(action_fn, name)
        self._add_node(node)
        return self

    def decorate(self, decorator: Decorator) -> 'BehaviorTreeBuilder':
        """Add a decorator node."""
        self._add_node(decorator)
        return self

    def repeat(self, count: int = -1) -> 'BehaviorTreeBuilder':
        """Repeat the previous child count times."""
        if self.current and self.current.children:
            child = self.current.children.pop()
            repeater = Repeater(child, count)
            self.current.add_child(repeater)
        return self

    def retry(self, max_attempts: int = 3) -> 'BehaviorTreeBuilder':
        """Retry the previous child on failure."""
        if self.current and self.current.children:
            child = self.current.children.pop()
            retry_node = Retry(child, max_attempts)
            self.current.add_child(retry_node)
        return self

    def cooldown(self, seconds: float = 1.0) -> 'BehaviorTreeBuilder':
        """Add cooldown to previous child."""
        if self.current and self.current.children:
            child = self.current.children.pop()
            cd = Cooldown(child, seconds)
            self.current.add_child(cd)
        return self

    def end(self) -> 'BehaviorTreeBuilder':
        """End the current composite node."""
        if self.stack:
            self.current = self.stack.pop()
        return self

    def _add_node(self, node: BehaviorNode):
        """Add a node to the current parent."""
        if self.root is None:
            self.root = node
            self.current = node
        elif self.current is not None:
            self.current.add_child(node)
            # If node is composite, make it current
            if isinstance(node, (Selector, Sequence, Parallel)):
                self.stack.append(self.current)
                self.current = node

    def build(self, name: str = "BehaviorTree") -> BehaviorTree:
        """Build the final behavior tree."""
        if self.root is None:
            raise ValueError("Cannot build empty behavior tree")
        return BehaviorTree(self.root, name)


# Convenience builder functions

def build_tree() -> BehaviorTreeBuilder:
    """Start building a behavior tree."""
    return BehaviorTreeBuilder()


if __name__ == "__main__":
    # Test behavior tree
    print("Testing Behavior Tree System")

    # Create a simple test context
    context = BehaviorContext()
    context.hunger = 10  # Very hungry!
    context.energy = 80
    context.happiness = 70
    context.owner_present = True
    context.time_of_day = "day"

    # Create behavior tree
    tree = create_pet_behavior_tree()
    tree.context = context

    print("\nPet behavior test:")
    print(f"Initial state: hunger={context.hunger}, energy={context.energy}, happiness={context.happiness}")

    # Run several ticks
    for i in range(5):
        status = tree.update()
        print(f"Tick {i+1}: status={status.value}, hunger={context.hunger:.0f}")

    print("\nBehavior tree test passed!")
