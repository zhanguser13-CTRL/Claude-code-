"""
StatsManager - Manages pet statistics with decay logic

Handles hunger, happiness, and energy stats with time-based decay.
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
from enum import Enum


class StatType(Enum):
    """Types of stats managed."""
    HUNGER = "hunger"
    HAPPINESS = "happiness"
    ENERGY = "energy"


class StatsManager:
    """Manages pet statistics with decay and restoration."""

    # Decay rates per hour
    DECAY_RATES = {
        StatType.HUNGER: 5,    # Loses 5 hunger per hour
        StatType.HAPPINESS: 3, # Loses 3 happiness per hour
        StatType.ENERGY: 4     # Loses 4 energy per hour when awake
    }

    # Sleep recovery rate per hour
    SLEEP_RECOVERY_RATE = 20

    # Critical thresholds
    CRITICAL_THRESHOLD = 20
    WARNING_THRESHOLD = 50

    def __init__(self, state=None):
        """Initialize stats manager with optional state reference."""
        self.state = state
        self.last_update = datetime.now()

    def update_time(self):
        """Update the last update time."""
        self.last_update = datetime.now()

    def calculate_decay(self, stat_type: StatType, hours_passed: float) -> int:
        """Calculate decay amount for a stat over time period."""
        if stat_type == StatType.ENERGY and self.state and self.state.is_sleeping:
            # Energy recovers during sleep
            return int(hours_passed * self.SLEEP_RECOVERY_RATE)

        decay_rate = self.DECAY_RATES.get(stat_type, 0)
        return int(hours_passed * decay_rate)

    def apply_decay(self, state, hours_passed: float = None):
        """Apply time-based decay to all stats."""
        if hours_passed is None:
            hours_passed = self._hours_since_last_update(state)

        for stat_type in StatType:
            current_value = getattr(state, stat_type.value)
            decay = self.calculate_decay(stat_type, hours_passed)

            if stat_type == StatType.ENERGY and state.is_sleeping:
                # Recover energy during sleep
                new_value = min(100, current_value + decay)
            else:
                # Apply normal decay
                new_value = max(0, current_value - decay)

            setattr(state, stat_type.value, new_value)

    def _hours_since_last_update(self, state) -> float:
        """Calculate hours passed since last update."""
        try:
            last_updated = datetime.fromisoformat(state.last_updated)
            now = datetime.now()
            delta = now - last_updated
            return max(0, delta.total_seconds() / 3600)
        except (ValueError, TypeError):
            return 0

    def get_status_level(self, value: int) -> str:
        """Get status level based on stat value."""
        if value <= self.CRITICAL_THRESHOLD:
            return "critical"
        elif value <= self.WARNING_THRESHOLD:
            return "warning"
        else:
            return "healthy"

    def needs_attention(self, state) -> Dict[str, bool]:
        """Check which stats need attention."""
        return {
            "hungry": getattr(state, "hunger") <= self.CRITICAL_THRESHOLD,
            "unhappy": getattr(state, "happiness") <= self.CRITICAL_THRESHOLD,
            "tired": getattr(state, "energy") <= self.CRITICAL_THRESHOLD
        }

    def feed(self, state, amount: int = 30) -> Dict[str, any]:
        """Feed the pet to restore hunger."""
        is_meal_time, meal_name = state.is_meal_time()

        # Meal time bonus
        if is_meal_time:
            bonus_amount = 15
            xp_bonus = 20
        else:
            bonus_amount = 0
            xp_bonus = 5

        total_amount = amount + bonus_amount
        new_hunger = state.modify_stat("hunger", total_amount)

        state.times_fed += 1
        state.last_meal_time = datetime.now().isoformat()
        state.last_interaction = datetime.now().isoformat()

        # Feeding also gives a small happiness boost
        state.modify_stat("happiness", 5)

        return {
            "new_hunger": new_hunger,
            "is_meal_time": is_meal_time,
            "meal_name": meal_name,
            "xp_bonus": xp_bonus
        }

    def play(self, state, amount: int = 25) -> Dict[str, any]:
        """Play with the pet to increase happiness."""
        new_happiness = state.modify_stat("happiness", amount)

        # Playing uses energy
        energy_cost = 10
        new_energy = state.modify_stat("energy", -energy_cost)

        state.times_played += 1
        state.last_interaction = datetime.now().isoformat()

        # Playing makes pet slightly hungry
        hunger_cost = 5
        new_hunger = state.modify_stat("hunger", -hunger_cost)

        return {
            "new_happiness": new_happiness,
            "energy_cost": energy_cost,
            "new_energy": new_energy,
            "hunger_cost": hunger_cost,
            "xp_bonus": 15
        }

    def sleep(self, state) -> Dict[str, any]:
        """Put the pet to sleep or wake it up."""
        if state.is_sleeping:
            # Wake up
            state.is_sleeping = False
            state.modify_stat("energy", -10)  # Wake up cost
            return {
                "action": "woke_up",
                "energy": state.energy
            }
        else:
            # Go to sleep
            state.is_sleeping = True
            state.times_slept += 1
            state.last_sleep_time = datetime.now().isoformat()

            # Immediate energy recovery
            recovered = min(100 - state.energy, 30)
            state.modify_stat("energy", recovered)

            return {
                "action": "fell_asleep",
                "energy_recovered": recovered,
                "new_energy": state.energy
            }

    def get_stat_emoji(self, stat_type: StatType, value: int) -> str:
        """Get emoji representation of stat level."""
        if value <= self.CRITICAL_THRESHOLD:
            emojis = {
                StatType.HUNGER: "🍽️",
                StatType.HAPPINESS: "😢",
                StatType.ENERGY: "😴"
            }
        elif value <= self.WARNING_THRESHOLD:
            emojis = {
                StatType.HUNGER: "🍪",
                StatType.HAPPINESS: "😐",
                StatType.ENERGY: "😪"
            }
        else:
            emojis = {
                StatType.HUNGER: "✅",
                StatType.HAPPINESS: "😊",
                StatType.ENERGY: "⚡"
            }
        return emojis.get(stat_type, "❓")

    def calculate_mood_from_stats(self, state) -> str:
        """Calculate pet's mood based on current stats."""
        hunger = state.hunger
        happiness = state.happiness
        energy = state.energy

        # Check for sleep
        if state.is_sleeping:
            return "sleepy"

        # Check critical conditions first
        if hunger <= 20:
            return "hungry"
        if energy <= 20:
            return "sleepy"

        # Check consecutive failures
        if state.consecutive_failures >= 3:
            return "worried"

        # Check consecutive successes
        if state.consecutive_successes >= 5:
            return "ecstatic"

        # Check overall state
        if happiness >= 80 and hunger >= 70 and energy >= 70:
            if happiness >= 95:
                return "excited"
            return "happy"

        if happiness <= 30:
            return "sad"

        # Default
        return "content"


# Convenience functions
def feed_pet(state, amount: int = 30) -> Dict[str, any]:
    """Feed the pet."""
    manager = StatsManager(state)
    return manager.feed(state, amount)


def play_with_pet(state, amount: int = 25) -> Dict[str, any]:
    """Play with the pet."""
    manager = StatsManager(state)
    return manager.play(state, amount)


def pet_sleep(state) -> Dict[str, any]:
    """Toggle pet sleep state."""
    manager = StatsManager(state)
    return manager.sleep(state)


def update_mood_from_stats(state):
    """Update pet mood based on current stats."""
    manager = StatsManager(state)
    new_mood = manager.calculate_mood_from_stats(state)
    state.update_mood(new_mood)
    return new_mood


if __name__ == "__main__":
    from pet_state import PetState

    # Test stats manager
    state = PetState()
    manager = StatsManager(state)

    print("Testing StatsManager")
    print(f"Initial hunger: {state.hunger}")

    result = manager.feed(state)
    print(f"After feeding: {result}")

    result = manager.play(state)
    print(f"After playing: {result}")

    result = manager.sleep(state)
    print(f"After sleep: {result}")
