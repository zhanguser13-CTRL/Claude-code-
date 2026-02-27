"""
Social System - Friends Module for Claude Pet Companion

Implements:
- Friend request system
- Online/offline status
- Friend activities
- Social interactions
"""

import random
import logging
import time
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class FriendStatus(Enum):
    """Status of a friendship."""
    NONE = "none"           # No relationship
    REQUEST_SENT = "request_sent"    # Request sent to user
    REQUEST_RECEIVED = "request_received"  # Request received from user
    FRIEND = "friend"      # Confirmed friend
    BLOCKED = "blocked"     # Blocked user


class OnlineStatus(Enum):
    """Online status indicators."""
    OFFLINE = "offline"
    AWAY = "away"
    IDLE = "idle"
    ONLINE = "online"
    BUSY = "busy"
    IN_GAME = "in_game"


@dataclass
class Friend:
    """A friend connection."""
    user_id: str
    username: str
    display_name: str = ""
    avatar: str = ""
    status: FriendStatus = FriendStatus.NONE
    online_status: OnlineStatus = OnlineStatus.OFFLINE
    last_seen: float = field(default_factory=time.time)
    level: int = 1
    pet_name: str = ""
    pet_evolution: int = 0

    # Social stats
    interactions: int = 0
    gifts_sent: int = 0
    gifts_received: int = 0
    battles_won: int = 0
    battles_lost: int = 0

    def __hash__(self):
        return hash(self.user_id)

    def update_online_status(self, status: OnlineStatus):
        """Update online status."""
        self.online_status = status
        if status != OnlineStatus.OFFLINE:
            self.last_seen = time.time()

    def add_interaction(self):
        """Record an interaction."""
        self.interactions += 1
        self.last_seen = time.time()

    def get_status_emoji(self) -> str:
        """Get emoji for online status."""
        return {
            OnlineStatus.OFFLINE: "⚫",
            OnlineStatus.AWAY: "🌙",
            OnlineStatus.IDLE: "💤",
            OnlineStatus.ONLINE: "🟢",
            OnlineStatus.BUSY: "🔴",
            OnlineStatus.IN_GAME: "🎮",
        }.get(self.online_status, "⚫")


@dataclass
class FriendRequest:
    """A friend request."""
    request_id: str
    from_user_id: str
    from_username: str
    to_user_id: str
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    status: str = "pending"  # pending, accepted, declined, expired


@dataclass
class SocialActivity:
    """A social activity/feed item."""
    activity_id: str
    activity_type: str  # "level_up", "evolution", "battle_win", etc.
    user_id: str
    username: str
    message: str
    timestamp: float = field(default_factory=time.time)
    pet_emoji: str = "🐾"


class FriendsSystem:
    """Manages friends and social interactions."""

    def __init__(self, current_user_id: str = "player"):
        self.current_user_id = current_user_id
        self.friends: Dict[str, Friend] = {}  # user_id -> Friend
        self.incoming_requests: Dict[str, FriendRequest] = {}
        self.outgoing_requests: Dict[str, FriendRequest] = {}
        self.blocked_users: Set[str] = set()

        # Activity feed
        self.activities: List[SocialActivity] = []

        # Online status cache
        self.online_users: Set[str] = set()

    def add_friend(self, friend: Friend) -> bool:
        """Add a friend (must be accepted first)."""
        if friend.user_id in self.blocked_users:
            return False

        self.friends[friend.user_id] = friend
        return True

    def remove_friend(self, user_id: str) -> bool:
        """Remove a friend."""
        if user_id in self.friends:
            del self.friends[user_id]
            return True
        return False

    def get_friend(self, user_id: str) -> Optional[Friend]:
        """Get friend by ID."""
        return self.friends.get(user_id)

    def get_all_friends(self) -> List[Friend]:
        """Get all friends."""
        return list(self.friends.values())

    def get_online_friends(self) -> List[Friend]:
        """Get friends who are online."""
        return [
            f for f in self.friends.values()
            if f.online_status != OnlineStatus.OFFLINE
        ]

    def send_friend_request(self, to_user_id: str, message: str = "") -> str:
        """Send a friend request."""
        request_id = f"req_{to_user_id}_{time.time()}"

        request = FriendRequest(
            request_id=request_id,
            from_user_id=self.current_user_id,
            from_username=self.current_user_id,  # Would use real username
            to_user_id=to_user_id,
            message=message
        )

        self.outgoing_requests[request_id] = request
        return request_id

    def accept_friend_request(self, request_id: str) -> bool:
        """Accept a friend request."""
        if request_id not in self.incoming_requests:
            return False

        request = self.incoming_requests[request_id]

        # Create friend
        friend = Friend(
            user_id=request.from_user_id,
            username=request.from_username,
            status=FriendStatus.FRIEND
        )

        self.friends[request.from_user_id] = friend

        # Remove request
        del self.incoming_requests[request_id]

        return True

    def decline_friend_request(self, request_id: str) -> bool:
        """Decline a friend request."""
        if request_id in self.incoming_requests:
            request = self.incoming_requests[request_id]
            request.status = "declined"
            del self.incoming_requests[request_id]
            return True
        return False

    def block_user(self, user_id: str) -> bool:
        """Block a user."""
        # Remove from friends first
        self.remove_friend(user_id)

        # Add to blocked
        self.blocked_users.add(user_id)

        # Remove any requests
        self.incoming_requests = {
            k: v for k, v in self.incoming_requests.items()
            if v.from_user_id != user_id
        }
        self.outgoing_requests = {
            k: v for k, v in self.outgoing_requests.items()
            if v.to_user_id != user_id
        }

        return True

    def unblock_user(self, user_id: str) -> bool:
        """Unblock a user."""
        if user_id in self.blocked_users:
            self.blocked_users.remove(user_id)
            return True
        return False

    def is_blocked(self, user_id: str) -> bool:
        """Check if a user is blocked."""
        return user_id in self.blocked_users

    def update_user_status(self, user_id: str, status: OnlineStatus):
        """Update a user's online status."""
        if status != OnlineStatus.OFFLINE:
            self.online_users.add(user_id)
        elif user_id in self.online_users:
            self.online_users.remove(user_id)

        # Update friend if exists
        friend = self.get_friend(user_id)
        if friend:
            friend.update_online_status(status)

    def add_activity(self, activity: SocialActivity):
        """Add an activity to the feed."""
        self.activities.insert(0, activity)

        # Keep only recent activities
        if len(self.activities) > 100:
            self.activities = self.activities[:100]

    def get_activity_feed(self, limit: int = 20) -> List[SocialActivity]:
        """Get recent activities."""
        return self.activities[:limit]

    def get_friend_activities(self, limit: int = 10) -> List[SocialActivity]:
        """Get activities from friends only."""
        friend_ids = set(self.friends.keys())
        return [
            a for a in self.activities
            if a.user_id in friend_ids
        ][:limit]

    def send_gift(self, to_user_id: str, gift_type: str = "item") -> bool:
        """Send a gift to a friend."""
        friend = self.get_friend(to_user_id)
        if friend:
            friend.gifts_received += 1

            # Record activity
            activity = SocialActivity(
                activity_id=f"gift_{time.time()}",
                activity_type="gift",
                user_id=self.current_user_id,
                username=self.current_user_id,
                message=f"sent a {gift_type} to their pet"
            )
            self.add_activity(activity)
            return True
        return False

    def get_friend_count(self) -> int:
        """Get number of friends."""
        return len(self.friends)

    def get_friend_stats(self) -> Dict:
        """Get friend statistics."""
        online_count = len(self.get_online_friends())

        # Count interactions
        total_interactions = sum(f.interactions for f in self.friends.values())

        return {
            'total_friends': len(self.friends),
            'online_friends': online_count,
            'pending_requests': len(self.incoming_requests),
            'blocked_users': len(self.blocked_users),
            'total_interactions': total_interactions,
        }

    def find_friends(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Find other users by username.

        In a real implementation, this would query a server.
        Returns mock results for now.
        """
        # Mock results
        mock_users = [
            {'user_id': 'user1', 'username': 'HappyPet', 'level': 15, 'pet': '🐱'},
            {'user_id': 'user2', 'username': 'DogLover', 'level': 22, 'pet': '🐕'},
            {'user_id': 'user3', 'username': 'CatFan', 'level': 8, 'pet': '😸'},
            {'user_id': 'user4', 'username': 'PetMaster', 'level': 30, 'pet': '🐰'},
            {'user_id': 'user5', 'username': 'AnimalFriend', 'level': 12, 'pet': '🐹'},
        ]

        # Filter by query
        if query:
            mock_users = [u for u in mock_users if query.lower() in u['username'].lower()]

        return mock_users[:limit]


if __name__ == "__main__":
    # Test friends system
    print("Testing Friends System")

    friends = FriendsSystem("test_user")

    # Add some mock friends
    friends.add_friend(Friend(
        user_id="user1",
        username="HappyPet",
        display_name="Happy Pet",
        pet_name="Whiskers",
        online_status=OnlineStatus.ONLINE
    ))

    friends.add_friend(Friend(
        user_id="user2",
        username="DogLover",
        display_name="Dog Lover",
        pet_name="Buddy",
        online_status=OnlineStatus.AWAY
    ))

    print(f"\nFriend count: {friends.get_friend_count()}")
    print(f"Stats: {friends.get_friend_stats()}")

    # Test online friends
    online = friends.get_online_friends()
    print(f"\nOnline friends: {len(online)}")
    for friend in online:
        print(f"  {friend.username} {friend.get_status_emoji()} - {friend.pet_name}")

    # Test activity feed
    friends.add_activity(SocialActivity(
        activity_id="act1",
        activity_type="level_up",
        user_id="user1",
        username="HappyPet",
        message="reached level 20!",
        pet_emoji="🐱"
    ))

    activities = friends.get_activity_feed()
    print(f"\nRecent activities:")
    for activity in activities[:3]:
        print(f"  {activity.username}: {activity.message}")

    print("\nFriends system test passed!")
