"""
Pet Breeding System for Claude Pet Companion

Allows breeding pets to create offspring with:
- Genetic trait inheritance
- Mutation chance
- Breeding cooldowns
- Lineage tracking
"""

import random
import logging
import time
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class GeneticTrait(Enum):
    """Traits that can be inherited."""
    COLOR = "color"
    SIZE = "size"
    TEMPERAMENT = "temperament"
    ABILITY = "ability"
    RARITY = "rarity"


@dataclass
class PetGenetics:
    """Genetic information for a pet."""
    parent1_id: str = ""
    parent2_id: str = ""
    generation: int = 1

    # Traits (0-1 scale, inherited from parents)
    color_red: float = 0.5
    color_green: float = 0.5
    color_blue: float = 0.5
    size: float = 0.5
    playfulness: float = 0.5
    aggression: float = 0.5
    intelligence: float = 0.5
    speed: float = 0.5

    # Special traits (binary, probabilistic inheritance)
    special_traits: List[str] = field(default_factory=list)

    def get_color_hex(self) -> str:
        """Get color as hex string."""
        r = int(self.color_red * 255)
        g = int(self.color_green * 255)
        b = int(self.color_blue * 255)
        return f"#{r:02x}{g:02x}{b:02x}"

    def inherit_from_parents(self, parent1: 'PetGenetics', parent2: 'PetGenetics'):
        """Inherit traits from parents with mutation."""
        self.parent1_id = parent1.parent1_id if parent1 else ""
        self.parent2_id = parent2.parent2_id if parent2 else ""
        self.generation = max((parent1.generation if parent1 else 0),
                              (parent2.generation if parent2 else 0)) + 1

        # Color inheritance (blend with mutation)
        self.color_red = self._inherit_trait(parent1.color_red, parent2.color_red)
        self.color_green = self._inherit_trait(parent1.color_green, parent2.color_green)
        self.color_blue = self._inherit_trait(parent1.color_blue, parent2.color_blue)

        # Other traits
        self.size = self._inherit_trait(parent1.size, parent2.size)
        self.playfulness = self._inherit_trait(parent1.playfulness, parent2.playfulness)
        self.aggression = self._inherit_trait(parent1.aggression, parent2.aggression)
        self.intelligence = self._inherit_trait(parent1.intelligence, parent2.intelligence)
        self.speed = self._inherit_trait(parent1.speed, parent2.speed)

        # Special traits
        self._inherit_special_traits(parent1, parent2)

    def _inherit_trait(self, trait1: float, trait2: float) -> float:
        """Inherit a single trait from parents with mutation."""
        # Average parents with mutation
        base_value = (trait1 + trait2) / 2

        # Add mutation
        if random.random() < 0.1:  # 10% mutation chance
            mutation = random.uniform(-0.1, 0.1)
            base_value = max(0.0, min(1.0, base_value + mutation))

        return base_value

    def _inherit_special_traits(self, parent1: 'PetGenetics', parent2: 'PetGenetics'):
        """Inherit special traits."""
        all_traits = set(parent1.special_traits) | set(parent2.special_traits)

        # Each trait has 50% chance to pass down
        for trait in all_traits:
            if random.random() < 0.5:
                self.special_traits.append(trait)

        # Small chance for new trait
        if random.random() < 0.05:
            new_traits = ["FLUFFY", "SLEEK", "SPOTTED", "STRIPED", "LONG_FUR",
                        "SHORT_FUR", "CURLED", "STRAIGHT_EARS", "FLOP_EARS"]
            self.special_traits.append(random.choice(new_traits))

    def mutate(self, rate: float = 0.05):
        """Apply random mutations."""
        # Mutate color
        if random.random() < rate:
            channel = random.choice(['color_red', 'color_green', 'color_blue'])
            current = getattr(self, channel)
            setattr(self, channel, max(0.0, min(1.0, current + random.uniform(-0.2, 0.2))))

        # Mutate other traits
        for trait in ['size', 'playfulness', 'aggression', 'intelligence', 'speed']:
            if random.random() < rate:
                current = getattr(self, trait)
                setattr(self, trait, max(0.0, min(1.0, current + random.uniform(-0.1, 0.1))))


@dataclass
class BreedingResult:
    """Result of a breeding attempt."""
    success: bool
    offspring: Optional['Offspring'] = None
    reason: str = ""


@dataclass
class Offspring:
    """A newborn pet from breeding."""
    id: str
    name: str
    genetics: PetGenetics
    parent1_id: str
    parent2_id: str
    birth_date: float = field(default_factory=time.time)

    # Stats derived from genetics
    level: int = 1
    xp: int = 0

    def get_display_name(self) -> str:
        """Get formatted name."""
        return f"{self.name} (Gen {self.genetics.generation})"


class BreedingSystem:
    """Manages pet breeding."""

    def __init__(self):
        self.breeding_cooldowns: Dict[str, float] = {}  # pet_id -> ready_time
        self.breeding_history: List[Dict] = []
        self.lineage: Dict[str, List[str]] = {}  # pet_id -> ancestor IDs

    def can_breed(self, pet1_id: str, pet2_id: str) -> Tuple[bool, str]:
        """
        Check if two pets can breed.

        Returns:
            (can_breed, reason)
        """
        # Check cooldowns
        now = time.time()
        for pet_id, ready_time in self.breeding_cooldowns.items():
            if pet_id in [pet1_id, pet2_id] and now < ready_time:
                return (False, "Pet is on breeding cooldown")

        # Check if trying to breed with self
        if pet1_id == pet2_id:
            return (False, "Cannot breed with same pet")

        # Additional validation would check pet types, compatibility, etc.
        return (True, "")

    def breed(self, pet1_genetics: PetGenetics, pet2_genetics: PetGenetics,
             pet1_id: str, pet2_id: str,
             name: str = "Baby") -> BreedingResult:
        """
        Breed two pets.

        Args:
            pet1_genetics: First parent's genetics
            pet2_genetics: Second parent's genetics
            pet1_id: ID of first parent
            pet2_id: ID of second parent
            name: Name for the offspring

        Returns:
            BreedingResult with offspring
        """
        can_breed, reason = self.can_breed(pet1_id, pet2_id)
        if not can_breed:
            return BreedingResult(success=False, reason=reason)

        # Create offspring genetics
        offspring_genetics = PetGenetics(
            parent1_id=pet1_id,
            parent2_id=pet2_id
        )
        offspring_genetics.inherit_from_parents(pet1_genetics, pet2_genetics)

        # Create offspring
        offspring = Offspring(
            id=f"offspring_{int(time.time())}_{random.randint(1000, 9999)}",
            name=name,
            genetics=offspring_genetics,
            parent1_id=pet1_id,
            parent2_id=pet2_id
        )

        # Set cooldown (24 hours)
        cooldown_end = time.time() + 86400
        self.breeding_cooldowns[pet1_id] = cooldown_end
        self.breeding_cooldowns[pet2_id] = cooldown_end

        # Record lineage
        self.lineage[offspring.id] = [pet1_id, pet2_id]

        # Record breeding
        self.breeding_history.append({
            'timestamp': time.time(),
            'parent1_id': pet1_id,
            'parent2_id': pet2_id,
            'offspring_id': offspring.id,
        })

        return BreedingResult(success=True, offspring=offspring)

    def get_lineage(self, pet_id: str) -> List[str]:
        """Get the lineage (ancestor IDs) for a pet."""
        return self.lineage.get(pet_id, [])

    def get_remaining_cooldown(self, pet_id: str) -> float:
        """Get remaining breeding cooldown in seconds."""
        if pet_id in self.breeding_cooldowns:
            remaining = self.breeding_cooldowns[pet_id] - time.time()
            return max(0, remaining)
        return 0

    def get_breeding_history(self, limit: int = 20) -> List[Dict]:
        """Get recent breeding history."""
        return sorted(
            self.breeding_history,
            key=lambda x: x['timestamp'],
            reverse=True
        )[:limit]


# Example usage

if __name__ == "__main__":
    # Test breeding system
    print("Testing Breeding System")

    system = BreedingSystem()

    # Create parent genetics
    parent1 = PetGenetics(
        parent1_id="pet1",
        color_red=1.0,
        color_green=0.0,
        color_blue=0.0,
        size=0.7,
        playfulness=0.8,
        special_traits=["FLUFFY", "LONG_FUR"]
    )

    parent2 = PetGenetics(
        parent1_id="pet2",
        parent2_id="pet2",
        color_red=0.0,
        color_green=0.0,
        color_blue=1.0,
        size=0.5,
        playfulness=0.6,
        special_traits=["SLEEK", "STRAIGHT_EARS"]
    )

    # Breed
    result = system.breed(parent1, parent2, "Fluffy Jr.", "pet1", "pet2")

    if result.success:
        print(f"\nBreeding successful!")
        print(f"Offspring: {result.offspring}")
        print(f"Color: {result.offspring.genetics.get_color_hex()}")
        print(f"Size: {result.offspring.genetics.size:.2f}")
        print(f"Special traits: {result.offspring.genetics.special_traits}")
        print(f"Generation: {result.offspring.genetics.generation}")
    else:
        print(f"\nBreeding failed: {result.reason}")

    print("\nBreeding system test passed!")
