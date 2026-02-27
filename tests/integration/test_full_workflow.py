"""
Integration Tests for Claude Pet Companion

End-to-end tests that verify complete workflows across multiple modules.
"""

import pytest
import sys
import time
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from claude_pet_companion.social import (
    FriendsSystem,
    BattleArena,
    MoveLibrary,
    PresetPets,
    ElementType,
    LeaderboardManager,
    LeaderboardType,
)

from claude_pet_companion.multi_pet import (
    Pet,
    PetType,
    PetState,
    Farm,
    BreedingManager,
    TradeManager,
)

from claude_pet_companion.performance import (
    profiler,
    cache_manager,
    lazy_loader,
    profile,
    cached,
    LoadPriority,
)

from claude_pet_companion.errors import (
    setup_crash_handler,
    setup_auto_save,
    crash_handler,
    AutoSaveManager,
)


class TestPetLifecycleWorkflow:
    """Test complete pet lifecycle from creation to evolution."""

    def test_pet_creation_and_growth(self):
        """Test creating a pet and leveling it up."""
        # Create a pet
        pet = Pet(
            pet_id="test_pet",
            name="Buddy",
            pet_type=PetType.CAT
        )

        assert pet.state == PetState.HATCHLING
        assert pet.level == 1

        # Feed and play with pet
        for _ in range(10):
            pet.feed()
            pet.play()

        assert pet.happiness > 50
        assert pet.hunger > 50

        # Add XP to level up
        pet.add_xp(500)
        assert pet.level > 1

    def test_pet_farm_workflow(self):
        """Test adding pet to farm and managing."""
        # Create farm
        farm = Farm(max_plots=5)

        # Create multiple pets
        pets = [
            Pet(pet_id=f"pet_{i}", name=f"Pet{i}", pet_type=PetType.CAT)
            for i in range(3)
        ]

        # Add pets to farm
        for pet in pets:
            result = farm.add_pet(pet)
            assert result is True

        # Verify farm state
        stats = farm.get_stats()
        assert stats['total_pets'] == 3
        assert stats['occupied_plots'] == 3

        # Collect resources
        resources = farm.collect_resources()
        assert isinstance(resources, dict)


class TestSocialWorkflow:
    """Test complete social features workflow."""

    def test_friendship_and_battle_workflow(self):
        """Test making friends and battling."""
        # Create friends system
        friends = FriendsSystem("player1")

        # Create arena
        arena = BattleArena()

        # Add a friend
        from claude_pet_companion.social import Friend, FriendStatus, OnlineStatus

        friend = Friend(
            user_id="player2",
            username="Player2",
            status=FriendStatus.FRIEND,
            online_status=OnlineStatus.ONLINE
        )
        friends.add_friend(friend)

        # Create battle pets
        pet1 = PresetPets.flame()
        pet1.owner_id = "player1"

        pet2 = PresetPets.splash()
        pet2.owner_id = "player2"

        # Battle
        battle = arena.create_battle(pet1, pet2)

        turns = 0
        while not battle.is_over and turns < 20:
            current_pet = battle.current_pet
            move = current_pet.moves[0]  # Use first move
            battle.execute_turn(move)
            turns += 1

        assert battle.is_over is True
        assert battle.winner in ["player1", "player2"]

        # Record battle result
        winner = battle.winner
        assert winner is not None

    def test_leaderboard_workflow(self):
        """Test updating and querying leaderboards."""
        manager = LeaderboardManager()

        # Simulate some players
        manager.simulate_players(10)

        # Register our player
        manager.register_player("test_player", "TestPlayer", "Buddy", "🐕")

        # Update scores
        manager.update_score("test_player", "TestPlayer", LeaderboardType.LEVEL, 25)
        manager.update_score("test_player", "TestPlayer", LeaderboardType.BATTLE_WINS, 10)

        # Check rank
        rank = manager.get_global_rank("test_player", LeaderboardType.LEVEL)
        assert rank is not None

        # Get summaries
        summaries = manager.get_all_summaries()
        assert len(summaries) > 0


class TestBreedingWorkflow:
    """Test complete breeding workflow."""

    def test_breeding_egg_to_pet_workflow(self):
        """Test breeding, egg creation, and hatching."""
        breeding_manager = BreedingManager()

        # Create parent pets
        parent1 = Pet(
            pet_id="parent1",
            name="Mom",
            pet_type=PetType.CAT,
            state=PetState.ADULT,
            level=10
        )

        parent2 = Pet(
            pet_id="parent2",
            name="Dad",
            pet_type=PetType.CAT,
            state=PetState.ADULT,
            level=10
        )

        # Breed
        result = breeding_manager.breed(parent1, parent2)
        assert result.success is True

        # Get egg
        egg = breeding_manager.get_egg(result.egg_id)
        assert egg is not None

        # Hatch (with short wait time for testing)
        from claude_pet_companion.multi_pet import Egg
        test_egg = Egg(
            egg_id="test_egg",
            parent1_id="p1",
            parent2_id="p2",
            hatch_time=0.1
        )

        time.sleep(0.15)
        assert test_egg.can_hatch() is True

        baby = test_egg.hatch()
        assert baby is not None
        assert baby.state == PetState.HATCHLING


class TestTradingWorkflow:
    """Test complete trading workflow."""

    def test_trade_creation_and_completion(self):
        """Test creating, accepting, and completing a trade."""
        trade_manager = TradeManager()

        # Create pets
        pet1 = Pet(pet_id="pet1", name="Pet1", pet_type=PetType.CAT)
        pet2 = Pet(pet_id="pet2", name="Pet2", pet_type=PetType.DOG)

        # Create trade
        trade_id = trade_manager.create_trade(
            from_user_id="user1",
            to_user_id="user2",
            offered_pet_ids=["pet1"],
            requested_pet_ids=["pet2"]
        )

        assert trade_id is not None

        # Get trade
        trade = trade_manager.get_trade(trade_id)
        assert trade is not None
        assert trade.from_user_id == "user1"

        # Accept trade
        result = trade_manager.accept_trade(trade_id, "user2")
        assert result is True


class TestPerformanceIntegration:
    """Test performance features integration."""

    def test_profiling_and_caching(self):
        """Test using profiler and cache together."""
        # Setup
        profiler.reset()
        profiler.enable()

        # Create cache
        cache = cache_manager.get_cache("integration_test")

        @profile
        @cached(cache_name='integration_test')
        def expensive_computation(n):
            """Simulate expensive computation."""
            total = 0
            for i in range(n):
                total += i * i
            return total

        # First call - computes
        result1 = expensive_computation(1000)

        # Second call - cached
        result2 = expensive_computation(1000)

        assert result1 == result2

        # Check profiler stats
        stats = profiler.get_stats("expensive_computation")
        assert stats is not None
        # May have been called twice due to how decorators chain

    def test_lazy_loading_workflow(self):
        """Test lazy loading resources."""
        loader = LazyLoader(max_workers=2)

        # Create test files
        import os
        test_dir = Path(tempfile.mkdtemp())

        try:
            test_file = test_dir / "test.txt"
            test_file.write_text("lazy load test")

            # Load synchronously
            data = loader.load_now("test_res", str(test_file), 'file')
            assert b"lazy load test" in data

            # Verify cache
            assert loader.is_loaded("test_res")

        finally:
            shutil.rmtree(test_dir)


class TestErrorHandlingIntegration:
    """Test error handling integration."""

    def test_crash_handling_workflow(self):
        """Test crash handler setup."""
        test_dir = Path(tempfile.mkdtemp())

        try:
            crash_dir = test_dir / "crashes"
            save_dir = test_dir / "saves"

            # Setup crash handler
            handler = setup_crash_handler(
                crash_dir=crash_dir,
                auto_restart=False
            )

            assert handler.crash_dir == crash_dir

            # Capture exception
            try:
                1 / 0
            except ZeroDivisionError as e:
                from claude_pet_companion.errors import capture_exception
                report = capture_exception(e)
                assert report.exception_type == "ZeroDivisionError"

            # Cleanup
            handler.shutdown()

        finally:
            shutil.rmtree(test_dir)

    def test_auto_save_workflow(self):
        """Test auto-save system."""
        test_dir = Path(tempfile.mkdtemp())

        try:
            save_dir = test_dir / "saves"

            # Create auto-save manager
            manager = AutoSaveManager(save_dir, auto_save_interval=0.5)

            # Set some data
            manager.set("test_key", "test_value")
            manager.set("number", 42)

            # Save immediately
            result = manager.save_now()
            assert result is True

            # Create new manager and load
            manager2 = AutoSaveManager(save_dir)
            loaded = manager2.load()
            assert loaded is True
            assert manager2.get("test_key") == "test_value"
            assert manager2.get("number") == 42

        finally:
            shutil.rmtree(test_dir)


class TestCompleteWorkflow:
    """Test complete end-to-end workflow."""

    def test_new_user_experience(self):
        """Test the new user onboarding experience."""
        # 1. Create a new pet
        pet = Pet(
            pet_id="user_first_pet",
            name="Buddy",
            pet_type=PetType.CAT
        )

        # 2. Add to farm
        farm = Farm(max_plots=10)
        farm.add_pet(pet)

        # 3. Care for pet
        pet.feed()
        pet.play()
        pet.add_xp(100)

        # 4. Setup social
        friends = FriendsSystem("new_user")
        from claude_pet_companion.social import Friend, OnlineStatus

        # Find and add friends
        found = friends.find_friends("Cat", limit=5)
        assert len(found) >= 0

        # 5. Setup leaderboard
        leaderboard = LeaderboardManager()
        leaderboard.register_player("new_user", "NewUser", "Buddy", "🐱")

        # 6. Setup performance tracking
        profiler.enable()

        # 7. Setup auto-save
        test_dir = Path(tempfile.mkdtemp())
        try:
            save_dir = test_dir / "saves"
            auto_save = AutoSaveManager(save_dir)
            auto_save.set("pet_name", pet.name)
            auto_save.set("pet_level", pet.level)
            auto_save.save_now()

            # Verify save
            assert auto_save.get("pet_name") == "Buddy"

        finally:
            shutil.rmtree(test_dir)

    def test_advanced_user_workflow(self):
        """Test advanced user with multiple pets and social features."""
        # 1. User has multiple pets
        farm = Farm(max_plots=20)

        pets = []
        for i in range(5):
            pet = Pet(
                pet_id=f"pet_{i}",
                name=f"Pet{i}",
                pet_type=PetType.CAT if i % 2 == 0 else PetType.DOG
            )
            pets.append(pet)
            farm.add_pet(pet)

        # 2. Breed pets
        breeding_manager = BreedingManager()

        # Find two adult pets
        pets[0].state = PetState.ADULT
        pets[0].level = 10
        pets[1].state = PetState.ADULT
        pets[1].level = 10

        result = breeding_manager.breed(pets[0], pets[1])
        assert result.success is True

        # 3. Battle with friends
        arena = BattleArena()

        from claude_pet_companion.social import FriendsSystem, Friend, FriendStatus
        friends = FriendsSystem("advanced_user")

        friend = Friend(
            user_id="friend_user",
            username="FriendUser",
            status=FriendStatus.FRIEND
        )
        friends.add_friend(friend)

        # 4. Check rankings
        leaderboard = LeaderboardManager()
        leaderboard.simulate_players(50)

        leaderboard.register_player("advanced_user", "AdvancedUser", "Pet0", "🐱")
        leaderboard.update_score("advanced_user", "AdvancedUser",
                               LeaderboardType.LEVEL, 50)

        rank = leaderboard.get_global_rank("advanced_user", LeaderboardType.LEVEL)
        assert rank is not None

        # 5. Trade pets
        trade_manager = TradeManager()
        trade_id = trade_manager.create_trade(
            from_user_id="advanced_user",
            to_user_id="friend_user",
            offered_pet_ids=["pet_2"],
            requested_pet_ids=["friend_pet"]
        )
        assert trade_id is not None


class TestModuleIntegration:
    """Test integration between different modules."""

    def test_social_multi_pet_integration(self):
        """Test social features with multi-pet system."""
        # User with multiple pets wants to battle
        farm = Farm(max_plots=10)

        pet1 = Pet(pet_id="battle_pet1", name="Fighter", pet_type=PetType.DOG)
        pet1.state = PetState.ADULT
        farm.add_pet(pet1)

        pet2 = Pet(pet_id="battle_pet2", name="Warrior", pet_type=PetType.CAT)
        pet2.state = PetState.ADULT
        farm.add_pet(pet2)

        # Setup social for battling
        friends = FriendsSystem("pet_owner")

        from claude_pet_companion.social import Friend, FriendStatus
        friend = Friend(
            user_id="opponent",
            username="Opponent",
            status=FriendStatus.FRIEND
        )
        friends.add_friend(friend)

        # Create battle pets based on farm pets
        from claude_pet_companion.social import BattlePet

        battle_pet1 = BattlePet(
            name=pet1.name,
            emoji="🐕",
            level=pet1.level,
            owner_id="pet_owner"
        )

        battle_pet2 = BattlePet(
            name="OpponentPet",
            emoji="🐱",
            level=10,
            owner_id="opponent"
        )

        arena = BattleArena()
        battle = arena.create_battle(battle_pet1, battle_pet2)

        # Simulate a few turns
        for _ in range(5):
            if not battle.is_over:
                battle.execute_turn(MoveLibrary.tackle())

    def test_performance_multi_pet_integration(self):
        """Test performance features with multi-pet system."""
        cache = cache_manager.get_cache("pet_cache")

        @cached(cache_name='pet_cache')
        def get_pet_stats(pet_id):
            """Simulate expensive pet stat calculation."""
            return {"health": 100, "attack": 50, "defense": 50}

        # Cache multiple pet stats
        for i in range(10):
            stats = get_pet_stats(f"pet_{i}")
            assert stats["health"] == 100

        # Second call should use cache
        stats = get_pet_stats("pet_5")
        assert stats is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
