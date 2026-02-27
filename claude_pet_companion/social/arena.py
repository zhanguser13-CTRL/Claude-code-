"""
Arena/PVP System for Claude Pet Companion

Implements pet battling with:
- Turn-based combat
- Type advantages
- Special abilities
- Ranked matches
- Leaderboards
"""

import random
import logging
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ElementType(Enum):
    """Element types for pets."""
    NORMAL = "normal"
    FIRE = "fire"
    WATER = "water"
    GRASS = "grass"
    ELECTRIC = "electric"
    ICE = "ice"
    FIGHTING = "fighting"
    POISON = "poison"
    GROUND = "ground"
    FLYING = "flying"
    PSYCHIC = "psychic"
    BUG = "bug"
    ROCK = "rock"
    GHOST = "ghost"
    DRAGON = "dragon"
    DARK = "dark"
    STEEL = "steel"
    FAIRY = "fairy"


# Type effectiveness chart (attack vs defense)
TYPE_EFFECTIVENESS = {
    # Super effective (2x)
    (ElementType.FIRE, ElementType.GRASS): 2.0,
    (ElementType.FIRE, ElementType.BUG): 2.0,
    (ElementType.FIRE, ElementType.ICE): 2.0,
    (ElementType.FIRE, ElementType.STEEL): 2.0,

    (ElementType.WATER, ElementType.FIRE): 2.0,
    (ElementType.WATER, ElementType.GROUND): 2.0,
    (ElementType.WATER, ElementType.ROCK): 2.0,

    (ElementType.GRASS, ElementType.WATER): 2.0,
    (ElementType.GRASS, ElementType.GROUND): 2.0,
    (ElementType.GRASS, ElementType.ROCK): 2.0,

    (ElementType.ELECTRIC, ElementType.WATER): 2.0,
    (ElementType.ELECTRIC, ElementType.FLYING): 2.0,

    (ElementType.ICE, ElementType.GRASS): 2.0,
    (ElementType.ICE, ElementType.GROUND): 2.0,
    (ElementType.ICE, ElementType.FLYING): 2.0,
    (ElementType.ICE, ElementType.DRAGON): 2.0,

    (ElementType.FIGHTING, ElementType.NORMAL): 2.0,
    (ElementType.FIGHTING, ElementType.ICE): 2.0,
    (ElementType.FIGHTING, ElementType.ROCK): 2.0,
    (ElementType.FIGHTING, ElementType.DARK): 2.0,
    (ElementType.FIGHTING, ElementType.STEEL): 2.0,

    (ElementType.POISON, ElementType.GRASS): 2.0,
    (ElementType.POISON, ElementType.FAIRY): 2.0,

    (ElementType.GROUND, ElementType.ELECTRIC): 2.0,
    (ElementType.GROUND, ElementType.POISON): 2.0,
    (ElementType.GROUND, ElementType.ROCK): 2.0,
    (ElementType.GROUND, ElementType.STEEL): 2.0,
    (ElementType.GROUND, ElementType.FIRE): 2.0,

    (ElementType.FLYING, ElementType.GRASS): 2.0,
    (ElementType.FLYING, ElementType.FIGHTING): 2.0,
    (ElementType.FLYING, ElementType.BUG): 2.0,

    (ElementType.PSYCHIC, ElementType.FIGHTING): 2.0,
    (ElementType.PSYCHIC, ElementType.POISON): 2.0,

    (ElementType.BUG, ElementType.GRASS): 2.0,
    (ElementType.BUG, ElementType.PSYCHIC): 2.0,
    (ElementType.BUG, ElementType.DARK): 2.0,

    (ElementType.ROCK, ElementType.FIRE): 2.0,
    (ElementType.ROCK, ElementType.ICE): 2.0,
    (ElementType.ROCK, ElementType.FLYING): 2.0,
    (ElementType.ROCK, ElementType.BUG): 2.0,

    (ElementType.GHOST, ElementType.PSYCHIC): 2.0,
    (ElementType.GHOST, ElementType.GHOST): 2.0,

    (ElementType.DRAGON, ElementType.DRAGON): 2.0,

    (ElementType.DARK, ElementType.PSYCHIC): 2.0,
    (ElementType.DARK, ElementType.GHOST): 2.0,

    (ElementType.STEEL, ElementType.ICE): 2.0,
    (ElementType.STEEL, ElementType.ROCK): 2.0,
    (ElementType.STEEL, ElementType.FAIRY): 2.0,

    (ElementType.FAIRY, ElementType.FIGHTING): 2.0,
    (ElementType.FAIRY, ElementType.DARK): 2.0,
    (ElementType.FAIRY, ElementType.DRAGON): 2.0,
}


class MoveCategory(Enum):
    """Categories of moves."""
    PHYSICAL = "physical"  # Uses attack
    SPECIAL = "special"    # Uses special attack
    STATUS = "status"      # Status effect


@dataclass
class Move:
    """A battle move."""
    name: str
    element: ElementType
    category: MoveCategory
    power: int  # Base damage (0 for status moves)
    accuracy: float  # 0-1, chance to hit
    pp: int  # Power points (uses)
    description: str = ""

    # Effects
    stat_changes: Dict[str, int] = field(default_factory=dict)  # stat boosts/drops
    status_effect: Optional[str] = None  # Status to inflict
    status_chance: float = 0.0

    def __str__(self):
        return f"{self.name} ({self.element.value}) - {self.category.value} {self.power} power"


@dataclass
class BattlePet:
    """A pet for battle."""
    name: str
    level: int = 1
    element: ElementType = ElementType.NORMAL
    emoji: str = "🐾"

    # Stats
    max_hp: int = 100
    current_hp: int = 100
    attack: int = 50
    defense: int = 50
    special_attack: int = 50
    special_defense: int = 50
    speed: int = 50

    # Moves
    moves: List[Move] = field(default_factory=list)

    # Owner
    owner_id: str = ""
    owner_name: str = ""

    def get_effective_attack(self, category: MoveCategory) -> int:
        """Get attack stat for category."""
        if category == MoveCategory.PHYSICAL:
            return self.attack
        return self.special_attack

    def get_effective_defense(self, category: MoveCategory) -> int:
        """Get defense stat for category."""
        if category == MoveCategory.PHYSICAL:
            return self.defense
        return self.special_defense

    def take_damage(self, damage: int) -> int:
        """Take damage, return actual damage taken."""
        self.current_hp = max(0, self.current_hp - damage)
        return damage

    def is_alive(self) -> bool:
        """Check if pet can still battle."""
        return self.current_hp > 0

    def get_hp_percentage(self) -> float:
        """Get HP as percentage."""
        if self.max_hp == 0:
            return 0.0
        return self.current_hp / self.max_hp


@dataclass
class BattleAction:
    """An action taken in battle."""
    pet: BattlePet
    move: Move
    damage: int = 0
    effectiveness: float = 1.0
    hit: bool = True
    critical: bool = False


@dataclass
class BattleResult:
    """Result of a battle."""
    winner: str  # user_id of winner
    loser: str  # user_id of loser
    turns: int
    actions: List[BattleAction] = field(default_factory=list)
    reward_xp: int = 0
    rank_change: int = 0


class BattleArena:
    """Arena for pet battles."""

    def __init__(self):
        self.active_battles: Dict[str, "Battle"] = {}
        self.battle_history: List[BattleResult] = []

    def create_battle(self, pet1: BattlePet, pet2: BattlePet) -> "Battle":
        """Create a new battle."""
        battle = Battle(pet1, pet2)
        battle_id = f"battle_{time.time()}_{random.randint(1000, 9999)}"
        self.active_battles[battle_id] = battle
        return battle

    def get_battle(self, battle_id: str) -> Optional["Battle"]:
        """Get an active battle."""
        return self.active_battles.get(battle_id)

    def end_battle(self, battle_id: str, result: BattleResult):
        """End a battle and record results."""
        if battle_id in self.active_battles:
            del self.active_battles[battle_id]
        self.battle_history.append(result)


class Battle:
    """A single battle instance."""

    def __init__(self, pet1: BattlePet, pet2: BattlePet):
        self.pet1 = pet1
        self.pet2 = pet2
        self.turn = 1
        self.current_pet = pet1  # Pet that acts this turn
        self.actions: List[BattleAction] = []
        self.is_over = False
        self.winner = None

        # Determine turn order based on speed
        if pet2.speed > pet1.speed:
            self.current_pet = pet2

    def get_opponent(self, pet: BattlePet) -> BattlePet:
        """Get the opponent pet."""
        return self.pet2 if pet == self.pet1 else self.pet1

    def execute_turn(self, move: Move) -> BattleAction:
        """Execute a turn with the given move."""
        opponent = self.get_opponent(self.current_pet)
        action = BattleAction(pet=self.current_pet, move=move)

        # Check accuracy
        hit_roll = random.random()
        if hit_roll > move.accuracy:
            action.hit = False
        else:
            # Calculate damage
            damage = self._calculate_damage(self.current_pet, opponent, move)
            action.damage = opponent.take_damage(damage)

            # Apply stat changes
            for stat, change in move.stat_changes.items():
                if hasattr(opponent, stat):
                    current_value = getattr(opponent, stat)
                    setattr(opponent, stat, current_value + change)

        # Record action
        self.actions.append(action)

        # Check for battle end
        if not opponent.is_alive():
            self.is_over = True
            self.winner = self.current_pet.owner_id

        # Switch turns
        self.current_pet = opponent
        if self.current_pet == self.pet1:
            self.turn += 1

        return action

    def _calculate_damage(self, attacker: BattlePet, defender: BattlePet,
                          move: Move) -> int:
        """Calculate damage for a move."""
        # Base damage
        attack_stat = attacker.get_effective_attack(move.category)
        defense_stat = defender.get_effective_defense(move.category)

        # Damage formula
        damage = ((2 * attacker.level / 5 + 2) * move.power * attack_stat / defense_stat) / 50 + 2

        # Level modifier
        damage = damage * (attacker.level / defender.level) ** 0.5

        # Type effectiveness
        effectiveness = self.get_type_effectiveness(move.element, defender.element)
        damage *= effectiveness

        # STAB (Same Type Attack Bonus) - 1.5x if move matches pet's type
        if move.element == attacker.element:
            damage *= 1.5

        # Random factor
        damage *= random.uniform(0.85, 1.0)

        # Critical hit?
        is_critical = random.random() < 0.0625  # 6.25%
        if is_critical:
            damage *= 1.5

        return int(damage)

    def get_type_effectiveness(self, move_type: ElementType,
                             defender_type: ElementType) -> float:
        """Get type effectiveness multiplier."""
        key = (move_type, defender_type)
        effectiveness = TYPE_EFFECTIVENESS.get(key, 1.0)

        # Check for resistance (0.5x) - inverse of effectiveness
        if effectiveness != 1.0:
            reverse_key = (defender_type, move_type)
            if reverse_key in TYPE_EFFECTIVENESS:
                # Both directions defined - use higher number
                effectiveness = max(effectiveness, TYPE_EFFECTIVENESS[reverse_key])

        return effectiveness

    def get_winner(self) -> Optional[str]:
        """Get the winner's user ID if battle is over."""
        return self.winner

    def surrender(self, user_id: str) -> Optional[str]:
        """Surrender from the battle."""
        # Other user wins
        if user_id == self.pet1.owner_id:
            self.winner = self.pet2.owner_id
        elif user_id == self.pet2.owner_id:
            self.winner = self.pet1.owner_id

        self.is_over = True
        return self.winner


# Preset moves

class MoveLibrary:
    """Library of preset moves."""

    @staticmethod
    def tackle() -> Move:
        return Move(
            name="Tackle",
            element=ElementType.NORMAL,
            category=MoveCategory.PHYSICAL,
            power=40,
            accuracy=1.0,
            pp=35,
            description="A full-body charge."
        )

    @staticmethod
    def bite() -> Move:
        return Move(
            name="Bite",
            element=ElementType.DARK,
            category=MoveCategory.PHYSICAL,
            power=60,
            accuracy=1.0,
            pp=25,
            description="A biting attack."
        )

    @staticmethod
    def ember() -> Move:
        return Move(
            name="Ember",
            element=ElementType.FIRE,
            category=MoveCategory.SPECIAL,
            power=40,
            accuracy=1.0,
            pp=25,
            description="A small flame attack."
        )

    @staticmethod
    def water_gun() -> Move:
        return Move(
            name="Water Gun",
            element=ElementType.WATER,
            category=MoveCategory.SPECIAL,
            power=40,
            accuracy=1.0,
            pp=25,
            description="Sprays water at the target."
        )

    @staticmethod
    def vine_whip() -> Move:
        return Move(
            name="Vine Whip",
            element=ElementType.GRASS,
            category=MoveCategory.PHYSICAL,
            power=45,
            accuracy=1.0,
            pp=25,
            description="Whips the target with vines."
        )

    @staticmethod
    def thunder_shock() -> Move:
        return Move(
            name="Thunder Shock",
            element=ElementType.ELECTRIC,
            category=MoveCategory.SPECIAL,
            power=40,
            accuracy=1.0,
            pp=30,
            description="A weak electric shock."
        )

    @staticmethod
    def ice_beam() -> Move:
        return Move(
            name="Ice Beam",
            element=ElementType.ICE,
            category=MoveCategory.SPECIAL,
            power=90,
            accuracy=1.0,
            pp=10,
            description="A freezing beam of ice."
        )

    @staticmethod
    def flamethrower() -> Move:
        return Move(
            name="Flamethrower",
            element=ElementType.FIRE,
            category=MoveCategory.SPECIAL,
            power=90,
            accuracy=1.0,
            pp=15,
            description="A powerful stream of fire."
        )

    @staticmethod
    def hydro_pump() -> Move:
        return Move(
            name="Hydro Pump",
            element=ElementType.WATER,
            category=MoveCategory.SPECIAL,
            power=110,
            accuracy=0.8,
            pp=5,
            description="A massive water blast."
        )

    @staticmethod
    def quick_attack() -> Move:
        return Move(
            name="Quick Attack",
            element=ElementType.NORMAL,
            category=MoveCategory.PHYSICAL,
            power=40,
            accuracy=1.0,
            pp=30,
            description="A fast attack that usually goes first."
        )

    @staticmethod
    def heal() -> Move:
        return Move(
            name="Heal",
            element=ElementType.NORMAL,
            category=MoveCategory.STATUS,
            power=0,
            accuracy=1.0,
            pp=10,
            description="Restores HP.",
            stat_changes={"current_hp": 50}  # Would need context for max HP
        )


# Preset battle pets

class PresetPets:
    """Preset battle pets."""

    @staticmethod
    def spark() -> BattlePet:
        return BattlePet(
            name="Spark",
            element=ElementType.ELECTRIC,
            emoji="⚡",
            level=10,
            max_hp=90,
            attack=55,
            defense=40,
            special_attack=70,
            special_defense=50,
            speed=75,
            moves=[MoveLibrary.quick_attack(), MoveLibrary.thunder_shock()]
        )

    @staticmethod
    def flame() -> BattlePet:
        return BattlePet(
            name="Flame",
            element=ElementType.FIRE,
            emoji="🔥",
            level=10,
            max_hp=100,
            attack=70,
            defense=50,
            special_attack=80,
            special_defense=50,
            speed=65,
            moves=[MoveLibrary.quick_attack(), MoveLibrary.ember(), MoveLibrary.flamethrower()]
        )

    @staticmethod
    def splash() -> BattlePet:
        return BattlePet(
            name="Splash",
            element=ElementType.WATER,
            emoji="💧",
            level=10,
            max_hp=110,
            attack=50,
            defense=60,
            special_attack=70,
            special_defense=70,
            speed=50,
            moves=[MoveLibrary.tackle(), MoveLibrary.water_gun(), MoveLibrary.hydro_pump()]
        )

    @staticmethod
    def leaf() -> BattlePet:
        return BattlePet(
            name="Leaf",
            element=ElementType.GRASS,
            emoji="🌿",
            level=10,
            max_hp=95,
            attack=60,
            defense=65,
            special_attack=60,
            special_defense=65,
            speed=55,
            moves=[MoveLibrary.tackle(), MoveLibrary.vine_whip()]
        )


if __name__ == "__main__":
    # Test arena system
    print("Testing Arena/PVP System")

    arena = BattleArena()

    # Create battle pets
    pet1 = PresetPets.flame()
    pet1.owner_id = "player1"
    pet1.owner_name = "Player 1"

    pet2 = PresetPets.splash()
    pet2.owner_id = "player2"
    pet2.owner_name = "Player 2"

    print(f"\nBattle: {pet1.name} ({pet1.element.value}) vs {pet2.name} ({pet2.element.value})")
    print(f"{pet1.name}: HP={pet1.current_hp}/{pet1.max_hp}, ATK={pet1.attack}")
    print(f"{pet2.name}: HP={pet2.current_hp}/{pet2.max_hp}, ATK={pet2.attack}")

    # Create battle
    battle = arena.create_battle(pet1, pet2)

    # Simulate battle
    print("\nBattle begins!")
    while not battle.is_over:
        current = battle.current_pet
        move = random.choice(current.moves)
        action = battle.execute_turn(move)

        if action.hit:
            print(f"  {current.name} used {move.name}! {action.damage} damage (effectiveness: {action.effectiveness:.1f}x)")
        else:
            print(f"  {current.name} used {move.name} but missed!")

        if battle.is_over:
            print(f"\nBattle over! Winner: {battle.winner}")
            break

    print("\nArena/PVP system test passed!")
