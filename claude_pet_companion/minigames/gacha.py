"""
Gacha / Collection System for Claude Pet Companion

A collection card game with:
- Card rarities
- Pity system
- Collection tracking
- Trading between players
- Special limited-time cards
"""

import random
import logging
import json
import time
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter

logger = logging.getLogger(__name__)


class Rarity(Enum):
    """Card rarity levels."""
    COMMON = "common"           # 1★ - 80% chance
    UNCOMMON = "uncommon"       # 2★ - 15% chance
    RARE = "rare"             # 3★ - 4% chance
    EPIC = "epic"             # 4★ - 0.9% chance
    LEGENDARY = "legendary"     # 5★ - 0.1% chance
    MYTHIC = "mythic"         # 6★ - 0.01% chance (special events)


class CardCategory(Enum):
    """Types of collectible cards."""
    PET = "pet"              # Pet variants
    ITEM = "item"            # Useful items
    TOY = "toy"              # Toys for pets
    FOOD = "food"            # Special foods
    DECORATION = "decoration" # Home decorations
    SPECIAL = "special"       # Limited edition


@dataclass
class Card:
    """A collectible card."""
    id: str
    name: str
    rarity: Rarity
    category: CardCategory
    description: str = ""
    image: str = ""  # Image identifier
    attack: int = 0  # For battle cards
    defense: int = 0  # For battle cards
    special_ability: str = ""
    is_owned: bool = False
    quantity: int = 1  # For duplicate cards
    obtain_date: float = field(default_factory=time.time)

    def get_stars(self) -> int:
        """Get star rating (1-6)."""
        stars = {
            Rarity.COMMON: 1,
            Rarity.UNCOMMON: 2,
            Rarity.RARE: 3,
            Rarity.EPIC: 4,
            Rarity.LEGENDARY: 5,
            Rarity.MYTHIC: 6,
        }
        return stars.get(self.rarity, 1)

    def get_display_name(self) -> str:
        """Get formatted name with rarity indicator."""
        stars = "★" * self.get_stars()
        return f"{self.name} {stars}"

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'rarity': self.rarity.value,
            'category': self.category.value,
            'description': self.description,
            'image': self.image,
            'attack': self.attack,
            'defense': self.defense,
            'special_ability': self.special_ability,
            'is_owned': self.is_owned,
            'quantity': self.quantity,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Card':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            rarity=Rarity(data['rarity']),
            category=CardCategory(data['category']),
            description=data.get('description', ''),
            image=data.get('image', ''),
            attack=data.get('attack', 0),
            defense=data.get('defense', 0),
            special_ability=data.get('special_ability', ''),
            is_owned=data.get('is_owned', False),
            quantity=data.get('quantity', 1),
        )


@dataclass
class GachaPool:
    """A pool of cards that can be pulled from."""
    name: str
    cards: List[Card] = field(default_factory=list)
    cost: int = 100  # Cost per pull
    pity_threshold: int = 90  # Pulls until guaranteed 4+
    featured_cards: List[str] = field(default_factory=list)  # Increased rate cards
    is_limited: bool = False
    end_date: Optional[float] = None

    def get_rate(self, rarity: Rarity) -> float:
        """Get pull rate for a rarity."""
        base_rates = {
            Rarity.COMMON: 0.80,
            Rarity.UNCOMMON: 0.15,
            Rarity.RARE: 0.04,
            Rarity.EPIC: 0.009,
            Rarity.LEGENDARY: 0.001,
            Rarity.MYTHIC: 0.0001,
        }
        return base_rates.get(rarity, 0.0)


@dataclass
class PullResult:
    """Result of a gacha pull."""
    cards: List[Card] = field(default_factory=list)
    cost: int = 0
    pity_triggered: bool = False
    featured_pulled: bool = False
    new_cards: int = 0
    duplicates: int = 0


class GachaSystem:
    """Main gacha system."""

    def __init__(self):
        self.pools: Dict[str, GachaPool] = {}
        self.collection: Dict[str, Card] = {}  # owned cards by ID
        self.pity_counters: Dict[str, int] = {}  # pity counter per pool
        self.currency: int = 1000  # Starting currency
        self.total_pulls: int = 0

        # Initialize default pool
        self._create_default_pool()

    def _create_default_pool(self):
        """Create the default card pool."""
        pool = GachaPool(name="Standard", cost=100)

        # Common cards
        for i in range(10):
            pool.cards.append(Card(
                id=f"common_pet_{i}",
                name=f"Cute Pet #{i+1}",
                rarity=Rarity.COMMON,
                category=CardCategory.PET,
                description="A common cute pet.",
                attack=random.randint(1, 5),
                defense=random.randint(1, 5),
            ))

        # Uncommon cards
        for i in range(5):
            pool.cards.append(Card(
                id=f"uncommon_pet_{i}",
                name=f"Adorable Pet #{i+1}",
                rarity=Rarity.UNCOMMON,
                category=CardCategory.PET,
                description="An uncommon pet with special traits.",
                attack=random.randint(5, 10),
                defense=random.randint(5, 10),
            ))

        # Rare cards
        for i in range(3):
            pool.cards.append(Card(
                id=f"rare_pet_{i}",
                name=f"Majestic Pet #{i+1}",
                rarity=Rarity.RARE,
                category=CardCategory.PET,
                description="A rare and powerful pet.",
                attack=random.randint(10, 15),
                defense=random.randint(10, 15),
            ))

        # Epic cards
        for i in range(2):
            pool.cards.append(Card(
                id=f"epic_pet_{i}",
                name=f"Epic Companion #{i+1}",
                rarity=Rarity.EPIC,
                category=CardCategory.PET,
                description="An epic pet with legendary potential.",
                attack=random.randint(15, 20),
                defense=random.randint(15, 20),
            ))

        # One legendary
        pool.cards.append(Card(
            id="legendary_pet_0",
            name="Legendary Guardian",
            rarity=Rarity.LEGENDARY,
            category=CardCategory.PET,
            description="The legendary guardian of all pets.",
            attack=30,
            defense=25,
        ))

        self.pools["standard"] = pool
        self.pity_counters["standard"] = 0

    def add_pool(self, pool: GachaPool):
        """Add a gacha pool."""
        self.pools[pool.name.lower()] = pool
        self.pity_counters[pool.name.lower()] = 0

    def pull(self, pool_name: str = "standard", count: int = 1) -> PullResult:
        """
        Perform gacha pulls.

        Args:
            pool_name: Name of the pool to pull from
            count: Number of pulls (1-10 at a time)

        Returns:
            PullResult with cards and stats
        """
        count = max(1, min(10, count))
        pool = self.pools.get(pool_name.lower())

        if not pool:
            return PullResult(cards=[], cost=0)

        total_cost = pool.cost * count

        if self.currency < total_cost:
            return PullResult(cards=[], cost=0)

        self.currency -= total_cost
        self.total_pulls += count
        self.pity_counters[pool_name.lower()] += count

        result = PullResult(cost=total_cost)
        pity_triggered = False

        # Check pity (guaranteed 4+ star after threshold)
        if self.pity_counters[pool_name.lower()] >= pool.pity_threshold:
            pity_triggered = True
            guaranteed_rarities = [Rarity.EPIC, Rarity.LEGENDARY, Rarity.MYTHIC]
            guaranteed_rarity = random.choice(guaranteed_rarities)

            # Get cards of guaranteed rarity or higher
            pool_cards = [c for c in pool.cards if c.rarity.value in [r.value for r in [
                Rarity.COMMON, Rarity.UNCOMMON, Rarity.RARE
            ]] or c.rarity == guaranteed_rarity]

            if pool_cards:
                card = random.choice(pool_cards)
                result.cards.append(card)

        # Pull cards
        pulls_remaining = count - len(result.cards)

        for _ in range(pulls_remaining):
            card = self._pull_single(pool)
            result.cards.append(card)

            # Check for featured
            if card.id in pool.featured_cards:
                result.featured_pulled = True

        # Process results
        for card in result.cards:
            if card.id in self.collection:
                # Duplicate
                card.quantity = self.collection[card.id].quantity + 1
                result.duplicates += 1
            else:
                # New card
                card.is_owned = True
                self.collection[card.id] = card
                result.new_cards += 1

        # Reset pity if 4+ was pulled
        if any(c.get_stars() >= 4 for c in result.cards):
            self.pity_counters[pool_name.lower()] = 0

        return result

    def _pull_single(self, pool: GachaPool) -> Card:
        """Pull a single card from the pool."""
        # Roll for rarity
        roll = random.random()

        # Determine rarity tier
        if roll < 0.0001:
            rarity = Rarity.MYTHIC
        elif roll < 0.0011:
            rarity = Rarity.LEGENDARY
        elif roll < 0.011:
            rarity = Rarity.EPIC
        elif roll < 0.051:
            rarity = Rarity.RARE
        elif roll < 0.201:
            rarity = Rarity.UNCOMMON
        else:
            rarity = Rarity.COMMON

        # Get cards of this rarity
        rarity_cards = [c for c in pool.cards if c.rarity == rarity]

        if not rarity_cards:
            # Fallback to common
            rarity_cards = [c for c in pool.cards if c.rarity == Rarity.COMMON]

        if rarity_cards:
            return random.choice(rarity_cards)

        # Fallback
        return pool.cards[0]

    def get_collection(self) -> Dict[str, Card]:
        """Get all owned cards."""
        return self.collection.copy()

    def get_card(self, card_id: str) -> Optional[Card]:
        """Get a specific card."""
        return self.collection.get(card_id)

    def get_cards_by_rarity(self, rarity: Rarity) -> List[Card]:
        """Get all owned cards of a rarity."""
        return [c for c in self.collection.values() if c.rarity == rarity]

    def get_cards_by_category(self, category: CardCategory) -> List[Card]:
        """Get all owned cards of a category."""
        return [c for c in self.collection.values() if c.category == category]

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        owned_by_rarity = Counter(c.rarity.value for c in self.collection.values())
        owned_by_category = Counter(c.category.value for c in self.collection.values())

        total_unique = len(self.collection)
        total_count = sum(c.quantity for c in self.collection.values())

        # Collection completion
        total_possible = sum(len(pool.cards) for pool in self.pools.values())

        return {
            'unique_cards': total_unique,
            'total_cards': total_count,
            'currency': self.currency,
            'total_pulls': self.total_pulls,
            'by_rarity': dict(owned_by_rarity),
            'by_category': dict(owned_by_category),
            'completion': f"{(total_unique / max(1, total_possible) * 100):.1f}%",
        }

    def add_currency(self, amount: int):
        """Add currency."""
        self.currency += amount

    def spend_currency(self, amount: int) -> bool:
        """Spend currency if available."""
        if self.currency >= amount:
            self.currency -= amount
            return True
        return False

    def save_collection(self, filepath: str = "gacha_save.json"):
        """Save collection to file."""
        data = {
            'collection': {id: c.to_dict() for id, c in self.collection.items()},
            'currency': self.currency,
            'total_pulls': self.total_pulls,
            'pity_counters': self.pity_counters,
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load_collection(self, filepath: str = "gacha_save.json"):
        """Load collection from file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            self.collection = {
                id: Card.from_dict(card_data)
                for id, card_data in data.get('collection', {}).items()
            }
            self.currency = data.get('currency', 1000)
            self.total_pulls = data.get('total_pulls', 0)
            self.pity_counters = data.get('pity_counters', {})

            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False

    def get_pity_progress(self, pool_name: str = "standard") -> Tuple[int, int]:
        """Get pity progress (current, threshold)."""
        pool = self.pools.get(pool_name.lower())
        if pool:
            current = self.pity_counters.get(pool_name.lower(), 0)
            return (min(current, pool.pity_threshold), pool.pity_threshold)
        return (0, 90)


class CardTrader:
    """Trading system for cards."""

    def __init__(self, gacha_system: GachaSystem):
        self.gacha = gacha_system
        self.trades: List[Dict] = []

    def can_trade(self, card_id: str) -> bool:
        """Check if a card can be traded."""
        card = self.gacha.get_card(card_id)
        return card is not None and card.quantity > 1

    def create_trade_offer(self, offering_card_ids: List[str],
                         requesting_card_ids: List[str]) -> bool:
        """
        Create a trade offer.

        Returns:
            True if trade is valid
        """
        # Check if offering cards exist and are owned
        for card_id in offering_card_ids:
            card = self.gacha.get_card(card_id)
            if not card:
                return False

        self.trades.append({
            'offering': offering_card_ids,
            'requesting': requesting_card_ids,
            'timestamp': time.time(),
            'status': 'pending',
        })

        return True

    def accept_trade(self, trade_index: int) -> bool:
        """Accept a trade offer."""
        if trade_index >= len(self.trades):
            return False

        trade = self.trades[trade_index]

        # Process trade
        for card_id in trade['offering']:
            if card_id in self.gacha.collection:
                self.gacha.collection[card_id].quantity += 1
            else:
                # New card
                card = self.gacha.collection.get(card_id)
                if card:
                    new_card = Card(**card.__dict__)
                    new_card.quantity = 1
                    self.gacha.collection[card_id] = new_card

        trade['status'] = 'completed'
        return True

    def get_pending_trades(self) -> List[Dict]:
        """Get pending trade offers."""
        return [t for t in self.trades if t['status'] == 'pending']


# Preset limited-time pools

class LimitedPools:
    """Limited-time gacha pools."""

    @staticmethod
    def summer_event() -> GachaPool:
        """Summer themed limited pool."""
        pool = GachaPool(
            name="Summer Event",
            cost=150,
            pity_threshold=70,
            is_limited=True,
            end_date=time.time() + 30 * 24 * 3600  # 30 days
        )

        # Summer themed cards
        pool.cards = [
            Card(
                id="summer_beach_pet",
                name="Beach Buddy",
                rarity=Rarity.UNCOMMON,
                category=CardCategory.PET,
                description="Loves the beach and swimming!",
                attack=10,
                defense=8,
            ),
            Card(
                id="summer_surf_pet",
                name="Surf Champion",
                rarity=Rarity.RARE,
                category=CardCategory.PET,
                description="Hangs ten on every wave!",
                attack=15,
                defense=12,
            ),
            Card(
                id="summer_legend",
                name="Sun God",
                rarity=Rarity.LEGENDARY,
                category=CardCategory.PET,
                description="The legendary bringer of summer.",
                attack=35,
                defense=30,
            ),
        ]

        pool.featured_cards = ["summer_legend"]
        return pool

    @staticmethod
    def halloween_event() -> GachaPool:
        """Halloween themed limited pool."""
        pool = GachaPool(
            name="Halloween",
            cost=150,
            pity_threshold=80,
            is_limited=True,
            end_date=time.time() + 30 * 24 * 3600
        )

        pool.cards = [
            Card(
                id="spooky_cat",
                name="Spooky Kitty",
                rarity=Rarity.UNCOMMON,
                category=CardCategory.PET,
                description="A mysterious black cat.",
                attack=12,
                defense=10,
            ),
            Card(
                id="ghost_pet",
                name="Ghost Friend",
                rarity=Rarity.EPIC,
                category=CardCategory.PET,
                description="A friendly ghost pet.",
                attack=20,
                defense=18,
            ),
            Card(
                id="pumpkin_king",
                name="Pumpkin King",
                rarity=Rarity.LEGENDARY,
                category=CardCategory.PET,
                description="Ruler of the Halloween realm.",
                attack=32,
                defense=28,
            ),
        ]

        pool.featured_cards = ["pumpkin_king"]
        return pool


if __name__ == "__main__":
    # Test gacha system
    print("Testing Gacha System")

    gacha = GachaSystem()

    print(f"\nStarting currency: {gacha.currency}")

    # Do some pulls
    print("\nPulling 10 cards:")
    result = gacha.pull("standard", count=10)

    print(f"Cost: {result.cost}")
    print(f"New cards: {result.new_cards}")
    print(f"Duplicates: {result.duplicates}")
    print(f"Pity triggered: {result.pity_triggered}")

    print("\nPulled cards:")
    for card in result.cards:
        print(f"  {card.get_display_name()} - {card.category.value}")

    # Check collection stats
    stats = gacha.get_collection_stats()
    print(f"\nCollection stats: {stats}")

    # Check pity
    pity_current, pity_max = gacha.get_pity_progress()
    print(f"Pity progress: {pity_current}/{pity_max}")

    # Try for legendary
    print("\nPulling until legendary (simulated):")
    legendary_found = False
    pulls = 0

    while not legendary_found and pulls < 200:
        result = gacha.pull("standard", count=10)
        pulls += 10

        for card in result.cards:
            if card.rarity == Rarity.LEGENDARY:
                print(f"  Found {card.name} after {pulls} pulls!")
                legendary_found = True
                break

    print(f"\nFinal currency: {gacha.currency}")

    print("\nGacha system test passed!")
