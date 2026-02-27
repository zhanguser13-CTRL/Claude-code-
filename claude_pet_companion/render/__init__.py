#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3D Rendering System for Claude Pet Companion

This module provides pseudo-3D layered rendering for the pet using tkinter.
"""

from .renderer_3d import Renderer3D
from .body_parts import BodyPart, BodyPartsManager
from .evolution_stages import StageVisuals, get_stage_visuals
from .evolution_paths import EvolutionPathVisuals, get_path_visuals
from .lighting import LightingSystem, LightingPreset
from .animations import AnimationManager, EvolutionAnimation
from .animation_library import (
    AnimationType,
    Easing,
    Animation,
    AnimationBuilder,
    AnimationLibrary,
    get_animation_library,
)

__all__ = [
    'Renderer3D',
    'BodyPart',
    'BodyPartsManager',
    'StageVisuals',
    'get_stage_visuals',
    'EvolutionPathVisuals',
    'get_path_visuals',
    'LightingSystem',
    'LightingPreset',
    'AnimationManager',
    'EvolutionAnimation',
    'AnimationType',
    'Easing',
    'Animation',
    'AnimationBuilder',
    'AnimationLibrary',
    'get_animation_library',
]
