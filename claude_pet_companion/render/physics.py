"""
Physics Engine for Claude Pet Companion

Provides realistic physics simulation with:
- Gravity and forces
- Collision detection (AABB, circle, polygon)
- Spring dynamics
- Particle physics
- Constraint solving
"""

import math
import logging
from typing import Dict, List, Tuple, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import time

logger = logging.getLogger(__name__)


class ColliderType(Enum):
    """Types of colliders."""
    NONE = "none"
    CIRCLE = "circle"
    AABB = "aabb"  # Axis-Aligned Bounding Box
    POLYGON = "polygon"


@dataclass
class Vector2:
    """2D vector for physics calculations."""
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

    def __neg__(self) -> 'Vector2':
        return Vector2(-self.x, -self.y)

    def dot(self, other: 'Vector2') -> float:
        """Dot product."""
        return self.x * other.x + self.y * other.y

    def cross(self, other: 'Vector2') -> float:
        """2D cross product (returns scalar)."""
        return self.x * other.y - self.y * other.x

    def length(self) -> float:
        """Vector magnitude."""
        return math.sqrt(self.x * self.x + self.y * self.y)

    def length_squared(self) -> float:
        """Vector magnitude squared (faster)."""
        return self.x * self.x + self.y * self.y

    def normalize(self) -> 'Vector2':
        """Return normalized unit vector."""
        length = self.length()
        if length > 0:
            return Vector2(self.x / length, self.y / length)
        return Vector2(0, 0)

    def perpendicular(self) -> 'Vector2':
        """Return perpendicular vector."""
        return Vector2(-self.y, self.x)

    def rotate(self, angle: float) -> 'Vector2':
        """Rotate vector by angle (radians)."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Vector2(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a
        )

    def distance_to(self, other: 'Vector2') -> float:
        """Distance to another vector."""
        return (self - other).length()

    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple."""
        return (self.x, self.y)


@dataclass
class Vector3:
    """3D vector for 3D physics."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def dot(self, other: 'Vector3') -> float:
        """Dot product."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: 'Vector3') -> 'Vector3':
        """Cross product."""
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    def length(self) -> float:
        """Vector magnitude."""
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalize(self) -> 'Vector3':
        """Return normalized unit vector."""
        length = self.length()
        if length > 0:
            return Vector3(self.x / length, self.y / length, self.z / length)
        return Vector3(0, 0, 0)


@dataclass
class AABB:
    """Axis-Aligned Bounding Box collider."""
    min_x: float = 0.0
    min_y: float = 0.0
    max_x: float = 0.0
    max_y: float = 0.0

    @classmethod
    def from_center(cls, center: Vector2, size: Vector2) -> 'AABB':
        """Create AABB from center point and size."""
        half_size = size * 0.5
        return cls(
            center.x - half_size.x,
            center.y - half_size.y,
            center.x + half_size.x,
            center.y + half_size.y
        )

    def contains(self, point: Vector2) -> bool:
        """Check if point is inside AABB."""
        return (self.min_x <= point.x <= self.max_x and
                self.min_y <= point.y <= self.max_y)

    def intersects(self, other: 'AABB') -> bool:
        """Check if two AABBs intersect."""
        return (self.min_x <= other.max_x and self.max_x >= other.min_x and
                self.min_y <= other.max_y and self.max_y >= other.min_y)

    def center(self) -> Vector2:
        """Get center point."""
        return Vector2((self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2)

    def size(self) -> Vector2:
        """Get size."""
        return Vector2(self.max_x - self.min_x, self.max_y - self.min_y)


@dataclass
class CircleCollider:
    """Circle collider."""
    center: Vector2 = field(default_factory=Vector2)
    radius: float = 1.0

    def contains(self, point: Vector2) -> bool:
        """Check if point is inside circle."""
        return self.center.distance_to(point) <= self.radius

    def intersects(self, other: 'CircleCollider') -> bool:
        """Check if two circles intersect."""
        return self.center.distance_to(other.center) <= (self.radius + other.radius)

    def intersects_aabb(self, aabb: AABB) -> bool:
        """Check intersection with AABB."""
        # Find closest point on AABB to circle center
        closest_x = max(aabb.min_x, min(self.center.x, aabb.max_x))
        closest_y = max(aabb.min_y, min(self.center.y, aabb.max_y))

        distance_x = self.center.x - closest_x
        distance_y = self.center.y - closest_y

        return (distance_x * distance_x + distance_y * distance_y) <= (self.radius * self.radius)


@dataclass
class PhysicsBody:
    """Physical body with mass and velocity."""
    position: Vector2 = field(default_factory=Vector2)
    velocity: Vector2 = field(default_factory=Vector2)
    acceleration: Vector2 = field(default_factory=Vector2)

    mass: float = 1.0
    inv_mass: float = 1.0
    restitution: float = 0.5  # Bounciness (0-1)
    friction: float = 0.3
    drag: float = 0.01

    is_static: bool = False
    is_kinematic: bool = False
    gravity_scale: float = 1.0

    # Collider
    collider_type: ColliderType = ColliderType.AABB
    collider_data: Optional[dict] = None

    # User data
    user_data: Dict = field(default_factory=dict)

    def __post_init__(self):
        if self.mass > 0:
            self.inv_mass = 1.0 / self.mass
        else:
            self.inv_mass = 0.0

    def apply_force(self, force: Vector2):
        """Apply force to body."""
        if not self.is_static:
            self.acceleration = self.acceleration + (force * self.inv_mass)

    def apply_impulse(self, impulse: Vector2):
        """Apply instantaneous impulse."""
        if not self.is_static and not self.is_kinematic:
            self.velocity = self.velocity + (impulse * self.inv_mass)

    def update(self, delta_time: float, gravity: Vector2 = None):
        """Update physics state."""
        if self.is_static:
            return

        # Apply gravity
        if gravity and self.gravity_scale > 0:
            gravity_force = gravity * self.mass * self.gravity_scale
            self.apply_force(gravity_force)

        # Apply drag
        self.velocity = self.velocity * (1.0 - self.drag)

        # Integrate velocity (Euler)
        self.velocity = self.velocity + (self.acceleration * delta_time)

        # Integrate position
        if not self.is_kinematic:
            self.position = self.position + (self.velocity * delta_time)

        # Reset acceleration
        self.acceleration = Vector2(0, 0)

    def get_aabb(self) -> Optional[AABB]:
        """Get AABB collider if applicable."""
        if self.collider_type == ColliderType.AABB and self.collider_data:
            size = Vector2(*self.collider_data.get('size', (1, 1)))
            return AABB.from_center(self.position, size)
        return None

    def get_circle(self) -> Optional[CircleCollider]:
        """Get circle collider if applicable."""
        if self.collider_type == ColliderType.CIRCLE and self.collider_data:
            return CircleCollider(
                self.position,
                self.collider_data.get('radius', 0.5)
            )
        return None


@dataclass
class Spring:
    """Spring connection between two bodies."""
    body_a: PhysicsBody
    body_b: PhysicsBody
    rest_length: float = 1.0
    stiffness: float = 100.0
    damping: float = 5.0

    def apply(self):
        """Apply spring forces to connected bodies."""
        delta = self.body_b.position - self.body_a.position
        distance = delta.length()

        if distance == 0:
            return

        # Hooke's law
        displacement = distance - self.rest_length
        direction = delta.normalize()
        spring_force = direction * (self.stiffness * displacement)

        # Damping
        rel_velocity = self.body_b.velocity - self.body_a.velocity
        damping_force = direction * (rel_velocity.dot(direction) * self.damping)

        total_force = spring_force + damping_force

        self.body_a.apply_force(total_force)
        self.body_b.apply_force(-total_force)


@dataclass
class Collision:
    """Collision result data."""
    body_a: PhysicsBody
    body_b: PhysicsBody
    normal: Vector2
    depth: float
    contacts: List[Vector2] = field(default_factory=list)


class PhysicsWorld:
    """Physics world simulation."""

    def __init__(self, gravity: Vector2 = None):
        self.gravity = gravity or Vector2(0, -9.81)
        self.bodies: List[PhysicsBody] = []
        self.springs: List[Spring] = []
        self.collisions: List[Collision] = []

        # Settings
        self.velocity_iterations = 8
        self.position_iterations = 3
        self.fixed_dt = 1.0 / 60.0

        # Callbacks
        self.on_collision: Optional[Callable[[Collision], None]] = None

        # Spatial hash for broad phase
        self.spatial_hash: Dict[Tuple[int, int], List[int]] = {}
        self.cell_size = 64

    def add_body(self, body: PhysicsBody):
        """Add a body to the world."""
        if body not in self.bodies:
            self.bodies.append(body)

    def remove_body(self, body: PhysicsBody):
        """Remove a body from the world."""
        if body in self.bodies:
            self.bodies.remove(body)

    def add_spring(self, spring: Spring):
        """Add a spring to the world."""
        if spring not in self.springs:
            self.springs.append(spring)

    def step(self, delta_time: float = None):
        """Step the physics simulation."""
        dt = delta_time or self.fixed_dt

        # Update bodies
        for body in self.bodies:
            body.update(dt, self.gravity)

        # Apply spring forces
        for spring in self.springs:
            spring.apply()

        # Detect collisions
        self.collisions.clear()
        self._broad_phase()
        self._narrow_phase()

        # Resolve collisions
        for _ in range(self.velocity_iterations):
            self._resolve_velocities()

        for _ in range(self.position_iterations):
            self._resolve_positions()

    def _broad_phase(self):
        """Broad phase collision detection using spatial hashing."""
        self.spatial_hash.clear()

        # Build spatial hash
        for i, body in enumerate(self.bodies):
            if body.is_static:
                continue

            cell_x = int(body.position.x // self.cell_size)
            cell_y = int(body.position.y // self.cell_size)

            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    key = (cell_x + dx, cell_y + dy)
                    if key not in self.spatial_hash:
                        self.spatial_hash[key] = []
                    self.spatial_hash[key].append(i)

    def _narrow_phase(self):
        """Narrow phase collision detection."""
        checked: Set[Tuple[int, int]] = set()

        for key, body_indices in self.spatial_hash.items():
            for i in range(len(body_indices)):
                for j in range(i + 1, len(body_indices)):
                    idx_a, idx_b = body_indices[i], body_indices[j]
                    pair = tuple(sorted((idx_a, idx_b)))

                    if pair in checked:
                        continue
                    checked.add(pair)

                    body_a = self.bodies[idx_a]
                    body_b = self.bodies[idx_b]

                    collision = self._check_collision(body_a, body_b)
                    if collision:
                        self.collisions.append(collision)
                        if self.on_collision:
                            self.on_collision(collision)

    def _check_collision(self, body_a: PhysicsBody, body_b: PhysicsBody) -> Optional[Collision]:
        """Check collision between two bodies."""
        # Circle vs Circle
        if (body_a.collider_type == ColliderType.CIRCLE and
            body_b.collider_type == ColliderType.CIRCLE):
            return self._circle_vs_circle(body_a, body_b)

        # AABB vs AABB
        if (body_a.collider_type == ColliderType.AABB and
            body_b.collider_type == ColliderType.AABB):
            return self._aabb_vs_aabb(body_a, body_b)

        # Circle vs AABB
        if (body_a.collider_type == ColliderType.CIRCLE and
            body_b.collider_type == ColliderType.AABB):
            return self._circle_vs_aabb(body_a, body_b)

        # AABB vs Circle
        if (body_a.collider_type == ColliderType.AABB and
            body_b.collider_type == ColliderType.CIRCLE):
            collision = self._circle_vs_aabb(body_b, body_a)
            if collision:
                collision.normal = -collision.normal
            return collision

        return None

    def _circle_vs_circle(self, body_a: PhysicsBody, body_b: PhysicsBody) -> Optional[Collision]:
        """Check circle vs circle collision."""
        circle_a = body_a.get_circle()
        circle_b = body_b.get_circle()

        if not circle_a or not circle_b:
            return None

        delta = circle_b.center - circle_a.center
        distance = delta.length()
        radius_sum = circle_a.radius + circle_b.radius

        if distance < radius_sum and distance > 0:
            normal = delta.normalize()
            depth = radius_sum - distance
            return Collision(body_a, body_b, normal, depth)

        return None

    def _aabb_vs_aabb(self, body_a: PhysicsBody, body_b: PhysicsBody) -> Optional[Collision]:
        """Check AABB vs AABB collision."""
        aabb_a = body_a.get_aabb()
        aabb_b = body_b.get_aabb()

        if not aabb_a or not aabb_b:
            return None

        if not aabb_a.intersects(aabb_b):
            return None

        # Calculate overlap and normal
        center_a = aabb_a.center()
        center_b = aabb_b.center()

        delta = center_b - center_a
        overlap_x = (aabb_a.size().x + aabb_b.size().x) / 2 - abs(delta.x)
        overlap_y = (aabb_a.size().y + aabb_b.size().y) / 2 - abs(delta.y)

        if overlap_x < overlap_y:
            normal = Vector2(1 if delta.x > 0 else -1, 0)
            depth = overlap_x
        else:
            normal = Vector2(0, 1 if delta.y > 0 else -1)
            depth = overlap_y

        return Collision(body_a, body_b, normal, depth)

    def _circle_vs_aabb(self, circle_body: PhysicsBody, aabb_body: PhysicsBody) -> Optional[Collision]:
        """Check circle vs AABB collision."""
        circle = circle_body.get_circle()
        aabb = aabb_body.get_aabb()

        if not circle or not aabb:
            return None

        # Find closest point on AABB
        closest_x = max(aabb.min_x, min(circle.center.x, aabb.max_x))
        closest_y = max(aabb.min_y, min(circle.center.y, aabb.max_y))
        closest = Vector2(closest_x, closest_y)

        delta = circle.center - closest
        distance = delta.length()

        if distance < circle.radius:
            if distance > 0:
                normal = delta.normalize()
            else:
                # Circle center is inside AABB
                normal = Vector2(0, 1)
            depth = circle.radius - distance
            return Collision(circle_body, aabb_body, normal, depth)

        return None

    def _resolve_velocities(self):
        """Resolve collision velocities."""
        for collision in self.collisions:
            body_a, body_b = collision.body_a, collision.body_b
            normal = collision.normal

            # Relative velocity
            rel_velocity = body_b.velocity - body_a.velocity
            velocity_along_normal = rel_velocity.dot(normal)

            # Only resolve if objects are moving toward each other
            if velocity_along_normal > 0:
                continue

            # Calculate restitution
            e = min(body_a.restitution, body_b.restitution)

            # Calculate impulse scalar
            j = -(1 + e) * velocity_along_normal
            j /= (body_a.inv_mass + body_b.inv_mass)

            # Apply impulse
            impulse = normal * j
            body_a.velocity = body_a.velocity - (impulse * body_a.inv_mass)
            body_b.velocity = body_b.velocity + (impulse * body_b.inv_mass)

            # Apply friction
            tangent = rel_velocity - (normal * velocity_along_normal)
            if tangent.length_squared() > 0:
                tangent = tangent.normalize()
                friction_coef = (body_a.friction + body_b.friction) / 2
                jt = -rel_velocity.dot(tangent)
                jt /= (body_a.inv_mass + body_b.inv_mass)

                # Clamp friction
                max_jt = j * friction_coef
                jt = max(-max_jt, min(max_jt, jt))

                friction_impulse = tangent * jt
                body_a.velocity = body_a.velocity - (friction_impulse * body_a.inv_mass)
                body_b.velocity = body_b.velocity + (friction_impulse * body_b.inv_mass)

    def _resolve_positions(self):
        """Resolve collision positions (prevent sinking)."""
        percent = 0.8  # Penetration percentage to correct
        slop = 0.01  # Penetration allowance

        for collision in self.collisions:
            body_a, body_b = collision.body_a, collision.body_b
            normal = collision.normal
            depth = collision.depth

            # Calculate positional correction
            correction_mag = max(depth - slop, 0) / (body_a.inv_mass + body_b.inv_mass) * percent
            correction = normal * correction_mag

            body_a.position = body_a.position - (correction * body_a.inv_mass)
            body_b.position = body_b.position + (correction * body_b.inv_mass)

    def query_point(self, point: Vector2) -> List[PhysicsBody]:
        """Find bodies containing a point."""
        results = []
        for body in self.bodies:
            if body.collider_type == ColliderType.AABB:
                aabb = body.get_aabb()
                if aabb and aabb.contains(point):
                    results.append(body)
            elif body.collider_type == ColliderType.CIRCLE:
                circle = body.get_circle()
                if circle and circle.contains(point):
                    results.append(body)
        return results

    def query_aabb(self, aabb: AABB) -> List[PhysicsBody]:
        """Find bodies intersecting an AABB."""
        results = []
        for body in self.bodies:
            if body.collider_type == ColliderType.AABB:
                body_aabb = body.get_aabb()
                if body_aabb and body_aabb.intersects(aabb):
                    results.append(body)
            elif body.collider_type == ColliderType.CIRCLE:
                circle = body.get_circle()
                if circle and circle.intersects_aabb(aabb):
                    results.append(body)
        return results

    def raycast(self, start: Vector2, end: Vector2) -> Optional[Tuple[PhysicsBody, Vector2, float]]:
        """
        Cast a ray and find first intersection.

        Returns:
            (body, point, t) or None
        """
        direction = end - start
        max_t = 1.0
        closest_t = max_t
        closest_body = None
        closest_point = None

        for body in self.bodies:
            if body.collider_type == ColliderType.AABB:
                result = self._ray_aabb(start, direction, body.get_aabb())
                if result and result[2] < closest_t:
                    closest_t = result[2]
                    closest_body = body
                    closest_point = result[1]

            elif body.collider_type == ColliderType.CIRCLE:
                result = self._ray_circle(start, direction, body.get_circle())
                if result and result[2] < closest_t:
                    closest_t = result[2]
                    closest_body = body
                    closest_point = result[1]

        if closest_body:
            return (closest_body, closest_point, closest_t)
        return None

    def _ray_aabb(self, start: Vector2, direction: Vector2, aabb: AABB) -> Optional[Tuple[Vector2, Vector2, float]]:
        """Ray-AABB intersection test."""
        if direction.x == 0 and direction.y == 0:
            return None

        t_min = 0.0
        t_max = 1.0

        # X axis
        if direction.x != 0:
            tx1 = (aabb.min_x - start.x) / direction.x
            tx2 = (aabb.max_x - start.x) / direction.x
            t_min = max(t_min, min(tx1, tx2))
            t_max = min(t_max, max(tx1, tx2))
        elif start.x < aabb.min_x or start.x > aabb.max_x:
            return None

        # Y axis
        if direction.y != 0:
            ty1 = (aabb.min_y - start.y) / direction.y
            ty2 = (aabb.max_y - start.y) / direction.y
            t_min = max(t_min, min(ty1, ty2))
            t_max = min(t_max, max(ty1, ty2))
        elif start.y < aabb.min_y or start.y > aabb.max_y:
            return None

        if t_min > t_max:
            return None

        hit_point = start + direction * t_min
        return (start, hit_point, t_min)

    def _ray_circle(self, start: Vector2, direction: Vector2, circle: CircleCollider) -> Optional[Tuple[Vector2, Vector2, float]]:
        """Ray-circle intersection test."""
        oc = start - circle.center
        a = direction.dot(direction)
        b = 2.0 * oc.dot(direction)
        c = oc.dot(oc) - circle.radius * circle.radius

        discriminant = b * b - 4 * a * c
        if discriminant < 0:
            return None

        sqrt_disc = math.sqrt(discriminant)
        t1 = (-b - sqrt_disc) / (2 * a)
        t2 = (-b + sqrt_disc) / (2 * a)

        t = None
        if 0 <= t1 <= 1:
            t = t1
        elif 0 <= t2 <= 1:
            t = t2

        if t is not None:
            hit_point = start + direction * t
            return (start, hit_point, t)

        return None


class Ragdoll:
    """Simple ragdoll physics for pet."""

    def __init__(self, world: PhysicsWorld, origin: Vector2):
        self.bodies: List[PhysicsBody] = []
        self.springs: List[Spring] = []
        self.world = world

        self._build(origin)

    def _build(self, origin: Vector2):
        """Build ragdoll bodies and constraints."""
        # Head
        head = PhysicsBody(
            position=origin + Vector2(0, 1.0),
            mass=2.0,
            collider_data={'radius': 0.4},
            collider_type=ColliderType.CIRCLE
        )
        self.bodies.append(head)
        self.world.add_body(head)

        # Body
        body = PhysicsBody(
            position=origin + Vector2(0, 0.2),
            mass=5.0,
            collider_data={'size': (0.6, 0.8)},
            collider_type=ColliderType.AABB
        )
        self.bodies.append(body)
        self.world.add_body(body)

        # Connect head to body
        neck = Spring(head, body, rest_length=0.4, stiffness=200, damping=10)
        self.springs.append(neck)
        self.world.add_spring(neck)

        # Add gravity dampening for floating effect
        head.gravity_scale = 0.1
        body.gravity_scale = 0.1


if __name__ == "__main__":
    # Test physics engine
    print("Testing Physics Engine")

    world = PhysicsWorld(gravity=Vector2(0, -5.0))

    # Create test bodies
    ground = PhysicsBody(
        position=Vector2(0, -2),
        mass=0,  # Static
        is_static=True,
        collider_data={'size': (20, 1)},
        collider_type=ColliderType.AABB
    )
    world.add_body(ground)

    ball = PhysicsBody(
        position=Vector2(0, 3),
        mass=1.0,
        restitution=0.7,
        collider_data={'radius': 0.5},
        collider_type=ColliderType.CIRCLE
    )
    world.add_body(ball)

    # Simulate
    for i in range(100):
        world.step(0.016)
        if i % 10 == 0:
            print(f"Step {i}: Ball at y={ball.position.y:.2f}, vy={ball.velocity.y:.2f}")

    print("Physics engine test passed!")
