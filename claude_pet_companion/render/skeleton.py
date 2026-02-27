"""
Skeletal Animation System

Provides bone-based animation with:
- Hierarchical bone structure
- Skinning weights for vertex deformation
- Animation keyframes and interpolation
- Blend trees for animation blending
- Procedural animation generation
"""

import math
import logging
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class InterpolationType(Enum):
    """Types of keyframe interpolation."""
    LINEAR = "linear"
    STEP = "step"
    CUBIC = "cubic"
    BEZIER = "bezier"


@dataclass
class Transform:
    """3D transform with position, rotation, and scale."""
    px: float = 0.0  # Position X
    py: float = 0.0  # Position Y
    pz: float = 0.0  # Position Z

    rx: float = 0.0  # Rotation X (radians)
    ry: float = 0.0  # Rotation Y (radians)
    rz: float = 0.0  # Rotation Z (radians)

    sx: float = 1.0  # Scale X
    sy: float = 1.0  # Scale Y
    sz: float = 1.0  # Scale Z

    def to_matrix(self) -> List[float]:
        """Convert to 4x4 transformation matrix."""
        # Translation matrix
        t_mat = [
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            self.px, self.py, self.pz, 1.0
        ]

        # Rotation matrices (XYZ Euler)
        cos_x, sin_x = math.cos(self.rx), math.sin(self.rx)
        cos_y, sin_y = math.cos(self.ry), math.sin(self.ry)
        cos_z, sin_z = math.cos(self.rz), math.sin(self.rz)

        rx_mat = [
            1.0, 0.0, 0.0, 0.0,
            0.0, cos_x, -sin_x, 0.0,
            0.0, sin_x, cos_x, 0.0,
            0.0, 0.0, 0.0, 1.0
        ]

        ry_mat = [
            cos_y, 0.0, sin_y, 0.0,
            0.0, 1.0, 0.0, 0.0,
            -sin_y, 0.0, cos_y, 0.0,
            0.0, 0.0, 0.0, 1.0
        ]

        rz_mat = [
            cos_z, -sin_z, 0.0, 0.0,
            sin_z, cos_z, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0
        ]

        # Scale matrix
        s_mat = [
            self.sx, 0.0, 0.0, 0.0,
            0.0, self.sy, 0.0, 0.0,
            0.0, 0.0, self.sz, 0.0,
            0.0, 0.0, 0.0, 1.0
        ]

        # Combine: T * Rz * Ry * Rx * S
        return self._multiply_matrices(t_mat,
                self._multiply_matrices(rz_mat,
                self._multiply_matrices(ry_mat,
                self._multiply_matrices(rx_mat, s_mat))))

    def _multiply_matrices(self, a: List[float], b: List[float]) -> List[float]:
        """Multiply two 4x4 matrices."""
        result = [0.0] * 16
        for row in range(4):
            for col in range(4):
                result[row * 4 + col] = (
                    a[row * 4 + 0] * b[0 * 4 + col] +
                    a[row * 4 + 1] * b[1 * 4 + col] +
                    a[row * 4 + 2] * b[2 * 4 + col] +
                    a[row * 4 + 3] * b[3 * 4 + col]
                )
        return result

    def lerp(self, other: 'Transform', t: float) -> 'Transform':
        """Linear interpolation between two transforms."""
        return Transform(
            px=self.px + (other.px - self.px) * t,
            py=self.py + (other.py - self.py) * t,
            pz=self.pz + (other.pz - self.pz) * t,
            rx=self.rx + (other.rx - self.rx) * t,
            ry=self.ry + (other.ry - self.ry) * t,
            rz=self.rz + (other.rz - self.rz) * t,
            sx=self.sx + (other.sx - self.sx) * t,
            sy=self.sy + (other.sy - self.sy) * t,
            sz=self.sz + (other.sz - self.sz) * t,
        )

    def copy(self) -> 'Transform':
        """Create a copy of this transform."""
        return Transform(
            self.px, self.py, self.pz,
            self.rx, self.ry, self.rz,
            self.sx, self.sy, self.sz
        )


@dataclass
class Keyframe:
    """Animation keyframe at a specific time."""
    time: float
    transform: Transform
    interpolation: InterpolationType = InterpolationType.LINEAR

    # For cubic/bezier interpolation
    tangent_in: Optional[Transform] = None
    tangent_out: Optional[Transform] = None


@dataclass
class Bone:
    """A single bone in the skeleton."""
    name: str
    parent_name: Optional[str] = None
    local_transform: Transform = field(default_factory=Transform)
    length: float = 1.0

    # Skin binding
    inverse_bind_matrix: List[float] = field(default_factory=lambda: [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])

    # Children bones
    children: List[str] = field(default_factory=list)


@dataclass
class SkinningWeight:
    """Vertex skinning weight."""
    bone_index: int
    weight: float


@dataclass
class AnimatedVertex:
    """Vertex with skinning information."""
    position: Tuple[float, float, float]
    normal: Tuple[float, float, float]
    tex_coord: Tuple[float, float]
    weights: List[SkinningWeight] = field(default_factory=list)

    def add_weight(self, bone_index: int, weight: float):
        """Add a bone weight (keeps only top 4)."""
        self.weights.append(SkinningWeight(bone_index, weight))
        # Sort by weight and keep top 4
        self.weights.sort(key=lambda w: w.weight, reverse=True)
        if len(self.weights) > 4:
            self.weights = self.weights[:4]

        # Normalize weights
        total = sum(w.weight for w in self.weights)
        if total > 0:
            for w in self.weights:
                w.weight /= total


@dataclass
class AnimationClip:
    """Animation clip with keyframes for multiple bones."""
    name: str
    duration: float  # in seconds
    loop: bool = True
    keyframes: Dict[str, List[Keyframe]] = field(default_factory=dict)

    def add_keyframe(self, bone_name: str, keyframe: Keyframe):
        """Add a keyframe for a bone."""
        if bone_name not in self.keyframes:
            self.keyframes[bone_name] = []
        self.keyframes[bone_name].append(keyframe)
        # Sort by time
        self.keyframes[bone_name].sort(key=lambda k: k.time)

    def get_transform_at(self, bone_name: str, time: float) -> Transform:
        """Get interpolated transform for a bone at a given time."""
        if bone_name not in self.keyframes or not self.keyframes[bone_name]:
            return Transform()

        keyframes = self.keyframes[bone_name]

        # Handle looping
        if self.loop and time > self.duration:
            time = time % self.duration

        # Find surrounding keyframes
        prev_kf = None
        next_kf = None

        for kf in keyframes:
            if kf.time <= time:
                prev_kf = kf
            elif next_kf is None:
                next_kf = kf
                break

        # Handle edge cases
        if prev_kf is None:
            return keyframes[0].transform
        if next_kf is None:
            return keyframes[-1].transform

        # Interpolate
        if prev_kf.interpolation == InterpolationType.STEP:
            return prev_kf.transform.copy()

        t = (time - prev_kf.time) / (next_kf.time - prev_kf.time)
        return prev_kf.transform.lerp(next_kf.transform, t)


class Skeleton:
    """Hierarchical skeleton for skeletal animation."""

    def __init__(self, name: str = "skeleton"):
        self.name = name
        self.bones: Dict[str, Bone] = {}
        self.root_bones: List[str] = []

        # Animation clips
        self.animations: Dict[str, AnimationClip] = {}
        self.current_animation: Optional[str] = None
        self.animation_time: float = 0.0

        # Bone index map for skinning
        self.bone_indices: Dict[str, int] = {}

    def add_bone(self, bone: Bone):
        """Add a bone to the skeleton."""
        self.bones[bone.name] = bone
        self.bone_indices[bone.name] = len(self.bone_indices)

        if bone.parent_name is None:
            self.root_bones.append(bone.name)
        elif bone.parent_name in self.bones:
            self.bones[bone.parent_name].children.append(bone.name)

    def get_bone(self, name: str) -> Optional[Bone]:
        """Get a bone by name."""
        return self.bones.get(name)

    def add_animation(self, animation: AnimationClip):
        """Add an animation clip."""
        self.animations[animation.name] = animation

    def play_animation(self, name: str, reset: bool = True):
        """Play an animation clip."""
        if name in self.animations:
            self.current_animation = name
            if reset:
                self.animation_time = 0.0
        else:
            logger.warning(f"Animation '{name}' not found")

    def update(self, delta_time: float):
        """Update animation playback."""
        if self.current_animation and self.current_animation in self.animations:
            self.animation_time += delta_time

    def get_bone_transforms(self, animation: Optional[str] = None,
                           time: Optional[float] = None) -> Dict[str, List[float]]:
        """
        Get world-space transform matrices for all bones.

        Returns:
            Dictionary mapping bone names to their 4x4 transform matrices
        """
        anim_name = animation or self.current_animation
        anim_time = time if time is not None else self.animation_time

        clip = self.animations.get(anim_name) if anim_name else None

        # Calculate transforms hierarchically
        transforms = {}

        def calculate_bone_transform(bone_name: str, parent_matrix: List[float]) -> List[float]:
            """Recursively calculate bone transform."""
            bone = self.bones[bone_name]

            # Get local transform (from animation or bind pose)
            if clip:
                local_transform = clip.get_transform_at(bone_name, anim_time)
            else:
                local_transform = bone.local_transform

            local_matrix = local_transform.to_matrix()

            # Calculate world matrix
            world_matrix = self._multiply_matrices(parent_matrix, local_matrix)
            transforms[bone_name] = world_matrix

            # Process children
            for child_name in bone.children:
                calculate_bone_transform(child_name, world_matrix)

            return world_matrix

        # Start with root bones
        identity = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]
        for root_name in self.root_bones:
            calculate_bone_transform(root_name, identity)

        return transforms

    def _multiply_matrices(self, a: List[float], b: List[float]) -> List[float]:
        """Multiply two 4x4 matrices."""
        result = [0.0] * 16
        for row in range(4):
            for col in range(4):
                result[row * 4 + col] = (
                    a[row * 4 + 0] * b[0 * 4 + col] +
                    a[row * 4 + 1] * b[1 * 4 + col] +
                    a[row * 4 + 2] * b[2 * 4 + col] +
                    a[row * 4 + 3] * b[3 * 4 + col]
                )
        return result

    def get_skinning_matrices(self) -> List[List[float]]:
        """
        Get skinning matrices (final pose * inverse bind pose).

        Returns:
            List of 4x4 matrices indexed by bone index
        """
        bone_transforms = self.get_bone_transforms()
        skinning_matrices = []

        # Ensure we have matrices for all bones
        for bone_name, bone_index in sorted(self.bone_indices.items(),
                                           key=lambda x: x[1]):
            if bone_name in bone_transforms:
                world_matrix = bone_transforms[bone_name]
                bone = self.bones[bone_name]
                # Multiply by inverse bind matrix
                final_matrix = self._multiply_matrices(world_matrix, bone.inverse_bind_matrix)
            else:
                final_matrix = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]

            # Extend list if needed
            while len(skinning_matrices) <= bone_index:
                skinning_matrices.append([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])

            skinning_matrices[bone_index] = final_matrix

        return skinning_matrices


class AnimationBlender:
    """Blends multiple animations together."""

    @staticmethod
    def blend(transforms_a: Dict[str, List[float]],
              transforms_b: Dict[str, List[float]],
              alpha: float) -> Dict[str, List[float]]:
        """
        Blend two sets of bone transforms.

        Args:
            transforms_a: First set of transforms
            transforms_b: Second set of transforms
            alpha: Blend factor (0.0 = all A, 1.0 = all B)

        Returns:
            Blended transforms
        """
        result = {}
        all_bones = set(transforms_a.keys()) | set(transforms_b.keys())

        for bone_name in all_bones:
            mat_a = transforms_a.get(bone_name, [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])
            mat_b = transforms_b.get(bone_name, [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])

            # Simple linear interpolation of matrices
            blended = [
                mat_a[i] + (mat_b[i] - mat_a[i]) * alpha
                for i in range(16)
            ]
            result[bone_name] = blended

        return result

    @staticmethod
    def blend_additive(base: Dict[str, List[float]],
                      additive: Dict[str, List[float]],
                      weight: float) -> Dict[str, List[float]]:
        """
        Blend additive animation on top of base animation.

        Args:
            base: Base animation transforms
            additive: Additive animation offsets
            weight: How much of the additive to apply

        Returns:
            Combined transforms
        """
        result = {}
        for bone_name, base_mat in base.items():
            add_mat = additive.get(bone_name)
            if add_mat:
                # Extract additive offset (subtract identity)
                offset = [add_mat[i] - (1 if i % 5 == 0 else 0) for i in range(16)]
                # Apply weighted offset
                result[bone_name] = [base_mat[i] + offset[i] * weight for i in range(16)]
            else:
                result[bone_name] = base_mat[:]
        return result


class ProceduralAnimation:
    """Procedurally generated animations."""

    @staticmethod
    def breathe(bone_transform: Transform, time: float,
                amplitude: float = 0.05, speed: float = 2.0) -> Transform:
        """Generate breathing animation."""
        scale = 1.0 + math.sin(time * speed) * amplitude
        result = bone_transform.copy()
        result.sx = result.sy = result.sz = scale
        return result

    @staticmethod
    def float_anim(bone_transform: Transform, time: float,
                   amplitude: float = 0.1, speed: float = 1.0) -> Transform:
        """Generate floating animation."""
        offset = math.sin(time * speed) * amplitude
        result = bone_transform.copy()
        result.py += offset
        return result

    @staticmethod
    def wiggle(bone_transform: Transform, time: float,
               axis: str = 'z', amplitude: float = 0.1, speed: float = 3.0) -> Transform:
        """Generate wiggle/rotation animation."""
        angle = math.sin(time * speed) * amplitude
        result = bone_transform.copy()
        if axis == 'x':
            result.rx = angle
        elif axis == 'y':
            result.ry = angle
        else:
            result.rz = angle
        return result


# Preset skeleton for pet

def create_pet_skeleton() -> Skeleton:
    """Create a basic skeleton for a pet."""
    skeleton = Skeleton("pet")

    # Root bone
    root = Bone("root", local_transform=Transform(py=-0.5))
    skeleton.add_bone(root)

    # Body
    body = Bone("body", parent_name="root", local_transform=Transform(py=0.5, sy=1.2))
    skeleton.add_bone(body)

    # Head
    head = Bone("head", parent_name="body", local_transform=Transform(py=1.0, sy=0.8))
    skeleton.add_bone(head)

    # Ears
    left_ear = Bone("ear_left", parent_name="head",
                   local_transform=Transform(px=-0.3, py=0.5, pz=0.2, rz=-0.3))
    right_ear = Bone("ear_right", parent_name="head",
                    local_transform=Transform(px=0.3, py=0.5, pz=0.2, rz=0.3))
    skeleton.add_bone(left_ear)
    skeleton.add_bone(right_ear)

    # Legs
    front_left_leg = Bone("leg_front_left", parent_name="body",
                         local_transform=Transform(px=-0.3, py=-0.8, pz=0.2))
    front_right_leg = Bone("leg_front_right", parent_name="body",
                          local_transform=Transform(px=0.3, py=-0.8, pz=0.2))
    back_left_leg = Bone("leg_back_left", parent_name="body",
                        local_transform=Transform(px=-0.3, py=-0.8, pz=-0.2))
    back_right_leg = Bone("leg_back_right", parent_name="body",
                         local_transform=Transform(px=0.3, py=-0.8, pz=-0.2))
    skeleton.add_bone(front_left_leg)
    skeleton.add_bone(front_right_leg)
    skeleton.add_bone(back_left_leg)
    skeleton.add_bone(back_right_leg)

    # Tail
    tail = Bone("tail", parent_name="body",
               local_transform=Transform(py=-0.5, pz=-0.3, rx=-0.5))
    skeleton.add_bone(tail)

    return skeleton


def create_idle_animation(skeleton: Skeleton) -> AnimationClip:
    """Create an idle animation with breathing and floating."""
    clip = AnimationClip(name="idle", duration=4.0, loop=True)

    # Breathing for body
    for t in [0.0, 1.0, 2.0, 3.0, 4.0]:
        breath_scale = 1.0 + math.sin(t * 1.57) * 0.03
        clip.add_keyframe("body", Keyframe(
            time=t,
            transform=Transform(sy=1.2 * breath_scale),
            interpolation=InterpolationType.LINEAR
        ))

    # Floating for root
    for t in [0.0, 1.0, 2.0, 3.0, 4.0]:
        float_offset = math.sin(t * 1.57) * 0.05
        clip.add_keyframe("root", Keyframe(
            time=t,
            transform=Transform(py=-0.5 + float_offset),
            interpolation=InterpolationType.LINEAR
        ))

    # Ear wiggle
    for t in [0.0, 0.5, 1.0, 1.5, 2.0]:
        ear_angle = math.sin(t * 3.14) * 0.1
        clip.add_keyframe("ear_left", Keyframe(
            time=t,
            transform=Transform(px=-0.3, py=0.5, pz=0.2, rz=-0.3 + ear_angle),
            interpolation=InterpolationType.LINEAR
        ))
        clip.add_keyframe("ear_right", Keyframe(
            time=t,
            transform=Transform(px=0.3, py=0.5, pz=0.2, rz=0.3 - ear_angle),
            interpolation=InterpolationType.LINEAR
        ))

    return clip


def create_walk_animation(skeleton: Skeleton) -> AnimationClip:
    """Create a walking animation."""
    clip = AnimationClip(name="walk", duration=1.0, loop=True)

    # Leg movement
    for i, t in enumerate([i / 8.0 for i in range(9)]):
        # Front left and back right move together
        leg_angle = math.sin(t * 6.28) * 0.3
        clip.add_keyframe("leg_front_left", Keyframe(
            time=t,
            transform=Transform(px=-0.3, py=-0.8, pz=0.2, rx=leg_angle),
            interpolation=InterpolationType.LINEAR
        ))
        clip.add_keyframe("leg_back_right", Keyframe(
            time=t,
            transform=Transform(px=0.3, py=-0.8, pz=-0.2, rx=leg_angle),
            interpolation=InterpolationType.LINEAR
        ))

        # Front right and back left opposite
        clip.add_keyframe("leg_front_right", Keyframe(
            time=t,
            transform=Transform(px=0.3, py=-0.8, pz=0.2, rx=-leg_angle),
            interpolation=InterpolationType.LINEAR
        ))
        clip.add_keyframe("leg_back_left", Keyframe(
            time=t,
            transform=Transform(px=-0.3, py=-0.8, pz=-0.2, rx=-leg_angle),
            interpolation=InterpolationType.LINEAR
        ))

        # Body bob
        bob = math.sin(t * 6.28 * 2) * 0.05
        clip.add_keyframe("body", Keyframe(
            time=t,
            transform=Transform(py=0.5 + bob, sy=1.2),
            interpolation=InterpolationType.LINEAR
        ))

    return clip


if __name__ == "__main__":
    # Test skeletal animation
    print("Testing Skeletal Animation System")

    skeleton = create_pet_skeleton()
    print(f"Created skeleton with {len(skeleton.bones)} bones")

    # Add animations
    idle = create_idle_animation(skeleton)
    walk = create_walk_animation(skeleton)

    skeleton.add_animation(idle)
    skeleton.add_animation(walk)

    print(f"Added animations: {list(skeleton.animations.keys())}")

    # Test animation playback
    skeleton.play_animation("idle")
    for _ in range(10):
        skeleton.update(0.1)
        transforms = skeleton.get_bone_transforms()
        # print(f"Time: {skeleton.animation_time:.1f}, Body transform: {transforms.get('body', 'N/A')[:4]}")

    print("Skeletal animation test passed!")
