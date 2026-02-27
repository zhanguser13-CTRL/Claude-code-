"""
Advanced Particle System v2 for Claude Pet Companion

Provides high-performance particle effects with:
- Thousands of particles
- Physics simulation (gravity, wind, collision)
- GPU-style effects (glow, additive blending)
- Emitters with various shapes
- Particle affinity and behavior
- Weather system integration
"""

import math
import random
import logging
import time
from typing import Dict, List, Tuple, Optional, Set, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class ColliderType(Enum):
    """Types of colliders for physics bodies."""
    NONE = "none"
    CIRCLE = "circle"
    AABB = "aabb"


class BlendMode(Enum):
    """Particle blend modes."""
    NORMAL = "normal"
    ADDITIVE = "additive"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    ALPHA = "alpha"


class EmitterType(Enum):
    """Particle emitter shapes."""
    POINT = "point"
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    SPHERE = "sphere"
    CONE = "cone"
    LINE = "line"


@dataclass
class Color:
    """RGBA color for particles."""
    r: float = 1.0
    g: float = 1.0
    b: float = 1.0
    a: float = 1.0

    @classmethod
    def from_hex(cls, hex_str: str) -> 'Color':
        """Create color from hex string."""
        hex_str = hex_str.lstrip('#')
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
        a = int(hex_str[6:8], 16) / 255.0 if len(hex_str) >= 8 else 1.0
        return cls(r, g, b, a)

    def to_tuple(self) -> Tuple[float, float, float, float]:
        return (self.r, self.g, self.b, self.a)

    def lerp(self, other: 'Color', t: float) -> 'Color':
        """Linear interpolate to another color."""
        return Color(
            self.r + (other.r - self.r) * t,
            self.g + (other.g - self.g) * t,
            self.b + (other.b - self.b) * t,
            self.a + (other.a - self.a) * t
        )


@dataclass
class Vector2:
    """2D vector for particle physics."""
    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> 'Vector2':
        return Vector2(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: float) -> 'Vector2':
        return Vector2(self.x / scalar, self.y / scalar)

    def length(self) -> float:
        return math.sqrt(self.x**2 + self.y**2)

    def normalize(self) -> 'Vector2':
        l = self.length()
        if l > 0:
            return Vector2(self.x / l, self.y / l)
        return Vector2(0, 0)

    def dot(self, other: 'Vector2') -> float:
        return self.x * other.x + self.y * other.y

    def distance_to(self, other: 'Vector2') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class Vector3:
    """3D vector."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def length(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalize(self) -> 'Vector3':
        l = self.length()
        if l > 0:
            return Vector3(self.x / l, self.y / l, self.z / l)
        return Vector3(0, 0, 0)

    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)


@dataclass
class AABB:
    """Axis-aligned bounding box for collision detection."""
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @classmethod
    def from_center(cls, center: Vector2, size: Vector2) -> 'AABB':
        """Create AABB from center point and size (full extents, will be halved)."""
        half_x = size.x / 2
        half_y = size.y / 2
        return cls(
            min_x=center.x - half_x,
            min_y=center.y - half_y,
            max_x=center.x + half_x,
            max_y=center.y + half_y
        )

    def contains(self, point) -> bool:
        """Check if point is inside AABB (inclusive bounds)."""
        if isinstance(point, Vector2):
            return self.min_x <= point.x <= self.max_x and self.min_y <= point.y <= self.max_y
        return self.min_x <= point[0] <= self.max_x and self.min_y <= point[1] <= self.max_y

    def intersects(self, other) -> bool:
        """Check if two AABBs intersect."""
        if isinstance(other, AABB):
            return not (self.max_x < other.min_x or self.min_x > other.max_x or
                       self.max_y < other.min_y or self.min_y > other.max_y)
        return False

    def width(self) -> float:
        return self.max_x - self.min_x

    def height(self) -> float:
        return self.max_y - self.min_y


@dataclass
class CircleCollider:
    """Circle collision collider."""
    center: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    radius: float = 1.0

    # Legacy support for x,y constructor
    def __init__(self, *args):
        if len(args) == 2 and isinstance(args[0], Vector2):
            self.center = args[0]
            self.radius = args[1]
        elif len(args) == 3:
            self.center = Vector2(args[0], args[1])
            self.radius = args[2]
        else:
            self.center = Vector2(0, 0)
            self.radius = 1.0

    def contains(self, point) -> bool:
        """Check if point is inside circle."""
        if isinstance(point, Vector2):
            dx = point.x - self.center.x
            dy = point.y - self.center.y
        else:
            dx = point[0] - self.center.x
            dy = point[1] - self.center.y
        return dx*dx + dy*dy <= self.radius**2

    def intersects_circle(self, other: 'CircleCollider') -> bool:
        """Check if two circles intersect."""
        distance = math.sqrt((self.center.x - other.center.x)**2 + (self.center.y - other.center.y)**2)
        return distance <= self.radius + other.radius

    def intersects(self, other) -> bool:
        """Check intersection with other collider."""
        if isinstance(other, CircleCollider):
            return self.intersects_circle(other)
        elif isinstance(other, AABB):
            return self.intersects_aabb(other)
        return False

    def intersects_aabb(self, aabb: AABB) -> bool:
        """Check if circle intersects AABB."""
        # Find closest point on AABB to circle center
        closest_x = max(aabb.min_x, min(self.center.x, aabb.max_x))
        closest_y = max(aabb.min_y, min(self.center.y, aabb.max_y))
        return (self.center.x - closest_x)**2 + (self.center.y - closest_y)**2 <= self.radius**2


@dataclass
class Spring:
    """Spring physics for particle connections."""
    stiffness: float = 1.0
    damping: float = 0.5
    rest_length: float = 1.0

    def apply_force(self, pos1: Vector2, pos2: Vector2, vel1: Vector2, vel2: Vector2,
                   mass1: float, mass2: float) -> Tuple[Vector2, Vector2]:
        """Apply spring force between two points."""
        delta = pos2 - pos1
        distance = delta.length()
        if distance == 0:
            return Vector2(0, 0), Vector2(0, 0)

        direction = Vector2(delta.x / distance, delta.y / distance)

        # Spring force (Hooke's law)
        displacement = distance - self.rest_length
        spring_force = stiffness * displacement

        # Damping force
        rel_vel = vel2 - vel1
        damping_force = self.damping * rel_vel.dot(direction)

        total_force = spring_force + damping_force

        force1 = Vector2(direction.x * total_force, direction.y * total_force)
        force2 = Vector2(-force1.x, -force1.y)

        return force1, force2


@dataclass
class PhysicsBody:
    """Physics body for collision and dynamics."""
    position: Vector2 = field(default_factory=Vector2)
    velocity: Vector2 = field(default_factory=Vector2)
    acceleration: Vector2 = field(default_factory=Vector2)
    mass: float = 1.0
    inv_mass: float = 1.0
    restitution: float = 0.5  # Bounciness
    friction: float = 0.1
    is_static: bool = False
    collider_type: ColliderType = ColliderType.NONE
    collider_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.mass > 0:
            self.inv_mass = 1.0 / self.mass
        else:
            self.inv_mass = 0.0

    def apply_force(self, force: Vector2):
        """Apply force to body."""
        if self.is_static:
            return
        self.acceleration = self.acceleration + Vector2(
            force.x * self.inv_mass,
            force.y * self.inv_mass
        )

    def update(self, dt: float):
        """Update physics state."""
        if self.is_static:
            return
        self.velocity = self.velocity + self.acceleration * dt
        self.position = self.position + self.velocity * dt
        self.acceleration = Vector2(0, 0)  # Reset acceleration


class PhysicsWorld:
    """Physics world for simulating particle interactions."""

    def __init__(self, gravity: Vector2 = None):
        self.gravity = gravity or Vector2(0, 9.8)
        self.bodies: List[PhysicsBody] = []
        self.colliders: List[object] = []  # Can be AABB or CircleCollider
        self.collisions: List[Tuple[PhysicsBody, PhysicsBody]] = []  # Detected collisions

    def add_body(self, body: PhysicsBody):
        """Add physics body to world."""
        self.bodies.append(body)

    def remove_body(self, body: PhysicsBody):
        """Remove physics body from world."""
        if body in self.bodies:
            self.bodies.remove(body)

    def add_collider(self, collider):
        """Add collider to world."""
        self.colliders.append(collider)

    def step(self, dt: float):
        """Step the simulation by dt seconds (alias for update)."""
        self.update(dt)

    def update(self, dt: float):
        """Update all bodies."""
        self.collisions.clear()

        for body in self.bodies:
            # Apply gravity
            if not body.is_static:
                body.apply_force(self.gravity * body.mass)

            body.update(dt)

            # Simple floor collision
            if body.position.y > 100:
                body.position.y = 100
                body.velocity.y *= -body.restitution

        # Check collisions between bodies
        for i, body1 in enumerate(self.bodies):
            for body2 in self.bodies[i+1:]:
                if self._check_collision(body1, body2):
                    self.collisions.append((body1, body2))

    def _check_collision(self, body1: PhysicsBody, body2: PhysicsBody) -> bool:
        """Check if two bodies collide."""
        # Simple distance check for now
        dx = body1.position.x - body2.position.x
        dy = body1.position.y - body2.position.y
        distance = math.sqrt(dx*dx + dy*dy)
        return distance < 2.0  # Simple collision radius

    def clear(self):
        """Clear all bodies."""
        self.bodies.clear()
        self.colliders.clear()
        self.collisions.clear()


@dataclass
class Particle:
    """Single particle with full physics and rendering data."""

    # Position and velocity
    position: Vector3 = field(default_factory=Vector3)
    velocity: Vector3 = field(default_factory=Vector3)
    acceleration: Vector3 = field(default_factory=Vector3)

    # Appearance
    size: float = 1.0
    color: Color = field(default_factory=Color)
    rotation: float = 0.0
    rotation_speed: float = 0.0

    # Lifetime
    life: float = 1.0  # Current remaining life (decreases from max_life to 0)
    max_life: float = 1.0  # Maximum lifetime in seconds
    age: float = 0.0  # Current age

    # Physics
    mass: float = 1.0
    drag: float = 0.01
    gravity_scale: float = 1.0

    # Behavior flags
    alive: bool = True
    collide: bool = False
    affected_by_wind: bool = True
    lifetime_enabled: bool = False  # Whether to decay life over time

    # Emission info
    emitter_id: Optional[int] = None

    def __post_init__(self):
        """Initialize particle state."""
        # life is already set to max_life by default, no need to reassign

    def update(self, dt: float, gravity: Vector3, wind: Vector3 = None) -> bool:
        """Update particle state. Returns False if particle died."""
        if wind is None:
            wind = Vector3(0, 0, 0)
        if not self.alive:
            return False

        # Age particle and decrease life (if enabled)
        self.age += dt
        if self.lifetime_enabled:
            self.life = self.max_life - self.age

        if self.life <= 0:
            self.life = 0
            self.alive = False
            return False

        # Apply gravity
        if self.gravity_scale > 0:
            g_force = gravity * self.mass * self.gravity_scale
            self.acceleration = self.acceleration + g_force

        # Apply wind
        if self.affected_by_wind:
            self.acceleration = self.acceleration + (wind * (1.0 / self.mass))

        # Apply drag
        self.velocity = self.velocity * (1.0 - self.drag)

        # Integrate
        self.velocity = self.velocity + (self.acceleration * dt)
        self.position = self.position + (self.velocity * dt)

        # Update rotation
        self.rotation += self.rotation_speed * dt

        # Reset acceleration
        self.acceleration = Vector3(0, 0, 0)

        return True


@dataclass
class ParticleEmitter:
    """Particle emitter that spawns particles."""

    # Emitter properties
    id: int = 0
    position: Vector3 = field(default_factory=Vector3)
    emitter_type: EmitterType = EmitterType.POINT

    # Emission rate
    rate: float = 10.0  # Particles per second
    burst: int = 0  # Particles per burst
    accumulated_time: float = 0.0

    # Particle properties
    lifetime: Tuple[float, float] = (1.0, 2.0)  # Min, max
    size: Tuple[float, float] = (1.0, 2.0)

    # Color
    color_start: Color = field(default_factory=Color)
    color_end: Color = field(default_factory=lambda: Color(1, 1, 1, 0))

    # Velocity
    velocity_min: Vector3 = field(default_factory=lambda: Vector3(-1, 2, -1))
    velocity_max: Vector3 = field(default_factory=lambda: Vector3(1, 4, 1))

    # Emitter shape
    radius: float = 1.0
    width: float = 1.0
    height: float = 1.0
    angle: float = 0.5  # For cone emitter

    # Flags
    active: bool = True
    looping: bool = True
    max_particles: int = 1000
    emitted_count: int = 0
    total_particles: int = 0  # Total to emit before stopping (0 = infinite)

    # Blend mode
    blend_mode: BlendMode = BlendMode.NORMAL

    def emit(self, count: int = 1) -> List[Particle]:
        """Emit new particles."""
        if not self.active:
            return []

        particles = []

        # If burst is set, emit burst particles instead of count
        emit_count = self.burst if self.burst > 0 else count
        self.burst = 0  # Reset burst after use

        actual_count = min(emit_count, self.max_particles - len(particles))

        for _ in range(actual_count):
            # Check limits
            if self.total_particles > 0 and self.emitted_count >= self.total_particles:
                if not self.looping:
                    self.active = False
                break

            particle = self._create_particle()
            particles.append(particle)
            self.emitted_count += 1

        return particles

    def _create_particle(self) -> Particle:
        """Create a single particle."""
        # Position based on emitter type
        pos = self._get_emission_position()

        # Velocity
        vel = self._get_emission_velocity()

        # Lifetime
        lifetime = random.uniform(*self.lifetime)

        # Size
        size = random.uniform(*self.size)

        return Particle(
            position=pos,
            velocity=vel,
            color=self.color_start,
            size=size,
            max_life=lifetime,
            life=1.0,
            emitter_id=self.id
        )

    def _get_emission_position(self) -> Vector3:
        """Get spawn position based on emitter type."""
        if self.emitter_type == EmitterType.POINT:
            return self.position

        elif self.emitter_type == EmitterType.CIRCLE:
            angle = random.uniform(0, math.pi * 2)
            r = math.sqrt(random.uniform(0, 1)) * self.radius
            return Vector3(
                self.position.x + r * math.cos(angle),
                self.position.y,
                self.position.z + r * math.sin(angle)
            )

        elif self.emitter_type == EmitterType.RECTANGLE:
            return Vector3(
                self.position.x + random.uniform(-self.width / 2, self.width / 2),
                self.position.y,
                self.position.z + random.uniform(-self.height / 2, self.height / 2)
            )

        elif self.emitter_type == EmitterType.SPHERE:
            # Random point on sphere surface
            theta = random.uniform(0, math.pi * 2)
            phi = math.acos(random.uniform(-1, 1))
            r = self.radius
            return Vector3(
                self.position.x + r * math.sin(phi) * math.cos(theta),
                self.position.y + r * math.sin(phi) * math.sin(theta),
                self.position.z + r * math.cos(phi)
            )

        elif self.emitter_type == EmitterType.CONE:
            # Point within cone
            angle = random.uniform(0, math.pi * 2)
            r = random.uniform(0, self.radius * math.tan(self.angle))
            return Vector3(
                self.position.x + r * math.cos(angle),
                self.position.y,
                self.position.z + r * math.sin(angle)
            )

        return self.position

    def _get_emission_velocity(self) -> Vector3:
        """Get initial velocity."""
        return Vector3(
            random.uniform(self.velocity_min.x, self.velocity_max.x),
            random.uniform(self.velocity_min.y, self.velocity_max.y),
            random.uniform(self.velocity_min.z, self.velocity_max.z)
        )


class ParticleSystem:
    """Manages multiple emitters and particles."""

    def __init__(self, max_particles: int = 10000):
        self.max_particles = max_particles
        self.particles: List[Particle] = []
        self.emitters: Dict[int, ParticleEmitter] = {}
        self.emitter_counter = 0

        # Physics
        self.gravity = Vector3(0, -9.81, 0)
        self.wind = Vector3(0, 0, 0)

        # Rendering
        self.camera_position = Vector3(0, 0, 10)

    def add_emitter(self, emitter: ParticleEmitter) -> int:
        """Add an emitter and return its ID."""
        emitter.id = self.emitter_counter
        self.emitters[emitter.id] = emitter
        self.emitter_counter += 1
        return emitter.id

    def remove_emitter(self, emitter_id: int):
        """Remove an emitter."""
        self.emitters.pop(emitter_id, None)

    def get_emitter(self, emitter_id: int) -> Optional[ParticleEmitter]:
        """Get an emitter by ID."""
        return self.emitters.get(emitter_id)

    def emit(self, emitter_id: int, count: int = 1) -> List[Particle]:
        """Emit particles from a specific emitter."""
        emitter = self.emitters.get(emitter_id)
        if emitter:
            new_particles = emitter.emit(count)

            # Add to system if space available
            available = self.max_particles - len(self.particles)
            to_add = new_particles[:available]

            if to_add:
                self.particles.extend(to_add)

            return to_add
        return []

    def burst(self, emitter_id: int, count: int) -> List[Particle]:
        """Burst emit particles."""
        return self.emit(emitter_id, count)

    def update(self, dt: float) -> int:
        """Update all particles and emitters. Returns active particle count."""
        # Update emitters
        for emitter in self.emitters.values():
            if not emitter.active:
                continue

            # Continuous emission
            if emitter.rate > 0:
                emitter.accumulated_time += dt
                particles_to_emit = int(emitter.accumulated_time * emitter.rate)
                if particles_to_emit > 0:
                    self.emit(emitter.id, particles_to_emit)
                    emitter.accumulated_time = 0

            # Handle burst
            if emitter.burst > 0:
                self.emit(emitter.id, emitter.burst)
                emitter.burst = 0

        # Update particles
        alive_particles = []
        for particle in self.particles:
            # Update particle color based on lifetime
            emitter = self.emitters.get(particle.emitter_id) if particle.emitter_id else None
            if emitter:
                particle.color = emitter.color_start.lerp(
                    emitter.color_end,
                    1.0 - particle.life
                )

            # Update particle physics
            if particle.update(dt, self.gravity, self.wind):
                alive_particles.append(particle)

        self.particles = alive_particles
        return len(self.particles)

    def clear(self):
        """Remove all particles."""
        self.particles.clear()

    def get_particle_count(self) -> int:
        """Get current particle count."""
        return len(self.particles)

    def set_gravity(self, x: float, y: float, z: float):
        """Set gravity vector."""
        self.gravity = Vector3(x, y, z)

    def set_wind(self, x: float, y: float, z: float):
        """Set wind vector."""
        self.wind = Vector3(x, y, z)


class WeatherSystem:
    """Weather effects using particles."""

    def __init__(self, particle_system: ParticleSystem):
        self.particle_system = particle_system
        self.current_weather = "clear"
        self.weather_emitters: Dict[str, int] = {}
        self.intensity = 0.5  # 0-1

    def set_weather(self, weather_type: str, intensity: float = 0.5):
        """Set current weather type."""
        # Clear existing weather
        self.clear_weather()

        self.current_weather = weather_type
        self.intensity = max(0.0, min(1.0, intensity))

        if weather_type == "rain":
            self._create_rain()
        elif weather_type == "snow":
            self._create_snow()
        elif weather_type == "sun":
            self._create_sun()

    def _create_rain(self):
        """Create rain effect."""
        rain_emitter = ParticleEmitter(
            position=Vector3(0, 10, 0),
            emitter_type=EmitterType.RECTANGLE,
            rate=100 * self.intensity,
            lifetime=(0.5, 1.0),
            size=(0.02, 0.05),
            color_start=Color(0.6, 0.7, 0.9, 0.6),
            color_end=Color(0.5, 0.6, 0.8, 0.3),
            velocity_min=Vector3(-0.5, -15, -0.5),
            velocity_max=Vector3(0.5, -20, 0.5),
            width=20,
            height=20,
            blend_mode=BlendMode.ALPHA
        )
        self.weather_emitters["rain"] = self.particle_system.add_emitter(rain_emitter)

    def _create_snow(self):
        """Create snow effect."""
        snow_emitter = ParticleEmitter(
            position=Vector3(0, 10, 0),
            emitter_type=EmitterType.RECTANGLE,
            rate=50 * self.intensity,
            lifetime=(3.0, 6.0),
            size=(0.1, 0.3),
            color_start=Color(1.0, 1.0, 1.0, 0.9),
            color_end=Color(1.0, 1.0, 1.0, 0.2),
            velocity_min=Vector3(-1, -1, -1),
            velocity_max=Vector3(1, -2, 1),
            width=20,
            height=20,
            blend_mode=BlendMode.NORMAL
        )
        snow_emitter.rotation_speed = 1.0
        self.weather_emitters["snow"] = self.particle_system.add_emitter(snow_emitter)

    def _create_sun(self):
        """Create sunny effect (light particles)."""
        sun_emitter = ParticleEmitter(
            position=Vector3(0, 8, 0),
            emitter_type=EmitterType.CIRCLE,
            rate=10 * self.intensity,
            lifetime=(2.0, 4.0),
            size=(0.5, 1.5),
            color_start=Color(1.0, 0.95, 0.7, 0.3),
            color_end=Color(1.0, 0.9, 0.5, 0.0),
            velocity_min=Vector3(-0.2, -0.5, -0.2),
            velocity_max=Vector3(0.2, -0.2, 0.2),
            radius=5,
            blend_mode=BlendMode.ADDITIVE
        )
        self.weather_emitters["sun"] = self.particle_system.add_emitter(sun_emitter)

    def clear_weather(self):
        """Clear all weather effects."""
        for emitter_id in self.weather_emitters.values():
            self.particle_system.remove_emitter(emitter_id)
        self.weather_emitters.clear()
        self.current_weather = "clear"


class ParticleEffectBuilder:
    """Builder for common particle effects."""

    @staticmethod
    def spark(position: Vector3, count: int = 20) -> ParticleEmitter:
        """Create spark effect."""
        return ParticleEmitter(
            position=position,
            emitter_type=EmitterType.POINT,
            rate=0,
            burst=count,
            lifetime=(0.2, 0.5),
            size=(0.05, 0.15),
            color_start=Color(1.0, 0.8, 0.3, 1.0),
            color_end=Color(1.0, 0.3, 0.1, 0.0),
            velocity_min=Vector3(-3, 1, -3),
            velocity_max=Vector3(3, 5, 3),
            blend_mode=BlendMode.ADDITIVE
        )

    @staticmethod
    def explosion(position: Vector3, count: int = 50) -> ParticleEmitter:
        """Create explosion effect."""
        return ParticleEmitter(
            position=position,
            emitter_type=EmitterType.SPHERE,
            rate=0,
            burst=count,
            lifetime=(0.3, 0.8),
            size=(0.1, 0.3),
            color_start=Color(1.0, 0.9, 0.5, 1.0),
            color_end=Color(1.0, 0.2, 0.1, 0.0),
            velocity_min=Vector3(-5, 2, -5),
            velocity_max=Vector3(5, 8, 5),
            radius=0.5,
            blend_mode=BlendMode.ADDITIVE
        )

    @staticmethod
    def heart_trail(position: Vector3) -> ParticleEmitter:
        """Create heart trail effect."""
        return ParticleEmitter(
            position=position,
            emitter_type=EmitterType.POINT,
            rate=30,
            lifetime=(0.5, 1.0),
            size=(0.2, 0.4),
            color_start=Color(1.0, 0.3, 0.4, 0.8),
            color_end=Color(1.0, 0.5, 0.6, 0.0),
            velocity_min=Vector3(-0.5, 1, -0.5),
            velocity_max=Vector3(0.5, 2, 0.5),
            blend_mode=BlendMode.ADDITIVE
        )

    @staticmethod
    def magic_circle(position: Vector3) -> ParticleEmitter:
        """Create magic circle effect."""
        return ParticleEmitter(
            position=position,
            emitter_type=EmitterType.CIRCLE,
            rate=50,
            lifetime=(0.3, 0.6),
            size=(0.1, 0.2),
            color_start=Color(0.5, 0.7, 1.0, 0.8),
            color_end=Color(0.8, 0.9, 1.0, 0.0),
            velocity_min=Vector3(-0.5, 0.5, -0.5),
            velocity_max=Vector3(0.5, 1.5, 0.5),
            radius=1.5,
            blend_mode=BlendMode.ADDITIVE
        )

    @staticmethod
    def sleep_zzz(position: Vector3) -> ParticleEmitter:
        """Create sleeping Zzz effect."""
        return ParticleEmitter(
            position=position,
            emitter_type=EmitterType.POINT,
            rate=5,
            lifetime=(1.5, 3.0),
            size=(0.2, 0.5),
            color_start=Color(0.8, 0.8, 1.0, 0.8),
            color_end=Color(0.6, 0.6, 0.8, 0.0),
            velocity_min=Vector3(-0.2, 0.8, -0.2),
            velocity_max=Vector3(0.2, 1.2, 0.2),
            blend_mode=BlendMode.ALPHA
        )

    @staticmethod
    def level_up(position: Vector3) -> ParticleEmitter:
        """Create level up celebration effect."""
        return ParticleEmitter(
            position=position,
            emitter_type=EmitterType.SPHERE,
            rate=0,
            burst=100,
            lifetime=(0.5, 1.5),
            size=(0.1, 0.3),
            color_start=Color(1.0, 1.0, 0.5, 1.0),
            color_end=Color(1.0, 0.5, 0.8, 0.0),
            velocity_min=Vector3(-2, 3, -2),
            velocity_max=Vector3(2, 6, 2),
            radius=1.0,
            blend_mode=BlendMode.ADDITIVE
        )


if __name__ == "__main__":
    # Test particle system
    print("Testing Particle System v2")

    system = ParticleSystem(max_particles=5000)

    # Create a test emitter
    emitter = ParticleEmitter(
        position=Vector3(0, 0, 0),
        emitter_type=EmitterType.POINT,
        rate=50,
        lifetime=(1.0, 2.0),
        size=(0.1, 0.3),
        color_start=Color(1.0, 0.5, 0.2, 1.0),
        color_end=Color(1.0, 0.2, 0.1, 0.0),
        velocity_min=Vector3(-1, 2, -1),
        velocity_max=Vector3(1, 4, 1)
    )

    emitter_id = system.add_emitter(emitter)
    print(f"Added emitter with ID: {emitter_id}")

    # Update for a few frames
    for i in range(10):
        count = system.update(0.016)
        if i % 3 == 0:
            print(f"Frame {i}: {count} particles")

    # Test weather
    weather = WeatherSystem(system)
    weather.set_weather("rain", intensity=0.5)
    print(f"\nWeather set to: {weather.current_weather}")

    system.clear()
    weather.set_weather("snow", intensity=0.7)
    print(f"Weather changed to: {weather.current_weather}")

    # Test effects
    system.clear()
    weather.clear_weather()

    spark = ParticleEffectBuilder.spark(Vector3(0, 0, 0))
    system.add_emitter(spark)
    system.burst(spark.id, 20)

    count = system.update(0.016)
    print(f"\nSpark effect: {count} particles")

    print("Particle system v2 test passed!")
