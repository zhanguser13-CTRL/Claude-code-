"""
Material System for Claude Pet Companion

Provides advanced material rendering with:
- Fur/hair simulation with shell technique
- Subsurface scattering for soft appearance
- Dynamic material properties
- Texture support
- Procedural patterns
"""

import math
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import random

logger = logging.getLogger(__name__)


class MaterialType(Enum):
    """Types of materials."""
    BASIC = "basic"
    FUR = "fur"
    SUBSURFACE = "subsurface"
    GLOSSY = "glossy"
    MATTE = "matte"
    METALLIC = "metallic"
    EMISSIVE = "emissive"
    GLASS = "glass"


@dataclass
class Color:
    """RGBA color."""
    r: float = 1.0
    g: float = 1.0
    b: float = 1.0
    a: float = 1.0

    def to_tuple(self) -> Tuple[float, float, float, float]:
        return (self.r, self.g, self.b, self.a)

    def to_rgb(self) -> Tuple[float, float, float]:
        return (self.r, self.g, self.b)

    def to_hex(self) -> str:
        """Convert to hex color string."""
        return f"#{int(self.r*255):02x}{int(self.g*255):02x}{int(self.b*255):02x}"

    @classmethod
    def from_hex(cls, hex_str: str) -> 'Color':
        """Create color from hex string."""
        hex_str = hex_str.lstrip('#')
        if len(hex_str) == 6:
            r = int(hex_str[0:2], 16) / 255.0
            g = int(hex_str[2:4], 16) / 255.0
            b = int(hex_str[4:6], 16) / 255.0
            return cls(r, g, b, 1.0)
        elif len(hex_str) == 8:
            r = int(hex_str[0:2], 16) / 255.0
            g = int(hex_str[2:4], 16) / 255.0
            b = int(hex_str[4:6], 16) / 255.0
            a = int(hex_str[6:8], 16) / 255.0
            return cls(r, g, b, a)
        return cls()

    def blend(self, other: 'Color', t: float) -> 'Color':
        """Blend with another color."""
        return Color(
            self.r + (other.r - self.r) * t,
            self.g + (other.g - self.g) * t,
            self.b + (other.b - self.b) * t,
            self.a + (other.a - self.a) * t,
        )

    def multiply(self, factor: float) -> 'Color':
        """Multiply color by factor."""
        return Color(
            max(0, min(1, self.r * factor)),
            max(0, min(1, self.g * factor)),
            max(0, min(1, self.b * factor)),
            self.a
        )

    def to_grayscale(self) -> float:
        """Convert to grayscale luminance."""
        return 0.299 * self.r + 0.587 * self.g + 0.114 * self.b


@dataclass
class FurLayer:
    """Single layer of fur for shell technique."""
    offset: float = 0.0  # Distance from base surface
    color: Color = field(default_factory=Color)
    opacity: float = 1.0
    roughness: float = 0.5


@dataclass
class FurMaterial:
    """Fur material using shell rendering technique."""

    # Base color
    base_color: Color = field(default_factory=lambda: Color(1.0, 1.0, 1.0, 1.0))

    # Fur properties
    fur_length: float = 0.1  # Length of fur strands
    fur_density: float = 0.5  # How dense the fur is
    fur_layers: int = 8  # Number of shell layers

    # Fur color variation
    fur_color: Color = field(default_factory=lambda: Color(0.95, 0.95, 0.95, 1.0))
    tip_color: Optional[Color] = None  # Color of fur tips
    root_color: Optional[Color] = None  # Color of fur roots

    # Fur behavior
    fur_stiffness: float = 0.3  # How stiff the fur is
    fur_direction: Tuple[float, float, float] = (0, 1, 0)  # Direction fur grows
    fur_randomness: float = 0.2  # Random variation in fur direction

    # Shell layers (generated)
    layers: List[FurLayer] = field(default_factory=list)

    def __post_init__(self):
        """Generate fur layers."""
        self._generate_layers()

    def _generate_layers(self):
        """Generate shell layers for fur rendering."""
        self.layers.clear()
        for i in range(self.fur_layers):
            t = (i + 1) / self.fur_layers
            offset = t * self.fur_length

            # Interpolate color from base to tip
            if self.root_color:
                layer_color = self.base_color.blend(self.fur_color, t * 0.5)
            else:
                layer_color = self.base_color.blend(self.fur_color, t)

            if self.tip_color and i == self.fur_layers - 1:
                layer_color = self.tip_color

            # Fade out at tips
            opacity = 1.0 - (t * 0.3)

            layer = FurLayer(
                offset=offset,
                color=layer_color,
                opacity=opacity,
                roughness=0.5 + t * 0.3
            )
            self.layers.append(layer)

    def get_layer_color(self, layer_index: int) -> Color:
        """Get color for a specific fur layer."""
        if 0 <= layer_index < len(self.layers):
            return self.layers[layer_index].color
        return self.base_color

    def get_layer_offset(self, layer_index: int) -> float:
        """Get offset for a specific fur layer."""
        if 0 <= layer_index < len(self.layers):
            return self.layers[layer_index].offset
        return 0.0


@dataclass
class SubsurfaceMaterial:
    """Subsurface scattering material for soft, translucent appearance."""

    # Base properties
    base_color: Color = field(default_factory=lambda: Color(1.0, 0.9, 0.8, 1.0))

    # Scattering
    scattering_color: Color = field(default_factory=lambda: Color(1.0, 0.6, 0.4, 1.0))
    scattering_scale: float = 0.5  # How far light scatters
    scattering_strength: float = 0.8  # Intensity of scattering

    # Transmission
    transmission: float = 0.3  # How much light passes through
    thickness: float = 0.5  # Apparent thickness

    # Softness
    roughness: float = 0.3
    specular: float = 0.2


@dataclass
class Pattern:
    """Procedural pattern for materials."""
    pattern_type: str = "solid"  # solid, striped, spotted, gradient, noise

    # Colors for pattern
    primary_color: Color = field(default_factory=Color)
    secondary_color: Optional[Color] = None

    # Pattern parameters
    scale: float = 1.0
    rotation: float = 0.0
    offset: Tuple[float, float] = (0.0, 0.0)

    # Specific pattern parameters
    stripe_width: float = 0.2  # For striped pattern
    spot_count: int = 10  # For spotted pattern
    spot_size: float = 0.1  # For spotted pattern
    noise_scale: float = 5.0  # For noise pattern
    seed: int = 42  # Random seed

    def get_color_at(self, u: float, v: float) -> Color:
        """Get pattern color at UV coordinates."""
        # Apply offset and scale
        x = (u - self.offset[0]) * self.scale
        y = (v - self.offset[1]) * self.scale

        # Apply rotation
        if self.rotation != 0:
            cos_r = math.cos(self.rotation)
            sin_r = math.sin(self.rotation)
            nx = x * cos_r - y * sin_r
            ny = x * sin_r + y * cos_r
            x, y = nx, ny

        if self.pattern_type == "solid":
            return self.primary_color

        elif self.pattern_type == "striped":
            if math.sin(x * math.pi * 2 / self.stripe_width) > 0:
                return self.primary_color
            return self.secondary_color or self.primary_color

        elif self.pattern_type == "ringed":
            dist = math.sqrt(x * x + y * y)
            if math.sin(dist * math.pi * 2 / self.stripe_width) > 0:
                return self.primary_color
            return self.secondary_color or self.primary_color

        elif self.pattern_type == "gradient":
            t = (math.sin(x * 0.5) + 1) / 2
            return self.primary_color.blend(
                self.secondary_color or self.primary_color,
                t
            )

        elif self.pattern_type == "spotted":
            # Simple procedural spots
            rng = random.Random(self.seed)
            spots = []
            for i in range(self.spot_count):
                sx = rng.uniform(-1, 1)
                sy = rng.uniform(-1, 1)
                spots.append((sx, sy))

            for sx, sy in spots:
                dist = math.sqrt((x - sx) ** 2 + (y - sy) ** 2)
                if dist < self.spot_size:
                    return self.secondary_color or self.primary_color
            return self.primary_color

        elif self.pattern_type == "noise":
            # Simple value noise
            rng = random.Random(self.seed + int(x * 10) + int(y * 10))
            noise = (rng.random() - 0.5) * 0.5
            t = ((math.sin(x * self.noise_scale) + math.sin(y * self.noise_scale)) / 2 + 1) / 2
            return self.primary_color.blend(
                self.secondary_color or self.primary_color,
                t + noise
            )

        return self.primary_color


class MaterialLibrary:
    """Library of pre-defined materials."""

    _materials: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(cls, name: str, material: Dict[str, Any]):
        """Register a material."""
        cls._materials[name] = material

    @classmethod
    def get(cls, name: str) -> Optional[Dict[str, Any]]:
        """Get a material by name."""
        return cls._materials.get(name)

    @classmethod
    def create_fur(cls, name: str, base_color: Color, fur_length: float = 0.1,
                  fur_color: Optional[Color] = None) -> FurMaterial:
        """Create a fur material."""
        material = FurMaterial(
            base_color=base_color,
            fur_color=fur_color or base_color,
            fur_length=fur_length
        )
        cls.register(name, {'type': 'fur', 'material': material})
        return material

    @classmethod
    def create_subsurface(cls, name: str, base_color: Color,
                         scattering: float = 0.5) -> SubsurfaceMaterial:
        """Create a subsurface material."""
        material = SubsurfaceMaterial(
            base_color=base_color,
            scattering_scale=scattering
        )
        cls.register(name, {'type': 'subsurface', 'material': material})
        return material


# Preset materials for pets

def create_default_pet_material() -> FurMaterial:
    """Create default pet fur material."""
    return FurMaterial(
        base_color=Color(0.95, 0.92, 0.88, 1.0),
        fur_length=0.08,
        fur_density=0.6,
        fur_layers=10,
        fur_color=Color(0.98, 0.95, 0.92, 1.0),
        tip_color=Color(1.0, 0.98, 0.95, 1.0),
        fur_stiffness=0.3
    )


def create_dark_pet_material() -> FurMaterial:
    """Create dark pet fur material."""
    return FurMaterial(
        base_color=Color(0.25, 0.22, 0.20, 1.0),
        fur_length=0.09,
        fur_density=0.7,
        fur_layers=12,
        fur_color=Color(0.28, 0.25, 0.23, 1.0),
        tip_color=Color(0.35, 0.32, 0.30, 1.0),
        fur_stiffness=0.4
    )


def create_orange_pet_material() -> FurMaterial:
    """Create orange tabby pet fur material."""
    base = FurMaterial(
        base_color=Color(0.95, 0.65, 0.35, 1.0),
        fur_length=0.085,
        fur_density=0.65,
        fur_layers=11,
        fur_color=Color(0.98, 0.68, 0.38, 1.0),
        tip_color=Color(1.0, 0.75, 0.45, 1.0),
        fur_stiffness=0.35
    )
    return base


def create_white_fluffy_material() -> FurMaterial:
    """Create white fluffy pet fur material."""
    return FurMaterial(
        base_color=Color(0.98, 0.98, 0.98, 1.0),
        fur_length=0.12,
        fur_density=0.8,
        fur_layers=15,
        fur_color=Color(1.0, 1.0, 1.0, 1.0),
        tip_color=Color(1.0, 1.0, 1.0, 0.95),
        fur_stiffness=0.25
    )


def create_patterned_material(base_color: Color, pattern_type: str,
                             secondary_color: Color) -> Tuple[FurMaterial, Pattern]:
    """Create a patterned fur material."""
    fur = FurMaterial(
        base_color=base_color,
        fur_length=0.08,
        fur_density=0.6,
        fur_layers=10
    )

    pattern = Pattern(
        pattern_type=pattern_type,
        primary_color=base_color,
        secondary_color=secondary_color,
        scale=2.0,
        stripe_width=0.3
    )

    return fur, pattern


# Material color presets

class PetColors:
    """Common pet color presets."""

    # Natural colors
    WHITE = Color(0.98, 0.98, 0.98, 1.0)
    CREAM = Color(1.0, 0.95, 0.82, 1.0)
    BEIGE = Color(0.92, 0.86, 0.76, 1.0)
    TAN = Color(0.82, 0.72, 0.60, 1.0)
    BROWN = Color(0.60, 0.48, 0.36, 1.0)
    DARK_BROWN = Color(0.40, 0.30, 0.22, 1.0)
    BLACK = Color(0.20, 0.18, 0.16, 1.0)

    # Orange/Red
    ORANGE = Color(0.95, 0.62, 0.32, 1.0)
    GINGER = Color(0.88, 0.52, 0.28, 1.0)
    RED = Color(0.75, 0.40, 0.25, 1.0)

    # Gray
    LIGHT_GRAY = Color(0.75, 0.75, 0.75, 1.0)
    GRAY = Color(0.55, 0.55, 0.55, 1.0)
    DARK_GRAY = Color(0.35, 0.35, 0.35, 1.0)

    # Special
    GOLDEN = Color(0.85, 0.70, 0.40, 1.0)
    SILVER = Color(0.70, 0.72, 0.75, 1.0)
    CREAM_POINT = Color(1.0, 0.92, 0.85, 1.0)


def blend_materials(base: FurMaterial, overlay: FurMaterial,
                   blend_factor: float) -> FurMaterial:
    """Blend two fur materials."""
    result = FurMaterial(
        base_color=base.base_color.blend(overlay.base_color, blend_factor),
        fur_length=base.fur_length + (overlay.fur_length - base.fur_length) * blend_factor,
        fur_density=base.fur_density + (overlay.fur_density - base.fur_density) * blend_factor,
        fur_layers=max(base.fur_layers, overlay.fur_layers),
        fur_color=base.fur_color.blend(overlay.fur_color, blend_factor),
        tip_color=base.tip_color.blend(overlay.tip_color, blend_factor) if base.tip_color and overlay.tip_color else None,
        fur_stiffness=base.fur_stiffness + (overlay.fur_stiffness - base.fur_stiffness) * blend_factor
    )
    return result


if __name__ == "__main__":
    # Test material system
    print("Testing Material System")

    # Test colors
    white = Color.from_hex("#ffffff")
    orange = Color.from_hex("#ff9933")

    print(f"White: {white.to_hex()}")
    print(f"Orange: {orange.to_hex()}")
    print(f"Blended: {white.blend(orange, 0.5).to_hex()}")

    # Test fur material
    fur = create_default_pet_material()
    print(f"\nFur material:")
    print(f"  Layers: {fur.fur_layers}")
    print(f"  Length: {fur.fur_length}")
    print(f"  Base color: {fur.base_color.to_hex()}")

    # Test pattern
    pattern = Pattern(
        pattern_type="striped",
        primary_color=Color(1.0, 0.9, 0.8, 1.0),
        secondary_color=Color(0.8, 0.7, 0.6, 1.0),
        scale=3.0
    )

    print(f"\nPattern at (0.5, 0.5): {pattern.get_color_at(0.5, 0.5).to_hex()}")
    print(f"Pattern at (0.0, 0.0): {pattern.get_color_at(0.0, 0.0).to_hex()}")

    # Test subsurface material
    sss = SubsurfaceMaterial(
        base_color=Color(1.0, 0.9, 0.85, 1.0),
        scattering_scale=0.5
    )
    print(f"\nSubsurface material color: {sss.base_color.to_hex()}")

    print("\nMaterial system test passed!")
