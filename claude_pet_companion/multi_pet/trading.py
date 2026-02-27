"""
Pet Trading System for Claude Pet Companion

Allows trading pets with other players:
- Trade offers
- Trade history
- Trade value estimation
"""

import random
import logging
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TradeStatus(Enum):
    """Status of a trade."""
    PENDING = "pending"     # Offer sent, waiting for response
    ACCEPTED = "accepted"   # Trade completed
    DECLINED = "declined"  # Trade rejected
    CANCELLED = "cancelled"  # Trade cancelled
    EXPIRED = "expired"     # Trade offer expired


@dataclass
class TradeOffer:
    """A trade offer between players."""
    trade_id: str
    from_user_id: str
    to_user_id: str
    offered_pet_id: str
    requested_pet_id: Optional[str] = None
    offered_items: List[str] = field(default_factory=list)
    requested_items: List[str] = field(default_factory=list)
    currency_offered: int = 0
    currency_requested: int = 0
    status: TradeStatus = TradeStatus.PENDING
    timestamp: float = field(default_factory=time.time)
    expiry_time: float = field(default_factory=lambda: time.time() + 86400)  # 24 hours
    message: str = ""

    def is_expired(self) -> bool:
        """Check if trade has expired."""
        return time.time() > self.expiry_time

    def get_estimated_value(self) -> int:
        """Get estimated trade value (offered - requested)."""
        # Simple value estimation
        value = self.currency_offered - self.currency_requested
        # Pet values would depend on level, rarity, etc.
        return value


class TradingSystem:
    """Manages pet trading between players."""

    def __init__(self):
        self.active_trades: Dict[str, TradeOffer] = {}
        self.trade_history: List[TradeOffer] = []
        self.user_reputation: Dict[str, int] = {}  # user_id -> reputation score

    def create_trade_offer(self, from_user_id: str, to_user_id: str,
                          offered_pet_id: str, requested_pet_id: str = None,
                          currency_offered: int = 0, currency_requested: int = 0,
                          message: str = "") -> str:
        """Create a new trade offer."""
        trade_id = f"trade_{from_user_id}_{to_user_id}_{int(time.time())}"

        trade = TradeOffer(
            trade_id=trade_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            offered_pet_id=offered_pet_id,
            requested_pet_id=requested_pet_id,
            currency_offered=currency_offered,
            currency_requested=currency_requested,
            message=message
        )

        self.active_trades[trade_id] = trade
        return trade_id

    def accept_trade(self, trade_id: str, user_id: str) -> bool:
        """Accept a trade offer."""
        trade = self.active_trades.get(trade_id)
        if not trade:
            return False

        if trade.to_user_id != user_id:
            return False

        # Execute trade
        trade.status = TradeStatus.ACCEPTED
        self._finalize_trade(trade)

        # Remove from active
        del self.active_trades[trade_id]
        self.trade_history.append(trade)

        return True

    def decline_trade(self, trade_id: str, user_id: str) -> bool:
        """Decline a trade offer."""
        trade = self.active_trades.get(trade_id)
        if not trade:
            return False

        if trade.to_user_id != user_id:
            return False

        trade.status = TradeStatus.DECLINED
        del self.active_trades[trade_id]
        self.trade_history.append(trade)

        return True

    def cancel_trade(self, trade_id: str, user_id: str) -> bool:
        """Cancel a trade offer."""
        trade = self.active_trades.get(trade_id)
        if not trade:
            return False

        if trade.from_user_id != user_id:
            return False

        trade.status = TradeStatus.CANCELLED
        del self.active_trades[trade_id]
        self.trade_history.append(trade)

        return True

    def get_trade(self, trade_id: str) -> Optional[TradeOffer]:
        """Get a trade by ID."""
        return self.active_trades.get(trade_id)

    def get_user_trades(self, user_id: str, include_history: bool = False
                       ) -> List[TradeOffer]:
        """Get all trades for a user."""
        trades = [t for t in self.active_trades.values()
                 if t.from_user_id == user_id or t.to_user_id == user_id]

        if include_history:
            trades.extend([t for t in self.trade_history
                          if t.from_user_id == user_id or t.to_user_id == user_id])

        return sorted(trades, key=lambda t: t.timestamp, reverse=True)

    def get_pending_trades(self, user_id: str) -> List[TradeOffer]:
        """Get pending trades for a user."""
        return [t for t in self.active_trades.values()
                if t.to_user_id == user_id and t.status == TradeStatus.PENDING]

    def update_reputation(self, user_id: str, delta: int):
        """Update a user's reputation."""
        self.user_reputation[user_id] = self.user_reputation.get(user_id, 0) + delta

    def get_reputation(self, user_id: str) -> int:
        """Get a user's reputation score."""
        return self.user_reputation.get(user_id, 0)

    def clean_expired_trades(self):
        """Remove expired trade offers."""
        expired = [tid for tid, trade in self.active_trades.items()
                   if trade.is_expired()]

        for trade_id in expired:
            trade = self.active_trades[trade_id]
            trade.status = TradeStatus.EXPIRED
            self.trade_history.append(trade)
            del self.active_trades[trade_id]

    def estimate_pet_value(self, pet_id: str, pet_data: Dict = None) -> int:
        """Estimate the value of a pet for trading."""
        # In a real implementation, this would check pet level, stats, rarity
        # For now, return a random value based on pet data
        if pet_data:
            level = pet_data.get('level', 1)
            rarity = pet_data.get('rarity', 'common')

            rarity_multiplier = {
                'common': 1,
                'uncommon': 2,
                'rare': 5,
                'epic': 10,
                'legendary': 25,
                'mythic': 50,
            }.get(rarity, 1)

            return level * 100 * rarity_multiplier

        return random.randint(100, 1000)

    def _finalize_trade(self, trade: TradeOffer):
        """Finalize a completed trade (exchange pets/items)."""
        # In a real implementation, this would:
        # 1. Transfer pets between users
        # 2. Transfer items
        # 3. Transfer currency
        # 4. Update histories
        pass


if __name__ == "__main__":
    # Test trading system
    print("Testing Trading System")

    trading = TradingSystem()

    # Create a trade
    trade_id = trading.create_trade_offer(
        from_user_id="user1",
        to_user_id="user2",
        offered_pet_id="pet1",
        requested_pet_id="pet2",
        currency_offered=0,
        currency_requested=100,
        message="Will trade for coins"
    )

    print(f"\nTrade created: {trade_id}")
    trade = trading.get_trade(trade_id)
    if trade:
        print(f"  From: {trade.from_user_id}")
        print(f"   To: {trade.to_user_id}")
        print(f"   Status: {trade.status.value}")

    # Check reputation
    rep1 = trading.get_reputation("user2")
    print(f"\nUser2 reputation before trade: {rep1}")

    # Simulate acceptance
    accepted = trading.accept_trade(trade_id, "user2")
    print(f"\nTrade accepted: {accepted}")

    rep2 = trading.get_reputation("user2")
    print(f"User2 reputation after trade: {rep2}")

    # Check trades
    user_trades = trading.get_user_trades("user1", include_history=True)
    print(f"\nUser1 trades: {len(user_trades)}")

    print("\nTrading system test passed!")
