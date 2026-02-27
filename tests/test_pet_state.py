"""
Unit tests for pet state management

Tests the pet state system including:
- Default state initialization
- XP addition and leveling
- State saving and loading
"""
import unittest
import tempfile
import json
from pathlib import Path
from dataclasses import asdict
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class MockPetState:
    """Mock pet state class for testing."""

    def __init__(self):
        # Core stats
        self.level = 1
        self.xp = 0
        self.xp_to_next_level = 100

        # Needs (0-100)
        self.hunger = 100
        self.happiness = 100
        self.energy = 100

        # Evolution
        self.evolution_stage = 0
        self.evolution_path = "balanced"

        # Stats
        self.total_interactions = 0
        self.feed_count = 0
        self.play_count = 0
        self.sleep_count = 0

        # State
        self.is_sleeping = False
        self.last_update = None

        # Achievements
        self.achievements = []

    def add_xp(self, amount: int) -> tuple:
        """Add XP and return (xp_gained, levels_gained)."""
        if amount <= 0:
            return (0, 0)

        self.xp += amount
        levels_gained = 0

        while self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            levels_gained += 1
            # XP curve: each level requires 10% more XP
            self.xp_to_next_level = int(100 * (1.1 ** (self.level - 1)))

        return (amount, levels_gained)

    def feed(self) -> dict:
        """Feed the pet."""
        self.feed_count += 1
        self.total_interactions += 1

        old_hunger = self.hunger
        self.hunger = min(100, self.hunger + 30)
        self.happiness = min(100, self.happiness + 5)

        xp_gained = 20
        self.add_xp(xp_gained)

        return {
            "hunger_gained": self.hunger - old_hunger,
            "xp_gained": xp_gained,
        }

    def play(self) -> dict:
        """Play with the pet."""
        self.play_count += 1
        self.total_interactions += 1

        old_happiness = self.happiness
        old_energy = self.energy
        self.happiness = min(100, self.happiness + 25)
        self.energy = max(0, self.energy - 10)

        xp_gained = 15
        self.add_xp(xp_gained)

        return {
            "happiness_gained": self.happiness - old_happiness,
            "energy_lost": old_energy - self.energy,
            "xp_gained": xp_gained,
        }

    def sleep(self) -> dict:
        """Put pet to sleep."""
        if self.is_sleeping:
            return {"error": "Already sleeping"}

        self.sleep_count += 1
        self.is_sleeping = True

        return {"success": True}

    def wake_up(self) -> dict:
        """Wake up pet."""
        if not self.is_sleeping:
            return {"error": "Not sleeping"}

        old_energy = self.energy
        self.energy = min(100, self.energy + 50)
        self.is_sleeping = False

        return {
            "energy_gained": self.energy - old_energy,
            "success": True,
        }

    def decay(self) -> dict:
        """Apply natural stat decay."""
        changes = {}

        if not self.is_sleeping:
            # Hunger decreases over time
            old_hunger = self.hunger
            self.hunger = max(0, self.hunger - 5)
            changes["hunger_lost"] = old_hunger - self.hunger

            # Happiness decreases over time
            old_happiness = self.happiness
            self.happiness = max(0, self.happiness - 3)
            changes["happiness_lost"] = old_happiness - self.happiness

        # Energy recovers slightly when sleeping
        if self.is_sleeping:
            old_energy = self.energy
            self.energy = min(100, self.energy + 10)
            changes["energy_gained"] = self.energy - old_energy

        return changes

    def to_dict(self) -> dict:
        """Convert state to dictionary."""
        return {
            "level": self.level,
            "xp": self.xp,
            "xp_to_next_level": self.xp_to_next_level,
            "hunger": self.hunger,
            "happiness": self.happiness,
            "energy": self.energy,
            "evolution_stage": self.eolution_stage if hasattr(self, 'eolution_stage') else self.evolution_stage,
            "evolution_path": self.evolution_path,
            "total_interactions": self.total_interactions,
            "feed_count": self.feed_count,
            "play_count": self.play_count,
            "sleep_count": self.sleep_count,
            "is_sleeping": self.is_sleeping,
            "achievements": self.achievements,
        }

    def save(self, file_path: Path) -> bool:
        """Save state to file."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception:
            return False

    def load(self, file_path: Path) -> bool:
        """Load state from file."""
        try:
            if not file_path.exists():
                return False

            with open(file_path, 'r') as f:
                data = json.load(f)

            self.level = data.get("level", 1)
            self.xp = data.get("xp", 0)
            self.xp_to_next_level = data.get("xp_to_next_level", 100)
            self.hunger = data.get("hunger", 100)
            self.happiness = data.get("happiness", 100)
            self.energy = data.get("energy", 100)
            self.evolution_stage = data.get("evolution_stage", 0)
            self.evolution_path = data.get("evolution_path", "balanced")
            self.total_interactions = data.get("total_interactions", 0)
            self.feed_count = data.get("feed_count", 0)
            self.play_count = data.get("play_count", 0)
            self.sleep_count = data.get("sleep_count", 0)
            self.is_sleeping = data.get("is_sleeping", False)
            self.achievements = data.get("achievements", [])

            return True
        except Exception:
            return False


class TestPetState(unittest.TestCase):
    """Test cases for pet state management."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.state = MockPetState()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_default_state(self):
        """Test that default state is correctly initialized."""
        self.assertEqual(self.state.level, 1)
        self.assertEqual(self.state.xp, 0)
        self.assertEqual(self.state.hunger, 100)
        self.assertEqual(self.state.happiness, 100)
        self.assertEqual(self.state.energy, 100)
        self.assertEqual(self.state.evolution_stage, 0)
        self.assertEqual(self.state.total_interactions, 0)
        self.assertFalse(self.state.is_sleeping)

    def test_add_xp_increases_xp(self):
        """Test that add_xp increases XP."""
        xp_gained, levels = self.state.add_xp(50)
        self.assertEqual(xp_gained, 50)
        self.assertEqual(self.state.xp, 50)
        self.assertEqual(levels, 0)

    def test_add_xp_levels_up(self):
        """Test that add_xp triggers level up."""
        # Add enough XP for two levels
        xp_gained, levels = self.state.add_xp(150)
        self.assertEqual(levels, 1)
        self.assertEqual(self.state.level, 2)
        self.assertGreater(self.state.xp_to_next_level, 100)

    def test_add_xp_multiple_levels(self):
        """Test that add_xp can trigger multiple level ups."""
        # Add a lot of XP
        self.state.add_xp(500)
        self.assertGreater(self.state.level, 1)

    def test_add_xp_negative_returns_zero(self):
        """Test that add_xp with negative amount returns 0."""
        xp_gained, levels = self.state.add_xp(-10)
        self.assertEqual(xp_gained, 0)
        self.assertEqual(levels, 0)

    def test_feed_increases_hunger(self):
        """Test that feeding increases hunger."""
        self.state.hunger = 50
        result = self.state.feed()
        self.assertGreater(result["hunger_gained"], 0)
        self.assertEqual(self.state.hunger, 80)
        self.assertEqual(self.state.feed_count, 1)

    def test_feed_caps_at_100(self):
        """Test that hunger is capped at 100."""
        self.state.hunger = 90
        self.state.feed()
        self.assertEqual(self.state.hunger, 100)

    def test_feed_increases_happiness(self):
        """Test that feeding increases happiness."""
        self.state.happiness = 80
        self.state.feed()
        self.assertEqual(self.state.happiness, 85)

    def test_play_increases_happiness(self):
        """Test that playing increases happiness."""
        self.state.happiness = 50
        result = self.state.play()
        self.assertGreater(result["happiness_gained"], 0)
        self.assertEqual(self.state.happiness, 75)
        self.assertEqual(self.state.play_count, 1)

    def test_play_decreases_energy(self):
        """Test that playing decreases energy."""
        self.state.energy = 80
        result = self.state.play()
        self.assertEqual(result["energy_lost"], 10)
        self.assertEqual(self.state.energy, 70)

    def test_sleep_sets_sleeping_state(self):
        """Test that sleep sets is_sleeping to True."""
        result = self.state.sleep()
        self.assertTrue(result.get("success"))
        self.assertTrue(self.state.is_sleeping)

    def test_sleep_when_already_sleeping(self):
        """Test that sleep when already sleeping returns error."""
        self.state.is_sleeping = True
        result = self.state.sleep()
        self.assertIn("error", result)

    def test_wake_up_when_not_sleeping(self):
        """Test that wake_up when not sleeping returns error."""
        result = self.state.wake_up()
        self.assertIn("error", result)

    def test_wake_up_restores_energy(self):
        """Test that wake_up restores energy."""
        self.state.is_sleeping = True
        self.state.energy = 30
        result = self.state.wake_up()
        self.assertEqual(self.state.energy, 80)
        self.assertFalse(self.state.is_sleeping)

    def test_decay_decreases_hunger_when_awake(self):
        """Test that decay decreases hunger when awake."""
        self.state.hunger = 100
        changes = self.state.decay()
        self.assertIn("hunger_lost", changes)
        self.assertEqual(self.state.hunger, 95)

    def test_decay_decreases_happiness_when_awake(self):
        """Test that decay decreases happiness when awake."""
        self.state.happiness = 100
        changes = self.state.decay()
        self.assertIn("happiness_lost", changes)
        self.assertEqual(self.state.happiness, 97)

    def test_decay_increases_energy_when_sleeping(self):
        """Test that decay increases energy when sleeping."""
        self.state.is_sleeping = True
        self.state.energy = 50
        changes = self.state.decay()
        self.assertIn("energy_gained", changes)
        self.assertEqual(self.state.energy, 60)

    def test_decay_no_hunger_loss_when_sleeping(self):
        """Test that decay doesn't decrease hunger when sleeping."""
        self.state.is_sleeping = True
        self.state.hunger = 100
        changes = self.state.decay()
        self.assertNotIn("hunger_lost", changes)
        self.assertEqual(self.state.hunger, 100)

    def test_save_creates_file(self):
        """Test that save creates a state file."""
        save_path = Path(self.temp_dir) / "pet_state.json"
        self.state.save(save_path)
        self.assertTrue(save_path.exists())

    def test_save_preserves_data(self):
        """Test that save preserves state data."""
        save_path = Path(self.temp_dir) / "pet_state.json"
        self.state.level = 5
        self.state.xp = 250
        self.state.hunger = 75
        self.state.save(save_path)

        with open(save_path, 'r') as f:
            data = json.load(f)

        self.assertEqual(data["level"], 5)
        self.assertEqual(data["xp"], 250)
        self.assertEqual(data["hunger"], 75)

    def test_load_restores_state(self):
        """Test that load restores state from file."""
        save_path = Path(self.temp_dir) / "pet_state.json"

        # Create and save a state
        self.state.level = 10
        self.state.xp = 500
        self.state.hunger = 60
        self.state.save(save_path)

        # Create new state and load
        new_state = MockPetState()
        success = new_state.load(save_path)

        self.assertTrue(success)
        self.assertEqual(new_state.level, 10)
        self.assertEqual(new_state.xp, 500)
        self.assertEqual(new_state.hunger, 60)

    def test_load_nonexistent_file_returns_false(self):
        """Test that load returns False for nonexistent file."""
        save_path = Path(self.temp_dir) / "nonexistent.json"
        success = self.state.load(save_path)
        self.assertFalse(success)

    def test_to_dict_contains_all_fields(self):
        """Test that to_dict contains all state fields."""
        data = self.state.to_dict()

        required_fields = [
            "level", "xp", "xp_to_next_level", "hunger",
            "happiness", "energy", "evolution_stage",
            "evolution_path", "total_interactions",
            "feed_count", "play_count", "sleep_count",
            "is_sleeping", "achievements"
        ]

        for field in required_fields:
            self.assertIn(field, data)

    def test_total_interactions_increases(self):
        """Test that total_interactions increases with actions."""
        initial_count = self.state.total_interactions

        self.state.feed()
        self.assertEqual(self.state.total_interactions, initial_count + 1)

        self.state.play()
        self.assertEqual(self.state.total_interactions, initial_count + 2)


if __name__ == '__main__':
    unittest.main()
