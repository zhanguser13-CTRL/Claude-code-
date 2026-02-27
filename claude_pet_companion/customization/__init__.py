"""
Claude Code Pet Companion - Customization System

This module provides:
- Pet appearance customization
- Accessory types and items
- Color schemes
- Unlockable items system
"""
from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import json


# ============================================================================
# Accessory Types
# ============================================================================

class AccessoryType(Enum):
    """Types of accessories for pets."""
    HAT = "hat"
    GLASSES = "glasses"
    BOW = "bow"
    SCARF = "scarf"
    WINGS = "wings"
    HALO = "halo"
    COLLAR = "collar"
    NECKLACE = "necklace"
    CROWN = "crown"
    HOLDING = "holding"           # Items pet holds


# ============================================================================
# Color Schemes
# ============================================================================

class ColorScheme(Enum):
    """Predefined color schemes for pets."""
    CLASSIC_BLUE = {
        "primary": "#4A90D9",
        "secondary": "#2E5C8A",
        "accent": "#87CEEB",
        "name": "Classic Blue"
    }
    PINK = {
        "primary": "#FF9EC5",
        "secondary": "#D46A9A",
        "accent": "#FFB3D9",
        "name": "Pink"
    }
    GREEN = {
        "primary": "#7CB97C",
        "secondary": "#4A7C4A",
        "accent": "#A8D4A8",
        "name": "Green"
    }
    ORANGE = {
        "primary": "#FFB347",
        "secondary": "#CC8435",
        "accent": "#FFCC70",
        "name": "Orange"
    }
    PURPLE = {
        "primary": "#9B72AA",
        "secondary": "#6B4A7A",
        "accent": "#B79CC4",
        "name": "Purple"
    }
    RAINBOW = {
        "primary": "#FF6B6B",
        "secondary": "#4ECDC4",
        "accent": "#FFE66D",
        "name": "Rainbow",
        "rainbow": True
    }
    GOLDEN = {
        "primary": "#FFD700",
        "secondary": "#DAA520",
        "accent": "#FFF8DC",
        "name": "Golden"
    }
    SHADOW = {
        "primary": "#2C2C2C",
        "secondary": "#1A1A1A",
        "accent": "#4A4A4A",
        "name": "Shadow"
    }
    CRYSTAL = {
        "primary": "#A8D8EA",
        "secondary": "#87CEEB",
        "accent": "#E0F7FA",
        "name": "Crystal"
    }
    LAVA = {
        "primary": "#FF4500",
        "secondary": "#8B0000",
        "accent": "#FFD700",
        "name": "Lava"
    }
    OCEAN = {
        "primary": "#006994",
        "secondary": "#004466",
        "accent": "#40E0D0",
        "name": "Ocean"
    }
    FOREST = {
        "primary": "#228B22",
        "secondary": "#006400",
        "accent": "#90EE90",
        "name": "Forest"
    }
    CHERRY_BLOSSOM = {
        "primary": "#FFB7C5",
        "secondary": "#FF69B4",
        "accent": "#FFF0F5",
        "name": "Cherry Blossom"
    }
    MIDNIGHT = {
        "primary": "#191970",
        "secondary": "#000080",
        "accent": "#4169E1",
        "name": "Midnight"
    }
    SUNSET = {
        "primary": "#FF7F50",
        "secondary": "#FF6347",
        "accent": "#FFD700",
        "name": "Sunset"
    }

    @classmethod
    def get_default(cls) -> 'ColorScheme':
        """Get the default color scheme."""
        return cls.CLASSIC_BLUE

    def get_colors(self) -> Dict[str, str]:
        """Get color dictionary for this scheme."""
        if isinstance(self.value, dict):
            return self.value
        return {}

    def get_primary(self) -> str:
        """Get primary color."""
        return self.get_colors().get("primary", "#4A90D9")

    def get_secondary(self) -> str:
        """Get secondary color."""
        return self.get_colors().get("secondary", "#2E5C8A")

    def get_accent(self) -> str:
        """Get accent color."""
        return self.get_colors().get("accent", "#87CEEB")

    def is_rainbow(self) -> bool:
        """Check if this is a rainbow scheme."""
        return self.get_colors().get("rainbow", False)


# ============================================================================
# Accessory Definition
# ============================================================================

@dataclass
class Accessory:
    """Represents a pet accessory."""
    id: str
    name: str
    description: str
    accessory_type: AccessoryType
    rarity: str = "common"           # common, rare, epic, legendary
    unlock_level: int = 1
    unlock_requirement: Optional[str] = None
    price: int = 0                   # In-game currency price
    icon: Optional[str] = None
    color_variants: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.accessory_type.value,
            "rarity": self.rarity,
            "unlock_level": self.unlock_level,
            "unlock_requirement": self.unlock_requirement,
            "price": self.price,
            "icon": self.icon,
            "color_variants": self.color_variants,
        }


# ============================================================================
# All Accessories
# ============================================================================

HATS = [
    Accessory(
        id="top_hat",
        name="Top Hat",
        description="A dapper top hat for distinguished pets.",
        accessory_type=AccessoryType.HAT,
        rarity="rare",
        unlock_level=5,
        price=100,
        icon="top_hat",
    ),
    Accessory(
        id="cowboy_hat",
        name="Cowboy Hat",
        description="Howdy partner!",
        accessory_type=AccessoryType.HAT,
        rarity="common",
        unlock_level=3,
        price=50,
        icon="cowboy_hat",
    ),
    Accessory(
        id="wizard_hat",
        name="Wizard Hat",
        description="Magical and mysterious.",
        accessory_type=AccessoryType.HAT,
        rarity="epic",
        unlock_level=15,
        price=500,
        icon="wizard_hat",
    ),
    Accessory(
        id="party_hat",
        name="Party Hat",
        description="It's time to celebrate!",
        accessory_type=AccessoryType.HAT,
        rarity="common",
        unlock_level=1,
        price=25,
        icon="party_hat",
    ),
    Accessory(
        id="crown",
        name="Crown",
        description="For royalty only.",
        accessory_type=AccessoryType.HAT,
        rarity="legendary",
        unlock_level=25,
        price=1000,
        icon="crown",
    ),
    Accessory(
        id="cat_ears",
        name="Cat Ears",
        description="Nya~",
        accessory_type=AccessoryType.HAT,
        rarity="common",
        unlock_level=1,
        price=30,
        icon="cat_ears",
    ),
    Accessory(
        id="beanie",
        name="Beanie",
        description="Cozy and warm.",
        accessory_type=AccessoryType.HAT,
        rarity="common",
        unlock_level=2,
        price=40,
        icon="beanie",
    ),
    Accessory(
        id="santa_hat",
        name="Santa Hat",
        description="Happy holidays!",
        accessory_type=AccessoryType.HAT,
        rarity="rare",
        unlock_level=10,
        price=200,
        icon="santa_hat",
    ),
]

GLASSES = [
    Accessory(
        id="sunglasses",
        name="Sunglasses",
        description="Cool shades.",
        accessory_type=AccessoryType.GLASSES,
        rarity="common",
        unlock_level=2,
        price=50,
        icon="sunglasses",
    ),
    Accessory(
        id="reading_glasses",
        name="Reading Glasses",
        description="For intellectual pets.",
        accessory_type=AccessoryType.GLASSES,
        rarity="common",
        unlock_level=1,
        price=30,
        icon="reading_glasses",
    ),
    Accessory(
        id="monocle",
        name="Monocle",
        description="Quite sophisticated.",
        accessory_type=AccessoryType.GLASSES,
        rarity="rare",
        unlock_level=8,
        price=150,
        icon="monocle",
    ),
    Accessory(
        id="3d_glasses",
        name="3D Glasses",
        description="Everything pops out!",
        accessory_type=AccessoryType.GLASSES,
        rarity="common",
        unlock_level=3,
        price=60,
        icon="3d_glasses",
    ),
]

BOWS = [
    Accessory(
        id="red_bow",
        name="Red Bow",
        description="A cute red bow tie.",
        accessory_type=AccessoryType.BOW,
        rarity="common",
        unlock_level=1,
        price=25,
        icon="red_bow",
    ),
    Accessory(
        id="bowtie",
        name="Bowtie",
        description="Formal and fancy.",
        accessory_type=AccessoryType.BOW,
        rarity="common",
        unlock_level=2,
        price=40,
        icon="bowtie",
    ),
    Accessory(
        id="golden_bow",
        name="Golden Bow",
        description="Fancy and valuable.",
        accessory_type=AccessoryType.BOW,
        rarity="rare",
        unlock_level=10,
        price=200,
        icon="golden_bow",
    ),
]

SCARVES = [
    Accessory(
        id="winter_scarf",
        name="Winter Scarf",
        description="Keep warm in style.",
        accessory_type=AccessoryType.SCARF,
        rarity="common",
        unlock_level=3,
        price=50,
        icon="winter_scarf",
    ),
    Accessory(
        id="striped_scarf",
        name="Striped Scarf",
        description="A classic look.",
        accessory_type=AccessoryType.SCARF,
        rarity="common",
        unlock_level=4,
        price=60,
        icon="striped_scarf",
    ),
]

WINGS = [
    Accessory(
        id="angel_wings",
        name="Angel Wings",
        description="Heavenly and divine.",
        accessory_type=AccessoryType.WINGS,
        rarity="legendary",
        unlock_level=30,
        price=1500,
        icon="angel_wings",
    ),
    Accessory(
        id="demon_wings",
        name="Demon Wings",
        description="From the depths below.",
        accessory_type=AccessoryType.WINGS,
        rarity="legendary",
        unlock_level=30,
        price=1500,
        icon="demon_wings",
    ),
    Accessory(
        id="fairy_wings",
        name="Fairy Wings",
        description="Delicate and magical.",
        accessory_type=AccessoryType.WINGS,
        rarity="epic",
        unlock_level=20,
        price=800,
        icon="fairy_wings",
    ),
    Accessory(
        id="dragon_wings",
        name="Dragon Wings",
        description="Powerful and fierce.",
        accessory_type=AccessoryType.WINGS,
        rarity="epic",
        unlock_level=20,
        price=800,
        icon="dragon_wings",
    ),
]

HALOS = [
    Accessory(
        id="golden_halo",
        name="Golden Halo",
        description="Divine protection.",
        accessory_type=AccessoryType.HALO,
        rarity="legendary",
        unlock_level=35,
        price=2000,
        icon="golden_halo",
    ),
    Accessory(
        id="silver_halo",
        name="Silver Halo",
        description="Celestial elegance.",
        accessory_type=AccessoryType.HALO,
        rarity="epic",
        unlock_level=25,
        price=1000,
        icon="silver_halo",
    ),
]

COLLARS = [
    Accessory(
        id="spiked_collar",
        name="Spiked Collar",
        description="Tough look.",
        accessory_type=AccessoryType.COLLAR,
        rarity="common",
        unlock_level=3,
        price=50,
        icon="spiked_collar",
    ),
    Accessory(
        id="diamond_collar",
        name="Diamond Collar",
        description="Luxurious and expensive.",
        accessory_type=AccessoryType.COLLAR,
        rarity="legendary",
        unlock_level=40,
        price=3000,
        icon="diamond_collar",
    ),
    Accessory(
        id="bell_collar",
        name="Bell Collar",
        description="Jingle jingle!",
        accessory_type=AccessoryType.COLLAR,
        rarity="common",
        unlock_level=1,
        price=30,
        icon="bell_collar",
    ),
]

HOLDING_ITEMS = [
    Accessory(
        id="laptop",
        name="Laptop",
        description="Ready to code!",
        accessory_type=AccessoryType.HOLDING,
        rarity="common",
        unlock_level=1,
        price=50,
        icon="laptop",
    ),
    Accessory(
        id="coffee",
        name="Coffee Cup",
        description="Fuel for coding.",
        accessory_type=AccessoryType.HOLDING,
        rarity="common",
        unlock_level=1,
        price=20,
        icon="coffee",
    ),
    Accessory(
        id="wand",
        name="Magic Wand",
        description="Abracadabra!",
        accessory_type=AccessoryType.HOLDING,
        rarity="rare",
        unlock_level=12,
        price=300,
        icon="wand",
    ),
    Accessory(
        id="sword",
        name="Sword",
        description="For brave adventures.",
        accessory_type=AccessoryType.HOLDING,
        rarity="epic",
        unlock_level=18,
        price=600,
        icon="sword",
    ),
    Accessory(
        id="book",
        name="Book",
        description="Knowledge is power.",
        accessory_type=AccessoryType.HOLDING,
        rarity="common",
        unlock_level=2,
        price=40,
        icon="book",
    ),
    Accessory(
        id="game_controller",
        name="Game Controller",
        description="Time to play!",
        accessory_type=AccessoryType.HOLDING,
        rarity="common",
        unlock_level=1,
        price=50,
        icon="game_controller",
    ),
    Accessory(
        id="ice_cream",
        name="Ice Cream",
        description="A tasty treat.",
        accessory_type=AccessoryType.HOLDING,
        rarity="common",
        unlock_level=1,
        price=20,
        icon="ice_cream",
    ),
]

ALL_ACCESSORIES: Dict[str, Accessory] = {}

def _register_accessories():
    """Register all accessories into the main dictionary."""
    ALL_ACCESSORIES.clear()
    for accessory_list in [HATS, GLASSES, BOWS, SCARVES, WINGS, HALOS, COLLARS, HOLDING_ITEMS]:
        for accessory in accessory_list:
            ALL_ACCESSORIES[accessory.id] = accessory

_register_accessories()


# ============================================================================
# Pet Appearance Data Class
# ============================================================================

@dataclass
class PetAppearance:
    """Represents the visual appearance of a pet."""
    color_scheme: ColorScheme = ColorScheme.CLASSIC_BLUE
    equipped_accessories: Dict[AccessoryType, Optional[str]] = field(default_factory=dict)
    custom_colors: Dict[str, str] = field(default_factory=dict)
    size_modifier: float = 1.0
    effects: List[str] = field(default_factory=list)

    def __post_init__(self):
        # Initialize empty slots for all accessory types
        for acc_type in AccessoryType:
            if acc_type not in self.equipped_accessories:
                self.equipped_accessories[acc_type] = None

    def equip_accessory(self, accessory_id: str) -> bool:
        """
        Equip an accessory.

        Args:
            accessory_id: ID of accessory to equip

        Returns:
            True if equipped successfully
        """
        accessory = ALL_ACCESSORIES.get(accessory_id)
        if accessory is None:
            return False

        self.equipped_accessories[accessory.accessory_type] = accessory_id
        return True

    def unequip_accessory(self, accessory_type: AccessoryType) -> None:
        """Unequip accessory of given type."""
        self.equipped_accessories[accessory_type] = None

    def get_equipped_accessory(self, accessory_type: AccessoryType) -> Optional[Accessory]:
        """Get equipped accessory of given type."""
        accessory_id = self.equipped_accessories.get(accessory_type)
        if accessory_id:
            return ALL_ACCESSORIES.get(accessory_id)
        return None

    def set_color_scheme(self, scheme: ColorScheme) -> None:
        """Set the color scheme."""
        self.color_scheme = scheme

    def set_custom_color(self, color_type: str, color: str) -> None:
        """Set a custom color override."""
        self.custom_colors[color_type] = color

    def get_color(self, color_type: str) -> str:
        """Get a color value, preferring custom overrides."""
        if color_type in self.custom_colors:
            return self.custom_colors[color_type]

        if color_type == "primary":
            return self.color_scheme.get_primary()
        elif color_type == "secondary":
            return self.color_scheme.get_secondary()
        elif color_type == "accent":
            return self.color_scheme.get_accent()

        return self.color_scheme.get_primary()

    def add_effect(self, effect: str) -> None:
        """Add a visual effect."""
        if effect not in self.effects:
            self.effects.append(effect)

    def remove_effect(self, effect: str) -> None:
        """Remove a visual effect."""
        if effect in self.effects:
            self.effects.remove(effect)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "color_scheme": self.color_scheme.name,
            "equipped_accessories": {
                acc_type.value: acc_id
                for acc_type, acc_id in self.equipped_accessories.items()
                if acc_id is not None
            },
            "custom_colors": self.custom_colors,
            "size_modifier": self.size_modifier,
            "effects": self.effects,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'PetAppearance':
        """Create from dictionary."""
        appearance = cls()

        # Load color scheme
        scheme_name = data.get("color_scheme", "CLASSIC_BLUE")
        try:
            appearance.color_scheme = ColorScheme[scheme_name]
        except KeyError:
            appearance.color_scheme = ColorScheme.CLASSIC_BLUE

        # Load accessories
        equipped = data.get("equipped_accessories", {})
        for acc_type_str, acc_id in equipped.items():
            try:
                acc_type = AccessoryType(acc_type_str)
                appearance.equipped_accessories[acc_type] = acc_id
            except (ValueError, KeyError):
                pass

        # Load custom colors
        appearance.custom_colors = data.get("custom_colors", {})

        # Load size modifier
        appearance.size_modifier = data.get("size_modifier", 1.0)

        # Load effects
        appearance.effects = data.get("effects", [])

        return appearance


# ============================================================================
# Customization Manager
# ============================================================================

class CustomizationManager:
    """
    Manages pet customization and unlockable items.
    """

    def __init__(self):
        self.appearance = PetAppearance()
        self.unlocked_accessories: Set[str] = set()
        self.currency: int = 0

    def get_all_accessories(self) -> List[Accessory]:
        """Get all available accessories."""
        return list(ALL_ACCESSORIES.values())

    def get_accessory(self, accessory_id: str) -> Optional[Accessory]:
        """Get an accessory by ID."""
        return ALL_ACCESSORIES.get(accessory_id)

    def get_accessories_by_type(self, acc_type: AccessoryType) -> List[Accessory]:
        """Get all accessories of a specific type."""
        return [
            acc for acc in ALL_ACCESSORIES.values()
            if acc.accessory_type == acc_type
        ]

    def unlock_accessory(self, accessory_id: str) -> bool:
        """
        Unlock an accessory.

        Args:
            accessory_id: ID of accessory to unlock

        Returns:
            True if unlocked successfully
        """
        accessory = self.get_accessory(accessory_id)
        if accessory is None:
            return False

        self.unlocked_accessories.add(accessory_id)
        return True

    def is_accessory_unlocked(self, accessory_id: str) -> bool:
        """Check if an accessory is unlocked."""
        return accessory_id in self.unlocked_accessories

    def can_equip(self, accessory_id: str, level: int = 1) -> bool:
        """
        Check if an accessory can be equipped.

        Args:
            accessory_id: ID of accessory
            level: Current pet level

        Returns:
            True if accessory can be equipped
        """
        if not self.is_accessory_unlocked(accessory_id):
            return False

        accessory = self.get_accessory(accessory_id)
        if accessory is None:
            return False

        return level >= accessory.unlock_level

    def equip(self, accessory_id: str, level: int = 1) -> bool:
        """
        Equip an accessory.

        Args:
            accessory_id: ID of accessory to equip
            level: Current pet level

        Returns:
            True if equipped successfully
        """
        if not self.can_equip(accessory_id, level):
            return False

        return self.appearance.equip_accessory(accessory_id)

    def unequip(self, accessory_type: AccessoryType) -> None:
        """Unequip an accessory type."""
        self.appearance.unequip_accessory(accessory_type)

    def set_color_scheme(self, scheme: ColorScheme) -> bool:
        """
        Set the pet's color scheme.

        Args:
            scheme: Color scheme to apply

        Returns:
            True if scheme is available
        """
        # Check if scheme is unlocked (all schemes available for now)
        self.appearance.set_color_scheme(scheme)
        return True

    def get_appearance(self) -> PetAppearance:
        """Get the current pet appearance."""
        return self.appearance

    def add_currency(self, amount: int) -> None:
        """Add currency."""
        self.currency += amount

    def spend_currency(self, amount: int) -> bool:
        """
        Spend currency if available.

        Args:
            amount: Amount to spend

        Returns:
            True if successful
        """
        if self.currency >= amount:
            self.currency -= amount
            return True
        return False

    def get_currency(self) -> int:
        """Get current currency amount."""
        return self.currency

    def save_state(self) -> Dict:
        """Get serializable state."""
        return {
            "appearance": self.appearance.to_dict(),
            "unlocked_accessories": list(self.unlocked_accessories),
            "currency": self.currency,
        }

    def load_state(self, state: Dict) -> None:
        """Load state from dictionary."""
        # Load appearance
        appearance_data = state.get("appearance", {})
        self.appearance = PetAppearance.from_dict(appearance_data)

        # Load unlocked accessories
        unlocked = state.get("unlocked_accessories", [])
        self.unlocked_accessories = set(unlocked)

        # Load currency
        self.currency = state.get("currency", 0)


__all__ = [
    # Enums
    "AccessoryType",
    "ColorScheme",
    # Classes
    "Accessory",
    "PetAppearance",
    "CustomizationManager",
    # Accessory lists
    "HATS",
    "GLASSES",
    "BOWS",
    "SCARVES",
    "WINGS",
    "HALOS",
    "COLLARS",
    "HOLDING_ITEMS",
    "ALL_ACCESSORIES",
    # Functions
    "_register_accessories",
]
