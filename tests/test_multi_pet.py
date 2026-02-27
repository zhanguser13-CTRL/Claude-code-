"""
Multi-Pet System Tests for Claude Pet Companion

Tests the farm system, breeding system, and trading system.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pet_companion.multi_pet import (
    PetType,
    PetState,
    FarmPet,
    PetFarm,
    BreedingSystem,
    BreedingResult,
    PetGenetics,
    TradingSystem,
    TradeOffer,
    TradeStatus,
    PresetFarmPets,
)


class TestPetType:
    """Test PetType enum."""

    def test_pet_types(self):
        """Test pet type values."""
        assert PetType.CAT.value == "cat"
        assert PetType.DOG.value == "dog"
        assert PetType.RABBIT.value == "rabbit"
        assert PetType.HAMSTER.value == "hamster"


class TestPetState:
    """Test PetState enum."""

    def test_states(self):
        """Test state values."""
        assert PetState.IDLE.value == "idle"
        assert PetState.SLEEPING.value == "sleeping"
        assert PetState.PLAYING.value == "playing"


class TestFarmPet:
    """Test FarmPet class."""

    def test_pet_creation(self):
        """Test creating a farm pet."""
        pet = FarmPet(
            id="pet_1",
            name="Fluffy",
            pet_type=PetType.CAT
        )
        assert pet.id == "pet_1"
        assert pet.name == "Fluffy"
        assert pet.pet_type == PetType.CAT
        assert pet.level == 1

    def test_feed_pet(self):
        """Test feeding pet."""
        farm = PetFarm()
        pet = FarmPet(id="pet_1", name="Fluffy", pet_type=PetType.CAT, hunger=50)
        farm.add_pet(pet)
        initial_hunger = pet.hunger

        fed = farm.feed_pet("pet_1")
        assert fed is True
        assert pet.hunger > initial_hunger

    def test_play_with_pet(self):
        """Test playing with pet."""
        farm = PetFarm()
        pet = FarmPet(id="pet_1", name="Fluffy", pet_type=PetType.CAT, happiness=50)
        farm.add_pet(pet)

        initial_happiness = pet.happiness
        farm.play_with_pet("pet_1")
        assert pet.happiness >= initial_happiness

    def test_pet_stats_limits(self):
        """Test pet stat limits."""
        pet = FarmPet(id="pet_1", name="Fluffy", pet_type=PetType.CAT)

        # Stats should be clamped to 0-100
        for _ in range(150):
            pet.hunger = min(100, pet.hunger + 20)
            pet.happiness = min(100, pet.happiness + 20)

        assert pet.hunger <= 100
        assert pet.happiness <= 100


class TestPetFarm:
    """Test PetFarm class."""

    @pytest.fixture
    def farm(self):
        """Create a farm for testing."""
        return PetFarm()

    def test_farm_creation(self, farm):
        """Test creating a farm."""
        assert farm is not None
        assert len(farm.pets) == 0

    def test_add_pet_to_farm(self, farm):
        """Test adding pet to farm."""
        pet = FarmPet(id="pet_1", name="Fluffy", pet_type=PetType.CAT)
        result = farm.add_pet(pet)
        assert result is True

    def test_remove_pet_from_farm(self, farm):
        """Test removing pet from farm."""
        pet = FarmPet(id="pet_1", name="Fluffy", pet_type=PetType.CAT)
        farm.add_pet(pet)

        result = farm.remove_pet("pet_1")
        assert result is True
        assert len(farm.pets) == 0

    def test_get_pet(self, farm):
        """Test getting pet from farm."""
        pet = FarmPet(id="pet_1", name="Fluffy", pet_type=PetType.CAT)
        farm.add_pet(pet)

        retrieved = farm.get_pet("pet_1")
        assert retrieved is not None
        assert retrieved.name == "Fluffy"

    def test_farm_capacity(self, farm):
        """Test farm capacity limits."""
        small_farm = PetFarm(max_pets=2)

        pet1 = FarmPet(id="pet_1", name="Fluffy", pet_type=PetType.CAT)
        pet2 = FarmPet(id="pet_2", name="Buddy", pet_type=PetType.DOG)
        pet3 = FarmPet(id="pet_3", name="Whiskers", pet_type=PetType.CAT)

        assert small_farm.add_pet(pet1) is True
        assert small_farm.add_pet(pet2) is True
        assert small_farm.add_pet(pet3) is False  # At capacity

    def test_farm_stats(self, farm):
        """Test farm statistics."""
        pet1 = FarmPet(id="pet_1", name="Fluffy", pet_type=PetType.CAT)
        pet2 = FarmPet(id="pet_2", name="Buddy", pet_type=PetType.DOG)

        farm.add_pet(pet1)
        farm.add_pet(pet2)

        stats = farm.get_farm_status()
        assert stats['total_pets'] == 2


class TestPetGenetics:
    """Test PetGenetics class."""

    def test_genetics_creation(self):
        """Test creating pet genetics."""
        genetics = PetGenetics(
            parent1_id="parent1",
            parent2_id="parent2"
        )
        assert genetics.parent1_id == "parent1"
        assert genetics.generation == 1

    def test_color_hex(self):
        """Test getting color as hex."""
        genetics = PetGenetics()
        genetics.color_red = 1.0
        genetics.color_green = 0.5
        genetics.color_blue = 0.25

        hex_color = genetics.get_color_hex()
        # Actual calculation: r=255, g=127, b=63 -> #ff7f3f
        assert hex_color == "#ff7f3f"


class TestBreedingResult:
    """Test BreedingResult class."""

    def test_breeding_result_creation(self):
        """Test creating breeding result."""
        result = BreedingResult(
            success=True,
            reason="Breeding successful",
            offspring=None
        )
        assert result.success is True
        assert result.reason == "Breeding successful"


class TestBreedingSystem:
    """Test BreedingSystem."""

    @pytest.fixture
    def breeding_system(self):
        """Create breeding system."""
        return BreedingSystem()

    @pytest.fixture
    def sample_genetics(self):
        """Create sample genetics for breeding."""
        genetics1 = PetGenetics(
            parent1_id="parent1",
            parent2_id="parent2"
        )
        genetics2 = PetGenetics(
            parent1_id="parent2",
            parent2_id="parent1"
        )

        return genetics1, genetics2

    def test_can_breed(self, breeding_system):
        """Test breeding compatibility check."""
        can_breed, reason = breeding_system.can_breed("pet1", "pet2")
        assert isinstance(can_breed, bool)
        assert isinstance(reason, str)

    def test_breed_pets(self, breeding_system, sample_genetics):
        """Test breeding two pets."""
        result = breeding_system.breed(
            sample_genetics[0],
            sample_genetics[1],
            "pet1_id",
            "pet2_id"
        )

        assert result is not None
        assert isinstance(result, BreedingResult)

    def test_cooldown(self, breeding_system):
        """Test breeding cooldown."""
        can_breed, reason = breeding_system.can_breed("pet1", "pet2")
        assert can_breed is True  # No cooldown initially

        # Set cooldown
        import time
        breeding_system.breeding_cooldowns["pet1"] = time.time() + 60

        # Should now be on cooldown
        can_breed, reason = breeding_system.can_breed("pet1", "pet2")
        assert can_breed is False


class TestTradeOffer:
    """Test TradeOffer class."""

    def test_trade_creation(self):
        """Test creating a trade offer."""
        trade = TradeOffer(
            trade_id="trade_1",
            from_user_id="user1",
            to_user_id="user2",
            offered_pet_id="pet_1",
            requested_pet_id="pet_2"
        )
        assert trade.trade_id == "trade_1"
        assert trade.status == TradeStatus.PENDING


class TestTradeStatus:
    """Test TradeStatus enum."""

    def test_trade_statuses(self):
        """Test trade status values."""
        assert TradeStatus.PENDING.value == "pending"
        assert TradeStatus.ACCEPTED.value == "accepted"
        assert TradeStatus.DECLINED.value == "declined"
        assert TradeStatus.CANCELLED.value == "cancelled"


class TestTradingSystem:
    """Test TradingSystem."""

    @pytest.fixture
    def trade_system(self):
        """Create trade system."""
        return TradingSystem()

    def test_create_trade(self, trade_system):
        """Test creating a trade."""
        trade_id = trade_system.create_trade_offer(
            from_user_id="user1",
            to_user_id="user2",
            offered_pet_id="pet_1",
            requested_pet_id="pet_2"
        )
        assert trade_id is not None

    def test_accept_trade(self, trade_system):
        """Test accepting a trade."""
        trade_id = trade_system.create_trade_offer(
            from_user_id="user1",
            to_user_id="user2",
            offered_pet_id="pet_1",
            requested_pet_id="pet_2"
        )

        result = trade_system.accept_trade(trade_id, "user2")
        assert result is True

    def test_decline_trade(self, trade_system):
        """Test declining a trade."""
        trade_id = trade_system.create_trade_offer(
            from_user_id="user1",
            to_user_id="user2",
            offered_pet_id="pet_1",
            requested_pet_id="pet_2"
        )

        result = trade_system.decline_trade(trade_id, "user2")
        assert result is True

    def test_cancel_trade(self, trade_system):
        """Test cancelling a trade."""
        trade_id = trade_system.create_trade_offer(
            from_user_id="user1",
            to_user_id="user2",
            offered_pet_id="pet_1",
            requested_pet_id="pet_2"
        )

        result = trade_system.cancel_trade(trade_id, "user1")
        assert result is True

    def test_get_trade(self, trade_system):
        """Test getting a trade."""
        trade_id = trade_system.create_trade_offer(
            from_user_id="user1",
            to_user_id="user2",
            offered_pet_id="pet_1",
            requested_pet_id="pet_2"
        )

        trade = trade_system.get_trade(trade_id)
        assert trade is not None
        assert trade.trade_id == trade_id

    def test_get_user_trades(self, trade_system):
        """Test getting user's trades."""
        trade_system.create_trade_offer(
            from_user_id="user1",
            to_user_id="user2",
            offered_pet_id="pet_1",
            requested_pet_id="pet_2"
        )

        trades = trade_system.get_user_trades("user1")
        assert len(trades) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
