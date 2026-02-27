"""
Multi-Pet Farm System for Claude Pet Companion

Allows raising multiple pets with:
- Pet farm management
- Pet interactions
- Resource management
"""

import random
import logging
import time
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PetState(Enum):
    """States of a pet."""
    SLEEPING = "sleeping"
    EATING = "eating"
    PLAYING = "playing"
    IDLE = "idle"
    WORKING = "working"
    EXPLORING = "exploring"
    SICK = "sick"


class PetType(Enum):
    """Types of pets."""
    CAT = "cat"
    DOG = "dog"
    RABBIT = "rabbit"
    HAMSTER = "hamster"
    BIRD = "bird"
    DRAGON = "dragon"
    UNICORN = "unicorn"
    FOX = "fox"


@dataclass
class FarmPet:
    """A pet in the farm."""
    id: str
    name: str
    pet_type: PetType
    emoji: str = "🐾"

    # Stats
    level: int = 1
    xp: int = 0
    xp_to_next: int = 100
    hunger: int = 100  # 0-100
    happiness: int = 100  # 0-100
    energy: int = 100  # 0-100
    health: int = 100  # 0-100

    # State
    current_state: PetState = PetState.IDLE
    state_start_time: float = 0

    # Appearance
    color: str = "#FFFFFF"
    accessory: str = ""

    # Personality
    playfulness: float = 0.5
    independence: float = 0.5
    affection: float = 0.5

    # Skills
    skills: List[str] = field(default_factory=list)

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return f"{self.emoji} {self.name} (Lv.{self.level})"

    def get_xp_progress(self) -> float:
        """Get XP progress (0-1)."""
        return self.xp / self.xp_to_next

    def add_xp(self, amount: int) -> bool:
        """Add XP, return True if leveled up."""
        self.xp += amount

        leveled = False
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.5)
            leveled = True

        return leveled

    def is_alive(self) -> bool:
        """Check if pet is alive."""
        return self.health > 0

    def update(self, dt: float):
        """Update pet state over time."""
        # Decay stats
        if self.current_state != PetState.SLEEPING:
            self.hunger = max(0, self.hunger - 0.5)
            self.happiness = max(0, self.happiness - 0.3)

        # Recovery during sleep
        if self.current_state == PetState.SLEEPING:
            self.energy = min(100, self.energy + 2.0)
            self.health = min(100, self.health + 0.5)

        # Check for death
        if self.hunger <= 0 or self.health <= 0:
            self.health = 0

        # State transitions
        if self.current_state != PetState.IDLE:
            if time.time() - self.state_start_time > 30:  # State lasts 30 seconds max
                self.set_state(PetState.IDLE)

    def set_state(self, state: PetState):
        """Set pet state."""
        self.current_state = state
        self.state_start_time = time.time()

    def get_primary_need(self) -> str:
        """Get the pet's most urgent need."""
        needs = {
            'hunger': self.hunger,
            'happiness': self.happiness,
            'energy': self.energy,
        }

        lowest = min(needs.items(), key=lambda x: x[1])
        return lowest[0]


class PetFarm:
    """Manages multiple pets."""

    def __init__(self, max_pets: int = 10):
        self.max_pets = max_pets
        self.pets: Dict[str, FarmPet] = {}
        self.active_pet_id: Optional[str] = None

        # Resources
        self.food: int = 100
        self.money: int = 1000
        self.toys: List[str] = []

        # Farm upgrade level
        self.farm_level: int = 1

    def add_pet(self, pet: FarmPet) -> bool:
        """Add a pet to the farm."""
        if len(self.pets) >= self.max_pets:
            return False

        self.pets[pet.id] = pet

        # Set as active if first pet
        if not self.active_pet_id:
            self.active_pet_id = pet.id

        return True

    def remove_pet(self, pet_id: str) -> bool:
        """Remove a pet from the farm."""
        if pet_id in self.pets:
            if pet_id == self.active_pet_id:
                self.active_pet_id = None

            del self.pets[pet_id]
            return True
        return False

    def get_pet(self, pet_id: str) -> Optional[FarmPet]:
        """Get a pet by ID."""
        return self.pets.get(pet_id)

    def get_active_pet(self) -> Optional[FarmPet]:
        """Get the currently active pet."""
        if self.active_pet_id:
            return self.pets.get(self.active_pet_id)
        return None

    def set_active_pet(self, pet_id: str) -> bool:
        """Set the active pet."""
        if pet_id in self.pets:
            self.active_pet_id = pet_id
            return True
        return False

    def feed_pet(self, pet_id: str) -> bool:
        """Feed a pet."""
        pet = self.get_pet(pet_id)
        if pet and self.food > 0:
            pet.hunger = min(100, pet.hunger + 30)
            pet.happiness = min(100, pet.happiness + 5)
            self.food -= 1
            return True
        return False

    def feed_all_pets(self) -> int:
        """Feed all pets. Returns number fed."""
        fed = 0
        for pet_id in self.pets:
            if self.feed_pet(pet_id):
                fed += 1
        return fed

    def play_with_pet(self, pet_id: str) -> bool:
        """Play with a pet."""
        pet = self.get_pet(pet_id)
        if pet:
            pet.set_state(PetState.PLAYING)
            pet.happiness = min(100, pet.happiness + 15)
            pet.energy = max(0, pet.energy - 10)
            pet.add_xp(5)
            return True
        return False

    def make_pets_interact(self) -> List[str]:
        """Make pets interact with each other."""
        interactions = []

        pet_list = list(self.pets.values())
        if len(pet_list) < 2:
            return interactions

        # Random interactions
        for _ in range(min(5, len(pet_list) * 2)):
            pet1, pet2 = random.sample(pet_list, 2)

            interaction = self._do_interaction(pet1, pet2)
            if interaction:
                interactions.append(interaction)
                pet1.add_xp(2)
                pet2.add_xp(2)

        return interactions

    def _do_interaction(self, pet1: FarmPet, pet2: FarmPet) -> Optional[str]:
        """Perform an interaction between two pets."""
        actions = [
            f"{pet1.name} and {pet2.name} play together",
            f"{pet1.name} nuzzles {pet2.name}",
            f"{pet2.name} grooms {pet1.name}",
            f"{pet1.name} and {pet2.name} nap together",
            f"{pet1.name} chases {pet2.name}",
            f"{pet1.name} shares with {pet2.name}",
        ]

        return random.choice(actions)

    def get_farm_status(self) -> Dict:
        """Get overall farm status."""
        alive_pets = [p for p in self.pets.values() if p.is_alive()]

        total_level = sum(p.level for p in alive_pets)
        avg_happiness = 0
        avg_hunger = 0

        if alive_pets:
            avg_happiness = sum(p.happiness for p in alive_pets) / len(alive_pets)
            avg_hunger = sum(p.hunger for p in alive_pets) / len(alive_pets)

        return {
            'total_pets': len(self.pets),
            'alive_pets': len(alive_pets),
            'total_level': total_level,
            'avg_happiness': f"{avg_happiness:.1f}",
            'avg_hunger': f"{avg_hunger:.1f}",
            'food': self.food,
            'money': self.money,
            'farm_level': self.farm_level,
        }

    def update(self, dt: float = 1.0):
        """Update all pets."""
        for pet in self.pets.values():
            if pet.is_alive():
                pet.update(dt)

    def collect_resources(self) -> int:
        """Collect resources from pets (like in idle games)."""
        collected = 0

        for pet in self.pets.values():
            if pet.is_alive():
                # Pets generate small income
                income = pet.level * 2
                self.money += income
                collected += income

        return collected

    def upgrade_farm(self) -> bool:
        """Upgrade the farm to hold more pets."""
        cost = self.farm_level * 5000

        if self.money >= cost:
            self.money -= cost
            self.farm_level += 1
            self.max_pets += 5
            return True
        return False


# Preset pets

class PresetFarmPets:
    """Preset farm pets."""

    @staticmethod
    def create_random_pet(index: int = 0) -> FarmPet:
        """Create a random pet."""
        types = list(PetType)
        pet_type = random.choice(types)

        # Emojis by type
        emojis = {
            PetType.CAT: ["🐱", "😸", "😺"],
            PetType.DOG: ["🐕", "🐶", "🐩"],
            PetType.RABBIT: ["🐰", "🐇"],
            PetType.HAMSTER: ["🐹", "🐭"],
            PetType.BIRD: ["🐦", "🐧", "🐥"],
            PetType.DRAGON: ["🐉", "🐲"],
            PetType.UNICORN: ["🦄", "🐴"],
            PetType.FOX: ["🦊"],
        }

        names = [
            "Whiskers", "Fluffy", "Buddy", "Max", "Bella",
            "Charlie", "Luna", "Rocky", "Coco", "Daisy",
            "Duke", "Elvis", "Felix", "Ginger", "Hunter",
            "Shadow", "Lucky", "Milo", "Oliver", "Pepper",
        ]

        colors = ["#FFFFFF", "#FFD700", "#FF69B4", "#87CEEB", "#98FB98", "#DDA0DD"]

        pet = FarmPet(
            id=f"pet_{index}_{random.randint(1000, 9999)}",
            name=random.choice(names),
            pet_type=pet_type,
            emoji=random.choice(emojis.get(pet_type, ["🐾"])[0]),
            color=random.choice(colors),
            playfulness=random.uniform(0.2, 0.8),
            independence=random.uniform(0.2, 0.8),
            affection=random.uniform(0.2, 0.8),
        )

        return pet


def create_farm(num_pets: int = 3) -> PetFarm:
    """Create a farm with random pets."""
    farm = PetFarm(max_pets=10)

    for i in range(num_pets):
        pet = PresetFarmPets.create_random_pet(i)
        farm.add_pet(pet)

    return farm


if __name__ == "__main__":
    # Test multi-pet farm
    print("Testing Multi-Pet Farm System")

    farm = create_farm(5)

    print(f"\nFarm created with {len(farm.pets)} pets:")
    for pet in farm.pets.values():
        print(f"  {pet}")

    # Test interactions
    print("\nPet interactions:")
    interactions = farm.make_pets_interact()
    for interaction in interactions[:3]:
        print(f"  {interaction}")

    # Feed all pets
    fed = farm.feed_all_pets()
    print(f"\nFed {fed} pets")

    # Play with active pet
    active = farm.get_active_pet()
    if active:
        farm.play_with_pet(active.id)
        print(f"\nPlayed with {active.name}")
        print(f"  Happiness: {active.happiness}")
        print(f"  XP progress: {active.get_xp_progress():.1%}")

    # Collect resources
    collected = farm.collect_resources()
    print(f"\nCollected {collected} coins")

    # Farm status
    print(f"\nFarm status:")
    status = farm.get_farm_status()
    for key, value in status.items():
        print(f"  {key}: {value}")

    print("\nMulti-pet farm test passed!")
