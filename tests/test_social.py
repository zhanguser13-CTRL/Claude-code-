"""
Social System Tests for Claude Pet Companion

Tests the friends system, arena battles, and leaderboards.
"""

import pytest
import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pet_companion.social import (
    Friend,
    FriendStatus,
    OnlineStatus,
    FriendRequest,
    SocialActivity,
    FriendsSystem,
    ElementType,
    MoveCategory,
    Move,
    BattlePet,
    BattleArena,
    Battle,
    MoveLibrary,
    PresetPets,
    LeaderboardType,
    LeaderboardEntry,
    Leaderboard,
    PlayerScore,
    LeaderboardManager,
)


class TestFriend:
    """Test Friend class."""

    def test_friend_creation(self):
        """Test creating a friend."""
        friend = Friend(
            user_id="test_user",
            username="TestUser",
            display_name="Test User",
            pet_name="Buddy"
        )
        assert friend.user_id == "test_user"
        assert friend.username == "TestUser"
        assert friend.status == FriendStatus.NONE
        assert friend.online_status == OnlineStatus.OFFLINE

    def test_update_online_status(self):
        """Test updating online status."""
        friend = Friend(user_id="test", username="Test")
        friend.update_online_status(OnlineStatus.ONLINE)
        assert friend.online_status == OnlineStatus.ONLINE

        friend.update_online_status(OnlineStatus.OFFLINE)
        assert friend.online_status == OnlineStatus.OFFLINE

    def test_add_interaction(self):
        """Test recording interactions."""
        friend = Friend(user_id="test", username="Test")
        assert friend.interactions == 0

        friend.add_interaction()
        assert friend.interactions == 1
        assert friend.last_seen > 0

    def test_status_emoji(self):
        """Test status emoji mapping."""
        friend = Friend(user_id="test", username="Test")

        friend.online_status = OnlineStatus.ONLINE
        assert friend.get_status_emoji() == "🟢"

        friend.online_status = OnlineStatus.OFFLINE
        assert friend.get_status_emoji() == "⚫"

        friend.online_status = OnlineStatus.AWAY
        assert friend.get_status_emoji() == "🌙"

        friend.online_status = OnlineStatus.IN_GAME
        assert friend.get_status_emoji() == "🎮"


class TestFriendRequest:
    """Test FriendRequest class."""

    def test_request_creation(self):
        """Test creating a friend request."""
        request = FriendRequest(
            request_id="req_1",
            from_user_id="user1",
            from_username="User1",
            to_user_id="user2",
            message="Let's be friends!"
        )
        assert request.request_id == "req_1"
        assert request.from_user_id == "user1"
        assert request.to_user_id == "user2"
        assert request.status == "pending"


class TestSocialActivity:
    """Test SocialActivity class."""

    def test_activity_creation(self):
        """Test creating a social activity."""
        activity = SocialActivity(
            activity_id="act_1",
            activity_type="level_up",
            user_id="user1",
            username="User1",
            message="reached level 20!",
            pet_emoji="🐱"
        )
        assert activity.activity_type == "level_up"
        assert activity.message == "reached level 20!"


class TestFriendsSystem:
    """Test FriendsSystem class."""

    @pytest.fixture
    def friends_system(self):
        """Create a friends system for testing."""
        return FriendsSystem("current_user")

    def test_add_friend(self, friends_system):
        """Test adding a friend."""
        friend = Friend(
            user_id="friend1",
            username="FriendOne",
            status=FriendStatus.FRIEND
        )
        result = friends_system.add_friend(friend)
        assert result is True
        assert friends_system.get_friend_count() == 1

    def test_remove_friend(self, friends_system):
        """Test removing a friend."""
        friend = Friend(user_id="friend1", username="FriendOne")
        friends_system.add_friend(friend)
        assert friends_system.get_friend_count() == 1

        result = friends_system.remove_friend("friend1")
        assert result is True
        assert friends_system.get_friend_count() == 0

    def test_get_friend(self, friends_system):
        """Test getting a friend."""
        friend = Friend(user_id="friend1", username="FriendOne")
        friends_system.add_friend(friend)

        retrieved = friends_system.get_friend("friend1")
        assert retrieved is not None
        assert retrieved.username == "FriendOne"

        # Test non-existent friend
        assert friends_system.get_friend("nonexistent") is None

    def test_online_friends(self, friends_system):
        """Test getting online friends."""
        # Add online friend
        online = Friend(
            user_id="online_friend",
            username="OnlineFriend",
            online_status=OnlineStatus.ONLINE
        )
        friends_system.add_friend(online)

        # Add offline friend
        offline = Friend(
            user_id="offline_friend",
            username="OfflineFriend",
            online_status=OnlineStatus.OFFLINE
        )
        friends_system.add_friend(offline)

        online_friends = friends_system.get_online_friends()
        assert len(online_friends) == 1
        assert online_friends[0].username == "OnlineFriend"

    def test_send_friend_request(self, friends_system):
        """Test sending a friend request."""
        request_id = friends_system.send_friend_request("target_user", "Hi!")
        assert request_id.startswith("req_")
        assert len(friends_system.outgoing_requests) == 1

    def test_accept_friend_request(self, friends_system):
        """Test accepting a friend request."""
        # Create incoming request
        request = FriendRequest(
            request_id="req_1",
            from_user_id="sender",
            from_username="Sender",
            to_user_id="current_user"
        )
        friends_system.incoming_requests["req_1"] = request

        # Accept request
        result = friends_system.accept_friend_request("req_1")
        assert result is True
        assert friends_system.get_friend("sender") is not None
        assert "req_1" not in friends_system.incoming_requests

    def test_block_user(self, friends_system):
        """Test blocking a user."""
        # Add friend first
        friend = Friend(user_id="block_me", username="BlockMe")
        friends_system.add_friend(friend)

        # Block user
        result = friends_system.block_user("block_me")
        assert result is True
        assert friends_system.is_blocked("block_me") is True
        assert friends_system.get_friend("block_me") is None

    def test_activity_feed(self, friends_system):
        """Test activity feed functionality."""
        activity = SocialActivity(
            activity_id="act_1",
            activity_type="level_up",
            user_id="user1",
            username="User1",
            message="Leveled up!"
        )
        friends_system.add_activity(activity)

        feed = friends_system.get_activity_feed(limit=10)
        assert len(feed) == 1
        assert feed[0].message == "Leveled up!"

    def test_send_gift(self, friends_system):
        """Test sending gifts."""
        friend = Friend(user_id="friend1", username="FriendOne")
        friends_system.add_friend(friend)

        result = friends_system.send_gift("friend1", "treat")
        assert result is True
        assert friend.gifts_received == 1

    def test_friend_stats(self, friends_system):
        """Test friend statistics."""
        friend = Friend(user_id="friend1", username="FriendOne",
                       online_status=OnlineStatus.ONLINE)
        friends_system.add_friend(friend)

        stats = friends_system.get_friend_stats()
        assert stats['total_friends'] == 1
        assert stats['online_friends'] == 1


class TestBattleArena:
    """Test BattleArena system."""

    @pytest.fixture
    def arena(self):
        """Create an arena for testing."""
        return BattleArena()

    @pytest.fixture
    def sample_pets(self):
        """Create sample battle pets."""
        pet1 = BattlePet(
            name="Flame",
            element=ElementType.FIRE,
            emoji="🔥",
            level=10,
            max_hp=100,
            current_hp=100,
            attack=60,
            defense=40,
            speed=65,
            moves=[MoveLibrary.ember(), MoveLibrary.flamethrower()]
        )
        pet1.owner_id = "player1"
        pet1.owner_name = "Player 1"

        pet2 = BattlePet(
            name="Splash",
            element=ElementType.WATER,
            emoji="💧",
            level=10,
            max_hp=110,
            current_hp=110,
            attack=50,
            defense=60,
            speed=50,
            moves=[MoveLibrary.water_gun(), MoveLibrary.hydro_pump()]
        )
        pet2.owner_id = "player2"
        pet2.owner_name = "Player 2"

        return pet1, pet2

    def test_create_battle(self, arena, sample_pets):
        """Test creating a battle."""
        pet1, pet2 = sample_pets
        battle = arena.create_battle(pet1, pet2)

        assert battle is not None
        assert battle.pet1 == pet1
        assert battle.pet2 == pet2
        assert battle.is_over is False

    def test_battle_turn(self, arena, sample_pets):
        """Test executing a battle turn."""
        pet1, pet2 = sample_pets
        battle = arena.create_battle(pet1, pet2)

        move = MoveLibrary.ember()
        action = battle.execute_turn(move)

        assert action.hit is True
        assert action.damage > 0
        assert pet2.current_hp < pet2.max_hp

    def test_type_effectiveness(self, arena, sample_pets):
        """Test type effectiveness."""
        pet1, pet2 = sample_pets
        battle = arena.create_battle(pet1, pet2)

        # Fire vs Water - not very effective
        effectiveness = battle.get_type_effectiveness(
            ElementType.FIRE, ElementType.WATER
        )
        # Water resists fire
        assert effectiveness <= 1.0

        # Fire vs Grass - super effective
        effectiveness = battle.get_type_effectiveness(
            ElementType.FIRE, ElementType.GRASS
        )
        assert effectiveness >= 1.5

    def test_battle_completion(self, arena, sample_pets):
        """Test battle ending conditions."""
        pet1, pet2 = sample_pets
        # Weaken pet2 significantly to ensure quick victory
        pet2.current_hp = 5

        battle = arena.create_battle(pet1, pet2)
        battle.execute_turn(MoveLibrary.ember())

        assert battle.is_over is True
        assert battle.winner == "player1"

    def test_surrender(self, arena, sample_pets):
        """Test surrendering from battle."""
        pet1, pet2 = sample_pets
        battle = arena.create_battle(pet1, pet2)

        winner = battle.surrender("player1")
        assert winner == "player2"
        assert battle.is_over is True


class TestMoveLibrary:
    """Test MoveLibrary."""

    def test_tackle_move(self):
        """Test Tackle move."""
        move = MoveLibrary.tackle()
        assert move.name == "Tackle"
        assert move.element == ElementType.NORMAL
        assert move.category == MoveCategory.PHYSICAL
        assert move.power == 40

    def test_elemental_moves(self):
        """Test elemental moves."""
        ember = MoveLibrary.ember()
        assert ember.element == ElementType.FIRE

        water_gun = MoveLibrary.water_gun()
        assert water_gun.element == ElementType.WATER

        vine_whip = MoveLibrary.vine_whip()
        assert vine_whip.element == ElementType.GRASS


class TestPresetPets:
    """Test PresetPets."""

    def test_spark_preset(self):
        """Test Spark preset pet."""
        spark = PresetPets.spark()
        assert spark.name == "Spark"
        assert spark.element == ElementType.ELECTRIC
        assert spark.emoji == "⚡"

    def test_flame_preset(self):
        """Test Flame preset pet."""
        flame = PresetPets.flame()
        assert flame.name == "Flame"
        assert flame.element == ElementType.FIRE
        assert flame.emoji == "🔥"

    def test_splash_preset(self):
        """Test Splash preset pet."""
        splash = PresetPets.splash()
        assert splash.name == "Splash"
        assert splash.element == ElementType.WATER
        assert splash.emoji == "💧"


class TestLeaderboard:
    """Test Leaderboard system."""

    @pytest.fixture
    def leaderboard(self):
        """Create a leaderboard for testing."""
        return Leaderboard(
            board_type=LeaderboardType.LEVEL,
            name="Level Rankings"
        )

    def test_update_score(self, leaderboard):
        """Test updating player scores."""
        leaderboard.update_player_score(
            user_id="player1",
            username="Player1",
            score=25,
            pet_name="Buddy",
            pet_emoji="🐕"
        )

        assert len(leaderboard.entries) == 1
        assert leaderboard.entries[0].score == 25

    def test_get_rank(self, leaderboard):
        """Test getting player rank."""
        leaderboard.update_player_score("player1", "Player1", score=10)
        leaderboard.update_player_score("player2", "Player2", score=20)
        leaderboard.update_player_score("player3", "Player3", score=30)

        # Higher score = lower rank number (sorted descending)
        rank = leaderboard.get_rank("player2")
        assert rank == 2  # Second place

    def test_get_top_entries(self, leaderboard):
        """Test getting top entries."""
        for i in range(10):
            leaderboard.update_player_score(
                f"player{i}",
                f"Player{i}",
                score=i * 10
            )

        top = leaderboard.get_top_entries(5)
        assert len(top) == 5
        assert top[0].score == 90  # Highest score

    def test_max_entries_limit(self, leaderboard):
        """Test max entries limit."""
        small_board = Leaderboard(
            board_type=LeaderboardType.LEVEL,
            max_entries=3
        )

        for i in range(10):
            small_board.update_player_score(
                f"player{i}",
                f"Player{i}",
                score=i
            )

        assert len(small_board.entries) == 3


class TestLeaderboardManager:
    """Test LeaderboardManager."""

    @pytest.fixture
    def manager(self):
        """Create a leaderboard manager."""
        return LeaderboardManager()

    def test_get_board(self, manager):
        """Test getting a specific board."""
        board = manager.get_board(LeaderboardType.LEVEL)
        assert board is not None
        assert board.board_type == LeaderboardType.LEVEL

    def test_update_score(self, manager):
        """Test updating scores through manager."""
        manager.update_score(
            "player1", "Player1",
            LeaderboardType.LEVEL, 25
        )

        rank = manager.get_global_rank("player1", LeaderboardType.LEVEL)
        assert rank == 1

    def test_register_player(self, manager):
        """Test player registration."""
        manager.register_player("new_player", "NewPlayer", "Fluffy", "🐱")

        scores = manager.get_player_scores("new_player")
        assert scores is not None
        assert scores.username == "NewPlayer"

    def test_simulate_players(self, manager):
        """Test player simulation."""
        manager.simulate_players(5)

        summaries = manager.get_all_summaries()
        for summary in summaries:
            if summary['total_players'] > 0:
                assert 'top_score' in summary


class TestPlayerScore:
    """Test PlayerScore."""

    def test_get_score(self):
        """Test getting score by type."""
        score = PlayerScore(
            user_id="player1",
            username="Player1",
            level=25,
            battle_wins=100
        )

        assert score.get_score(LeaderboardType.LEVEL) == 25
        assert score.get_score(LeaderboardType.BATTLE_WINS) == 100

    def test_add_battle_result(self):
        """Test recording battle results."""
        score = PlayerScore(user_id="player1", username="Player1")

        score.add_battle_result(won=True)
        assert score.battle_wins == 1
        assert score.battle_losses == 0

        score.add_battle_result(won=False)
        assert score.battle_wins == 1
        assert score.battle_losses == 1

    def test_add_playtime(self):
        """Test adding playtime."""
        score = PlayerScore(user_id="player1", username="Player1")

        score.add_playtime(30)
        assert score.total_playtime == 30

        score.add_playtime(45)
        assert score.total_playtime == 75


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
