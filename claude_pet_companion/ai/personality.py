"""
Personality System for Claude Pet Companion

Provides unique, evolving personalities with:
- Trait-based personality model
- Five Factor Model (Big Five) integration
- Personality evolution based on experiences
- Behavioral influence
- Quirks and preferences
"""

import logging
import random
import time
from typing import Dict, List, Tuple, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TraitType(Enum):
    """Categories of personality traits."""
    # Big Five traits
    OPENNESS = "openness"          # Openness to experience
    CONSCIENTIOUSNESS = "conscientiousness"  # Self-discipline
    EXTRAVERSION = "extraversion"  # Social energy
    AGREEABLENESS = "agreeableness" # Cooperation
    NEUROTICISM = "neuroticism"    # Emotional stability

    # Additional traits
    PLAYFULNESS = "playfulness"
    CURIOSITY = "curiosity"
    LAZINESS = "laziness"
    BOLDNESS = "boldness"
    INDEPENDENCE = "independence"
    AFFECTION = "affection"
    STUBBORNNESS = "stubbornness"
    GLUTTONY = "gluttony"


@dataclass
class Trait:
    """A personality trait with value (0-1)."""
    trait_type: TraitType
    value: float = 0.5  # 0.0 = low, 1.0 = high
    volatility: float = 0.01  # How much the trait can change over time

    def __post_init__(self):
        self.value = max(0.0, min(1.0, self.value))

    def increase(self, amount: float = 0.01):
        """Increase trait value."""
        self.value = min(1.0, self.value + amount)

    def decrease(self, amount: float = 0.01):
        """Decrease trait value."""
        self.value = max(0.0, self.value - amount)

    def drift(self):
        """Apply random drift to trait value."""
        change = random.uniform(-self.volatility, self.volatility)
        self.value = max(0.0, min(1.0, self.value + change))

    def get_description(self) -> str:
        """Get text description of trait value."""
        if self.value < 0.2:
            return self._get_low_description()
        elif self.value < 0.4:
            return self._get_below_average_description()
        elif self.value < 0.6:
            return self._get_average_description()
        elif self.value < 0.8:
            return self._get_above_average_description()
        else:
            return self._get_high_description()

    def _get_low_description(self) -> str:
        low_names = {
            TraitType.OPENNESS: "Conservative",
            TraitType.CONSCIENTIOUSNESS: "Careless",
            TraitType.EXTRAVERSION: "Introverted",
            TraitType.AGREEABLENESS: "Independent",
            TraitType.NEUROTICISM: "Calm",
            TraitType.PLAYFULNESS: "Serious",
            TraitType.CURIOSITY: "Indifferent",
            TraitType.LAZINESS: "Energetic",
            TraitType.BOLDNESS: "Shy",
            TraitType.INDEPENDENCE: "Dependent",
            TraitType.AFFECTION: "Distant",
            TraitType.STUBBORNNESS: "Flexible",
            TraitType.GLUTTONY: "Picky",
        }
        return low_names.get(self.trait_type, "Low")

    def _get_high_description(self) -> str:
        high_names = {
            TraitType.OPENNESS: "Adventurous",
            TraitType.CONSCIENTIOUSNESS: "Diligent",
            TraitType.EXTRAVERSION: "Extroverted",
            TraitType.AGREEABLENESS: "Cooperative",
            TraitType.NEUROTICISM: "Anxious",
            TraitType.PLAYFULNESS: "Playful",
            TraitType.CURIOSITY: "Curious",
            TraitType.LAZINESS: "Lazy",
            TraitType.BOLDNESS: "Bold",
            TraitType.INDEPENDENCE: "Independent",
            TraitType.AFFECTION: "Affectionate",
            TraitType.STUBBORNNESS: "Stubborn",
            TraitType.GLUTTONY: "Gluttonous",
        }
        return high_names.get(self.trait_type, "High")

    def _get_below_average_description(self) -> str:
        return self._get_low_description() + "-ish"

    def _get_average_description(self) -> str:
        return "Balanced"

    def _get_above_average_description(self) -> str:
        return self._get_high_description() + "-ish"


class Quirk(Enum):
    """Unique personality quirks."""
    CHASES_TAIL = "chases_tail"
    TALKATIVE = "talkative"
    DRAMATIC = "dramatic"
    CLUMSY = "clumsy"
    SNOOPY = "snoopy"
    NAP_LOVER = "nap_lover"
    FOOD_MOTIVATED = "food_motivated"
    ATTENTION_SEEKER = "attention_seeker"
    SHY_STRANGER = "shy_stranger"
    BRAVE = "brave"
    MISCHIEVOUS = "mischievous"
    GENTLE = "gentle"
    VOCAL = "vocal"
    LAP_LOVER = "lap_lover"
    FETCH_LOVER = "fetch_lover"
    WATER_LOVER = "water_lover"
    SCAREDY_CAT = "scaredy_cat"
    COUCH_POTATO = "couch_potato"
    EARLY_BIRD = "early_bird"
    NIGHT_OWL = "night_owl"
    GREEDY = "greedy"
    GENEROUS = "generous"


class PersonalityArchetype(Enum):
    """Predefined personality archetypes."""
    HERO = "hero"
    TRICKSTER = "trickster"
    SAGE = "sage"
    EXPLORER = "explorer"
    CAREGIVER = "caregiver"
    REBEL = "rebel"
    LOVER = "lover"
    JESTER = "jester"
    EVERYMAN = "everyman"
    INNOCENT = "innocent"


@dataclass
class Preference:
    """A preference for something."""
    category: str  # "food", "activity", "toy", etc.
    item: str
    affinity: float = 0.5  # 0 = hates, 1 = loves

    def update_affinity(self, delta: float):
        """Update preference affinity."""
        self.affinity = max(0.0, min(1.0, self.affinity + delta))


@dataclass
class MemoryInfluence:
    """How a memory influenced personality."""
    event_type: str
    traits_affected: Dict[TraitType, float]
    timestamp: float = field(default_factory=time.time)


class Personality:
    """
    Complete personality system for a pet.

    Combines traits, quirks, preferences, and memories
    to create a unique, evolving personality.
    """

    def __init__(self, archetype: PersonalityArchetype = None):
        self.traits: Dict[TraitType, Trait] = {}
        self.quirks: Set[Quirk] = set()
        self.preferences: Dict[str, List[Preference]] = {}
        self.archetype = archetype
        self.memory_influences: List[MemoryInfluence] = []

        # Personality age (number of interactions experienced)
        self.personality_age = 0

        # Initialize traits
        self._initialize_traits()

        # Apply archetype if provided
        if archetype:
            self._apply_archetype(archetype)

        # Random quirks
        self._generate_quirks()

    def _initialize_traits(self):
        """Initialize all traits with random values."""
        for trait_type in TraitType:
            # Start with moderate random values
            base_value = random.uniform(0.3, 0.7)
            volatility = random.uniform(0.005, 0.02)
            self.traits[trait_type] = Trait(trait_type, base_value, volatility)

    def _apply_archetype(self, archetype: PersonalityArchetype):
        """Apply trait modifiers for an archetype."""
        modifiers = ARCHETYPE_TRAIT_MODIFIERS.get(archetype, {})
        for trait_type, modifier in modifiers.items():
            if trait_type in self.traits:
                self.traits[trait_type].value = max(0.0, min(1.0,
                    self.traits[trait_type].value + modifier))

    def _generate_quirks(self):
        """Generate random quirks based on traits."""
        possible_quirks = list(Quirk)

        # Number of quirks based on openness and neuroticism
        openness = self.traits[TraitType.OPENNESS].value
        neuroticism = self.traits[TraitType.NEUROTICISM].value

        num_quirks = int(openness * 3 + random.random() * 2)

        for _ in range(num_quirks):
            if possible_quirks:
                quirk = random.choice(possible_quirks)
                self.quirks.add(quirk)

    def get_trait(self, trait_type: TraitType) -> float:
        """Get value of a trait."""
        return self.traits.get(trait_type, Trait(trait_type, 0.5)).value

    def set_trait(self, trait_type: TraitType, value: float):
        """Set a trait value."""
        if trait_type not in self.traits:
            self.traits[trait_type] = Trait(trait_type, value)
        else:
            self.traits[trait_type].value = max(0.0, min(1.0, value))

    def has_quirk(self, quirk: Quirk) -> bool:
        """Check if pet has a quirk."""
        return quirk in self.quirks

    def add_quirk(self, quirk: Quirk):
        """Add a quirk."""
        self.quirks.add(quirk)

    def remove_quirk(self, quirk: Quirk):
        """Remove a quirk."""
        self.quirks.discard(quirk)

    def get_preference(self, category: str, item: str) -> float:
        """Get affinity for a specific item in a category."""
        if category not in self.preferences:
            return 0.5  # Neutral

        for pref in self.preferences[category]:
            if pref.item == item:
                return pref.affinity

        return 0.5  # Neutral if not found

    def set_preference(self, category: str, item: str, affinity: float):
        """Set preference for an item."""
        if category not in self.preferences:
            self.preferences[category] = []

        # Check if preference exists
        for pref in self.preferences[category]:
            if pref.item == item:
                pref.affinity = max(0.0, min(1.0, affinity))
                return

        # Add new preference
        self.preferences[category].append(Preference(category, item, affinity))

    def update_preference(self, category: str, item: str, delta: float):
        """Update preference affinity."""
        current = self.get_preference(category, item)
        self.set_preference(category, item, current + delta)

    def process_experience(self, event_type: str, context: Dict = None):
        """
        Process an experience that may influence personality.

        Args:
            event_type: Type of event
            context: Additional context
        """
        context = context or {}
        self.personality_age += 1

        # Get trait influences for this event
        influences = EVENT_PERSONALITY_INFLUENCES.get(event_type, {})

        traits_affected = {}
        for trait_type, influence in influences.items():
            # Apply personality-based modifier
            base_influence = influence * 0.01  # Small changes

            # Context modifiers
            if event_type == "petted" and context.get("affection") == "high":
                if trait_type == TraitType.AFFECTION:
                    base_influence *= 2

            # Apply change
            if trait_type in self.traits:
                self.traits[trait_type].value += base_influence
                self.traits[trait_type].value = max(0.0, min(1.0, self.traits[trait_type].value))
                traits_affected[trait_type] = base_influence

        # Record significant influences
        if any(abs(v) > 0.02 for v in traits_affected.values()):
            self.memory_influences.append(MemoryInfluence(
                event_type=event_type,
                traits_affected=traits_affected
            ))

        # Clean old influences
        self._clean_old_influences()

    def evolve(self, dt: float = 1.0):
        """
        Evolve personality over time.

        Args:
            dt: Time delta in arbitrary units
        """
        # Apply drift to traits
        for trait in self.traits.values():
            trait.drift()

        # Natural tendency toward center (regression to mean)
        for trait in self.traits.values():
            if trait.value > 0.7:
                trait.decrease(0.001 * dt)
            elif trait.value < 0.3:
                trait.increase(0.001 * dt)

    def get_description(self) -> str:
        """Get a text description of the personality."""
        dominant_traits = []
        for trait_type, trait in sorted(self.traits.items(),
                                       key=lambda x: x[1].value, reverse=True):
            if trait.value > 0.65 or trait.value < 0.35:
                dominant_traits.append(trait.get_description())

        if not dominant_traits:
            return "A balanced personality."

        desc = "Personality: " + ", ".join(dominant_traits[:3])

        if self.quirks:
            quirk_names = [q.value.replace("_", " ") for q in list(self.quirks)[:3]]
            desc += f"\nQuirks: {', '.join(quirk_names)}"

        return desc

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of personality for display."""
        return {
            "archetype": self.archetype.value if self.archetype else "none",
            "traits": {t.value: round(v.value, 2) for t, v in self.traits.items()},
            "quirks": [q.value for q in self.quirks],
            "personality_age": self.personality_age,
        }

    def _clean_old_influences(self):
        """Remove old memory influences."""
        cutoff = time.time() - 30 * 24 * 3600  # 30 days
        self.memory_influences = [
            m for m in self.memory_influences
            if m.timestamp > cutoff
        ]


# Archetype trait modifiers

ARCHETYPE_TRAIT_MODIFIERS = {
    PersonalityArchetype.HERO: {
        TraitType.BOLDNESS: 0.3,
        TraitType.EXTRAVERSION: 0.2,
        TraitType.AGREEABLENESS: 0.2,
        TraitType.CONSCIENTIOUSNESS: 0.1,
    },
    PersonalityArchetype.TRICKSTER: {
        TraitType.PLAYFULNESS: 0.4,
        TraitType.EXTRAVERSION: 0.3,
        TraitType.CURIOSITY: 0.3,
        TraitType.NEUROTICISM: -0.1,
    },
    PersonalityArchetype.SAGE: {
        TraitType.OPENNESS: 0.4,
        TraitType.CONSCIENTIOUSNESS: 0.3,
        TraitType.CURIOSITY: 0.2,
        TraitType.EXTRAVERSION: -0.2,
    },
    PersonalityArchetype.EXPLORER: {
        TraitType.OPENNESS: 0.5,
        TraitType.BOLDNESS: 0.3,
        TraitType.CURIOSITY: 0.4,
        TraitType.INDEPENDENCE: 0.2,
    },
    PersonalityArchetype.CAREGIVER: {
        TraitType.AGREEABLENESS: 0.4,
        TraitType.AFFECTION: 0.5,
        TraitType.EXTRAVERSION: 0.1,
        TraitType.NEUROTICISM: -0.2,
    },
    PersonalityArchetype.REBEL: {
        TraitType.STUBBORNNESS: 0.4,
        TraitType.INDEPENDENCE: 0.4,
        TraitType.BOLDNESS: 0.2,
        TraitType.AGREEABLENESS: -0.3,
    },
    PersonalityArchetype.LOVER: {
        TraitType.AFFECTION: 0.5,
        TraitType.AGREEABLENESS: 0.3,
        TraitType.EXTRAVERSION: 0.2,
        TraitType.PLAYFULNESS: 0.2,
    },
    PersonalityArchetype.JESTER: {
        TraitType.PLAYFULNESS: 0.5,
        TraitType.EXTRAVERSION: 0.4,
        TraitType.OPENNESS: 0.2,
        TraitType.CONSCIENTIOUSNESS: -0.2,
    },
    PersonalityArchetype.EVERYMAN: {
        # Balanced - no strong modifiers
    },
    PersonalityArchetype.INNOCENT: {
        TraitType.AGREEABLENESS: 0.3,
        TraitType.EXTRAVERSION: 0.1,
        TraitType.NEUROTICISM: -0.3,
        TraitType.BOLDNESS: -0.2,
    },
}


# Event influences on personality traits
# Positive = increase trait, Negative = decrease trait

EVENT_PERSONALITY_INFLUENCES = {
    # Positive interactions
    "petted": {
        TraitType.AFFECTION: 2,
        TraitType.EXTRAVERSION: 0.5,
        TraitType.AGREEABLENESS: 0.5,
    },
    "fed": {
        TraitType.AGREEABLENESS: 0.3,
        TraitType.GLUTTONY: 0.5,
    },
    "played": {
        TraitType.PLAYFULNESS: 1,
        TraitType.EXTRAVERSION: 0.5,
    },
    "praised": {
        TraitType.CONSCIENTIOUSNESS: 0.5,
        TraitType.AGREEABLENESS: 0.3,
    },
    "scolded": {
        TraitType.AGREEABLENESS: -1,
        TraitType.NEUROTICISM: 1,
        TraitType.STUBBORNNESS: 0.3,
    },
    "new_experience": {
        TraitType.OPENNESS: 1,
        TraitType.BOLDNESS: 0.5,
        TraitType.CURIOSITY: 0.5,
    },
    "met_stranger": {
        TraitType.EXTRAVERSION: 0.5 if random.random() > 0.3 else -0.5,
        TraitType.BOLDNESS: 0.3,
    },
    "won_game": {
        TraitType.BOLDNESS: 1,
        TraitType.PLAYFULNESS: 0.5,
    },
    "lost_game": {
        TraitType.STUBBORNNESS: 0.3,
    },
    "explored": {
        TraitType.OPENNESS: 1,
        TraitType.CURIOSITY: 0.5,
        TraitType.INDEPENDENCE: 0.3,
    },
}


class PersonalityBuilder:
    """Builder for creating custom personalities."""

    def __init__(self):
        self._traits = {}
        self._quirks = set()
        self._archetype = None

    def trait(self, trait_type: TraitType, value: float) -> 'PersonalityBuilder':
        """Set a trait value."""
        self._traits[trait_type] = value
        return self

    def quirk(self, quirk: Quirk) -> 'PersonalityBuilder':
        """Add a quirk."""
        self._quirks.add(quirk)
        return self

    def archetype(self, archetype: PersonalityArchetype) -> 'PersonalityBuilder':
        """Set the archetype."""
        self._archetype = archetype
        return self

    def build(self) -> Personality:
        """Build the personality."""
        personality = Personality(self._archetype)

        # Apply custom traits
        for trait_type, value in self._traits.items():
            personality.set_trait(trait_type, value)

        # Apply custom quirks
        for quirk in self._quirks:
            personality.add_quirk(quirk)

        return personality


# Convenience functions

def create_random_personality() -> Personality:
    """Create a personality with random traits."""
    return Personality(random.choice(list(PersonalityArchetype)))


def create_personality(archetype: PersonalityArchetype) -> Personality:
    """Create a personality with a specific archetype."""
    return Personality(archetype)


def build_personality() -> PersonalityBuilder:
    """Start building a custom personality."""
    return PersonalityBuilder()


if __name__ == "__main__":
    # Test personality system
    print("Testing Personality System")

    # Test random personality
    print("\nRandom Personality:")
    p1 = create_random_personality()
    print(p1.get_description())

    # Test archetype
    print("\nTrickster Archetype:")
    p2 = create_personality(PersonalityArchetype.TRICKSTER)
    print(p2.get_description())

    # Test builder
    print("\nCustom Personality:")
    p3 = (build_personality()
          .trait(TraitType.PLAYFULNESS, 0.9)
          .trait(TraitType.AFFECTION, 0.8)
          .trait(TraitType.LAZINESS, 0.2)
          .quirk(Quirk.FETCH_LOVER)
          .quirk(Quirk.WATER_LOVER)
          .build())
    print(p3.get_description())

    # Test experience processing
    print("\nProcessing experiences:")
    for event in ["petted", "played", "petted", "fed", "praised", "scolded"]:
        p3.process_experience(event)
        print(f"  After {event}: Affection={p3.get_trait(TraitType.AFFECTION):.2f}")

    # Test preferences
    print("\nPreferences:")
    p3.set_preference("food", "fish", 0.9)
    p3.set_preference("food", "vegetables", 0.2)
    print(f"  Fish affinity: {p3.get_preference('food', 'fish')}")
    print(f"  Vegetable affinity: {p3.get_preference('food', 'vegetables')}")
    print(f"  Meat affinity (new): {p3.get_preference('food', 'meat')}")

    # Test evolution
    print("\nEvolution over time:")
    for i in range(5):
        p3.evolve()
        playfulness = p3.get_trait(TraitType.PLAYFULNESS)
        print(f"  Step {i+1}: Playfulness={playfulness:.2f}")

    print("\nPersonality system test passed!")
