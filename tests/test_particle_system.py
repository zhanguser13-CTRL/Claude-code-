"""
Unit Tests for Particle System v2

Tests the advanced particle system with physics.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_pet_companion.render.particles_v2 import (
    Vector2, Vector3,
    AABB,
    CircleCollider,
    PhysicsBody,
    PhysicsWorld,
    Spring,
    Particle,
    ParticleEmitter,
    ParticleSystem,
    WeatherSystem,
    ParticleEffectBuilder,
    ColliderType
)


class TestVector2:
    """Test 2D vector operations."""

    def test_vector_creation(self):
        """Test creating vectors."""
        v = Vector2(3.0, 4.0)
        assert v.x == 3.0
        assert v.y == 4.0

    def test_vector_addition(self):
        """Test vector addition."""
        v1 = Vector2(1.0, 2.0)
        v2 = Vector2(3.0, 4.0)
        result = v1 + v2
        assert result.x == 4.0
        assert result.y == 6.0

    def test_vector_subtraction(self):
        """Test vector subtraction."""
        v1 = Vector2(5.0, 10.0)
        v2 = Vector2(2.0, 3.0)
        result = v1 - v2
        assert result.x == 3.0
        assert result.y == 7.0

    def test_vector_scalar_multiplication(self):
        """Test scalar multiplication."""
        v = Vector2(2.0, 3.0)
        result = v * 2
        assert result.x == 4.0
        assert result.y == 6.0

    def test_vector_dot_product(self):
        """Test dot product."""
        v1 = Vector2(1.0, 2.0)
        v2 = Vector2(3.0, 4.0)
        result = v1.dot(v2)
        assert result == 11.0  # 1*3 + 2*4

    def test_vector_length(self):
        """Test vector magnitude."""
        v = Vector2(3.0, 4.0)
        assert v.length() == 5.0

    def test_vector_normalize(self):
        """Test vector normalization."""
        v = Vector2(0.0, 3.0)
        normalized = v.normalize()
        assert normalized.x == 0.0
        assert normalized.y == 1.0

    def test_vector_distance(self):
        """Test distance calculation."""
        v1 = Vector2(0.0, 0.0)
        v2 = Vector2(3.0, 4.0)
        assert v1.distance_to(v2) == 5.0


class TestAABB:
    """Test Axis-Aligned Bounding Box."""

    def test_creation_from_center(self):
        """Test creating AABB from center point."""
        aabb = AABB.from_center(Vector2(10.0, 10.0), Vector2(6.0, 4.0))
        assert aabb.min_x == 7.0  # 10 - 3
        assert aabb.max_x == 13.0  # 10 + 3
        assert aabb.min_y == 8.0   # 10 - 2
        assert aabb.max_y == 12.0  # 10 + 2

    def test_contains_point(self):
        """Test point containment."""
        aabb = AABB.from_center(Vector2(0.0, 0.0), Vector2(10.0, 10.0))
        assert aabb.contains(Vector2(0.0, 0.0))
        assert aabb.contains(Vector2(5.0, 0.0))
        assert not aabb.contains(Vector2(6.0, 0.0))

    def test_intersects(self):
        """Test AABB intersection."""
        aabb1 = AABB.from_center(Vector2(0.0, 0.0), Vector2(10.0, 10.0))
        aabb2 = AABB.from_center(Vector2(5.0, 0.0), Vector2(10.0, 10.0))

        assert aabb1.intersects(aabb2)

        # Non-overlapping
        aabb3 = AABB.from_center(Vector2(20.0, 20.0), Vector2(5.0, 5.0))
        assert not aabb1.intersects(aabb3)


class TestCircleCollider:
    """Test circle collider."""

    def test_contains_point(self):
        """Test point containment in circle."""
        circle = CircleCollider(Vector2(0.0, 0.0), 5.0)
        assert circle.contains(Vector2(0.0, 0.0))
        assert circle.contains(Vector2(3.0, 0.0))
        assert circle.contains(Vector2(0.0, 3.0))
        assert not circle.contains(Vector2(6.0, 0.0))

    def test_intersects_circle(self):
        """Test circle-circle intersection."""
        circle1 = CircleCollider(Vector2(0.0, 0.0), 5.0)
        circle2 = CircleCollider(Vector2(8.0, 0.0), 5.0)

        assert circle1.intersects(circle2)

        # Non-overlapping
        circle3 = CircleCollider(Vector2(20.0, 0.0), 5.0)
        assert not circle1.intersects(circle3)

    def test_intersects_aabb(self):
        """Test circle-AABB intersection."""
        circle = CircleCollider(Vector2(0.0, 0.0), 5.0)
        aabb = AABB.from_center(Vector2(2.0, 0.0), Vector2(6.0, 6.0))

        assert circle.intersects_aabb(aabb)


class TestPhysicsBody:
    """Test physics body."""

    def test_creation(self):
        """Test creating a physics body."""
        body = PhysicsBody(
            position=Vector2(0.0, 0.0),
            mass=1.0,
            collider_data={'radius': 1.0},
            collider_type=ColliderType.CIRCLE
        )

        assert body.position.x == 0.0
        assert body.mass == 1.0

    def test_apply_force(self):
        """Test applying force changes acceleration."""
        body = PhysicsBody(
            position=Vector2(0.0, 0.0),
            mass=2.0
        )

        body.apply_force(Vector2(4.0, 0.0))

        # F = ma -> a = F/m
        assert body.acceleration.x == 2.0  # 4.0 / 2.0

    def test_update(self):
        """Test physics update."""
        body = PhysicsBody(
            position=Vector2(0.0, 0.0),
            velocity=Vector2(10.0, 0.0),
            mass=1.0
        )

        body.update(0.1)

        # Position should have changed
        assert body.position.x > 0.0

    def test_static_body(self):
        """Test static bodies don't move."""
        body = PhysicsBody(
            position=Vector2(0.0, 0.0),
            velocity=Vector2(10.0, 0.0),
            is_static=True
        )

        initial_x = body.position.x
        body.update(0.1)

        assert body.position.x == initial_x

    def test_inv_mass_zero(self):
        """Test infinite mass object (static)."""
        body = PhysicsBody(
            position=Vector2(0.0, 0.0),
            mass=0
        )

        assert body.inv_mass == 0.0


class TestPhysicsWorld:
    """Test physics world simulation."""

    def test_add_remove_body(self):
        """Test adding and removing bodies."""
        world = PhysicsWorld()

        body = PhysicsBody(position=Vector2(0.0, 0.0))
        world.add_body(body)

        assert len(world.bodies) == 1

        world.remove_body(body)

        assert len(world.bodies) == 0

    def test_gravity(self):
        """Test gravity affects falling objects."""
        world = PhysicsWorld(gravity=Vector2(0, -9.81))

        body = PhysicsBody(
            position=Vector2(0.0, 10.0),
            mass=1.0,
            collider_data={'size': (1.0, 1.0)},
            collider_type=ColliderType.AABB
        )

        world.add_body(body)

        initial_y = body.position.y
        world.step(0.1)

        # Should have fallen
        assert body.position.y < initial_y

    def test_collision_detection(self):
        """Test collision detection between bodies."""
        world = PhysicsWorld()

        body1 = PhysicsBody(
            position=Vector2(0.0, 0.0),
            mass=1.0,
            collider_data={'radius': 1.0},
            collider_type=ColliderType.CIRCLE
        )

        body2 = PhysicsBody(
            position=Vector2(1.5, 0.0),
            mass=1.0,
            collider_data={'radius': 1.0},
            collider_type=ColliderType.CIRCLE
        )

        world.add_body(body1)
        world.add_body(body2)

        # They should not be colliding initially
        assert len(world.collisions) == 0

        # Move them together
        body2.position = Vector2(0.5, 0.0)
        world.step(0.0)

        # Should detect collision
        assert len(world.collisions) > 0


class TestParticle:
    """Test individual particle."""

    def test_creation(self):
        """Test creating a particle."""
        particle = Particle(
            position=Vector3(0.0, 0.0, 0.0),
            velocity=Vector3(1.0, 2.0, 3.0)
        )

        assert particle.position.x == 0.0
        assert particle.velocity.y == 2.0
        assert particle.velocity.z == 3.0

    def test_update(self):
        """Test particle update."""
        particle = Particle(
            position=Vector3(0.0, 0.0, 0.0),
            velocity=Vector3(1.0, 0.0, 0.0),
            mass=1.0
        )

        initial_life = particle.life
        alive = particle.update(0.1, Vector3(0, 0, 0))

        assert alive is True
        assert particle.life == initial_life

    def test_life_decay(self):
        """Test particle life decay."""
        particle = Particle(
            position=Vector3(0.0, 0.0, 0.0),
            max_life=1.0,
            lifetime_enabled=True
        )

        # Update past max_life
        particle.update(2.0, Vector3(0, 0, 0))

        assert not particle.alive
        assert particle.life == 0.0


class TestParticleEmitter:
    """Test particle emitter."""

    def test_emit(self):
        """Test emitting particles."""
        emitter = ParticleEmitter(
            position=Vector3(0.0, 0.0, 0.0),
            rate=10,
            lifetime=(1.0, 1.0),
            size=(1.0, 1.0)
        )

        particles = emitter.emit(5)

        assert len(particles) == 5
        for p in particles:
            assert isinstance(p, Particle)

    def test_emit_limits(self):
        """Test emitter respects max_particles."""
        emitter = ParticleEmitter(
            position=Vector3(0.0, 0.0, 0.0),
            rate=10,
            max_particles=3
        )

        particles = emitter.emit(5)

        assert len(particles) <= 3

    def test_burst(self):
        """Test burst emission."""
        emitter = ParticleEmitter(
            position=Vector3(0.0, 0.0, 0.0),
            burst=5
        )

        particles = emitter.emit(1)

        assert len(particles) == 5


class TestParticleSystem:
    """Test particle system."""

    def test_add_emitter(self):
        """Test adding an emitter."""
        system = ParticleSystem(max_particles=100)

        emitter = ParticleEmitter(position=Vector3(0.0, 0.0, 0.0))
        emitter_id = system.add_emitter(emitter)

        assert emitter_id in system.emitters

    def test_remove_emitter(self):
        """Test removing an emitter."""
        system = ParticleSystem()

        emitter = ParticleEmitter(position=Vector3(0.0, 0.0, 0.0))
        emitter_id = system.add_emitter(emitter)

        system.remove_emitter(emitter_id)

        assert emitter_id not in system.emitters

    def test_update(self):
        """Test updating particle system."""
        system = ParticleSystem()

        emitter = ParticleEmitter(position=Vector3(0.0, 0.0, 0.0))
        system.add_emitter(emitter)

        count = system.update(0.016)
        assert isinstance(count, int)


class TestWeatherSystem:
    """Test weather effects."""

    def test_set_weather(self):
        """Test setting weather."""
        system = ParticleSystem(max_particles=100)
        weather = WeatherSystem(system)

        weather.set_weather("rain", intensity=0.5)

        assert weather.current_weather == "rain"

    def test_clear_weather(self):
        """Test clearing weather."""
        system = ParticleSystem(max_particles=100)
        weather = WeatherSystem(system)

        weather.set_weather("rain")
        weather.clear_weather()

        assert weather.current_weather == "clear"


class TestParticleEffectBuilder:
    """Test particle effect builders."""

    def test_create_spark(self):
        """Test creating spark effect."""
        builder = ParticleEffectBuilder

        emitter = builder.spark(position=Vector3(0.0, 0.0, 0.0), count=3)
        assert emitter.burst == 3

    def test_create_explosion(self):
        """Test creating explosion effect."""
        builder = ParticleEffectBuilder

        emitter = builder.explosion(position=Vector3(0.0, 0.0, 0.0), count=5)
        assert emitter.burst == 5

    def test_create_heart_trail(self):
        """Test creating heart trail effect."""
        builder = ParticleEffectBuilder

        emitter = builder.heart_trail(position=Vector3(0.0, 0.0, 0.0))
        assert emitter.rate > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
