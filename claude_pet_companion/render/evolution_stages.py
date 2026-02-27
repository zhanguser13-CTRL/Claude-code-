#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evolution Stages Visual Configuration

Defines the visual appearance for each of the 10 evolution stages.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum


class EvolutionStage(Enum):
    """10个进化阶段"""
    EGG = 0
    HATCHLING = 1
    BABY = 2
    CHILD = 3
    PRE_TEEN = 4
    TEEN = 5
    YOUNG_ADULT = 6
    ADULT = 7
    ELDER = 8
    ANCIENT = 9


@dataclass
class StageVisuals:
    """单个进化阶段的视觉配置"""
    stage_id: int
    name: str
    name_cn: str

    # 等级要求
    min_level: int

    # 身体尺寸 (相对基准尺寸的倍数)
    head_size: Tuple[float, float]    # (width, height) 倍数
    body_size: Tuple[float, float]    # (width, height) 倍数
    ear_size: Tuple[float, float]     # (width, height) 倍数
    tail_length: float                # 尾巴长度倍数

    # 动画参数
    float_amplitude: float            # 浮动幅度
    float_speed: float                # 浮动速度
    breathing_intensity: float        # 呼吸强度
    breathing_speed: float            # 呼吸速度

    # 特效开关
    has_antenna: bool                 # 是否有天线
    has_ears: bool                    # 是否有耳朵
    has_tail: bool                    # 是否有尾巴
    has_shadow: bool                  # 是否有阴影
    has_glow: bool                    # 是否有发光

    # 粒子效果
    particle_types: List[str]         # 可用的粒子类型

    # 解锁的配饰
    accessories: List[str]            # 该阶段解锁的配饰

    # 特殊能力
    abilities: List[str]              # 解锁的能力

    # 表情支持
    supported_expressions: List[str]  # 支持的表情

    # 3D深度效果
    depth_layers: int                 # 深度层数
    shadow_intensity: float           # 阴影强度
    highlight_intensity: float        # 高光强度

    # 进化特效
    evolution_effect: str             # 进化时的特效类型


# 10个阶段的详细配置
STAGE_VISUALS: Dict[int, StageVisuals] = {
    0: StageVisuals(
        stage_id=0,
        name="Egg",
        name_cn="蛋",
        min_level=0,
        head_size=(0.8, 1.0),
        body_size=(0.8, 1.0),
        ear_size=(0.0, 0.0),
        tail_length=0.0,
        float_amplitude=2.0,
        float_speed=0.05,
        breathing_intensity=0.02,
        breathing_speed=0.03,
        has_antenna=False,
        has_ears=False,
        has_tail=False,
        has_shadow=True,
        has_glow=True,
        particle_types=["sparkle"],
        accessories=[],
        abilities=["hatch"],
        supported_expressions=["idle", "sleep"],
        depth_layers=3,
        shadow_intensity=0.3,
        highlight_intensity=0.5,
        evolution_effect="crack_open"
    ),

    1: StageVisuals(
        stage_id=1,
        name="Hatchling",
        name_cn="破壳",
        min_level=1,
        head_size=(0.9, 0.9),
        body_size=(0.7, 0.8),
        ear_size=(0.5, 0.6),
        tail_length=0.2,
        float_amplitude=2.5,
        float_speed=0.06,
        breathing_intensity=0.03,
        breathing_speed=0.04,
        has_antenna=False,
        has_ears=True,
        has_tail=True,
        has_shadow=True,
        has_glow=True,
        particle_types=["sparkle", "star"],
        accessories=["shell_helmet"],
        abilities=["basic_emotions", "wobble"],
        supported_expressions=["happy", "surprised", "sleep"],
        depth_layers=4,
        shadow_intensity=0.4,
        highlight_intensity=0.6,
        evolution_effect="shell_break"
    ),

    2: StageVisuals(
        stage_id=2,
        name="Baby",
        name_cn="幼体",
        min_level=4,
        head_size=(1.0, 1.0),
        body_size=(0.85, 0.9),
        ear_size=(0.7, 0.8),
        tail_length=0.4,
        float_amplitude=3.0,
        float_speed=0.07,
        breathing_intensity=0.04,
        breathing_speed=0.05,
        has_antenna=False,
        has_ears=True,
        has_tail=True,
        has_shadow=True,
        has_glow=True,
        particle_types=["sparkle", "star", "heart"],
        accessories=["tiny_antenna"],
        abilities=["basic_emotions", "wobble", "tumble"],
        supported_expressions=["happy", "surprised", "sleep", "confused"],
        depth_layers=5,
        shadow_intensity=0.4,
        highlight_intensity=0.6,
        evolution_effect="grow_spurt"
    ),

    3: StageVisuals(
        stage_id=3,
        name="Child",
        name_cn="儿童",
        min_level=8,
        head_size=(1.0, 1.0),
        body_size=(0.9, 0.95),
        ear_size=(0.8, 0.9),
        tail_length=0.6,
        float_amplitude=3.5,
        float_speed=0.08,
        breathing_intensity=0.05,
        breathing_speed=0.05,
        has_antenna=True,
        has_ears=True,
        has_tail=True,
        has_shadow=True,
        has_glow=True,
        particle_types=["sparkle", "star", "heart", "plus"],
        accessories=["tiny_antenna", "wrist_band"],
        abilities=["basic_emotions", "particle_effects", "jump"],
        supported_expressions=["happy", "surprised", "sleep", "confused", "excited"],
        depth_layers=5,
        shadow_intensity=0.5,
        highlight_intensity=0.7,
        evolution_effect="energy_surge"
    ),

    4: StageVisuals(
        stage_id=4,
        name="Pre-Teen",
        name_cn="预备少年",
        min_level=13,
        head_size=(1.0, 1.0),
        body_size=(0.95, 1.0),
        ear_size=(0.9, 0.95),
        tail_length=0.7,
        float_amplitude=3.0,
        float_speed=0.08,
        breathing_intensity=0.04,
        breathing_speed=0.05,
        has_antenna=True,
        has_ears=True,
        has_tail=True,
        has_shadow=True,
        has_glow=True,
        particle_types=["sparkle", "star", "heart", "plus", "note"],
        accessories=["tiny_antenna", "wrist_band", "shoulder_pad"],
        abilities=["basic_emotions", "particle_effects", "speech_bubbles", "jump"],
        supported_expressions=["happy", "surprised", "sleep", "confused", "excited", "proud"],
        depth_layers=6,
        shadow_intensity=0.5,
        highlight_intensity=0.7,
        evolution_effect="adolescent_spike"
    ),

    5: StageVisuals(
        stage_id=5,
        name="Teen",
        name_cn="少年",
        min_level=19,
        head_size=(1.0, 1.0),
        body_size=(1.0, 1.05),
        ear_size=(1.0, 1.0),
        tail_length=0.8,
        float_amplitude=4.0,
        float_speed=0.09,
        breathing_intensity=0.05,
        breathing_speed=0.06,
        has_antenna=True,
        has_ears=True,
        has_tail=True,
        has_shadow=True,
        has_glow=True,
        particle_types=["sparkle", "star", "heart", "plus", "note", "code"],
        accessories=["tiny_antenna", "wrist_band", "shoulder_pad", "path_specific"],
        abilities=["basic_emotions", "particle_effects", "speech_bubbles", "double_xp", "dash"],
        supported_expressions=["happy", "surprised", "sleep", "confused", "excited", "proud", "love"],
        depth_layers=6,
        shadow_intensity=0.5,
        highlight_intensity=0.8,
        evolution_effect="growth_burst"
    ),

    6: StageVisuals(
        stage_id=6,
        name="Young Adult",
        name_cn="青年",
        min_level=26,
        head_size=(1.0, 1.0),
        body_size=(1.05, 1.1),
        ear_size=(1.0, 1.0),
        tail_length=0.9,
        float_amplitude=3.5,
        float_speed=0.08,
        breathing_intensity=0.04,
        breathing_speed=0.05,
        has_antenna=True,
        has_ears=True,
        has_tail=True,
        has_shadow=True,
        has_glow=True,
        particle_types=["sparkle", "star", "heart", "plus", "note", "code", "fire"],
        accessories=["tiny_antenna", "wrist_band", "shoulder_pad", "path_specific", "cape"],
        abilities=["basic_emotions", "particle_effects", "speech_bubbles", "double_xp", "dash", "focus_mode"],
        supported_expressions=["happy", "surprised", "sleep", "confused", "excited", "proud", "love", "thinking"],
        depth_layers=7,
        shadow_intensity=0.6,
        highlight_intensity=0.8,
        evolution_effect="mature_glow"
    ),

    7: StageVisuals(
        stage_id=7,
        name="Adult",
        name_cn="成年",
        min_level=36,
        head_size=(1.0, 1.0),
        body_size=(1.1, 1.15),
        ear_size=(1.0, 1.0),
        tail_length=1.0,
        float_amplitude=3.0,
        float_speed=0.07,
        breathing_intensity=0.03,
        breathing_speed=0.04,
        has_antenna=True,
        has_ears=True,
        has_tail=True,
        has_shadow=True,
        has_glow=True,
        particle_types=["sparkle", "star", "heart", "plus", "note", "code", "fire", "energy"],
        accessories=["tiny_antenna", "wrist_band", "shoulder_pad", "path_specific", "cape", "aura"],
        abilities=["basic_emotions", "particle_effects", "speech_bubbles", "double_xp", "dash", "focus_mode", "mentor_mode"],
        supported_expressions=["happy", "surprised", "sleep", "confused", "excited", "proud", "love", "thinking", "determined"],
        depth_layers=8,
        shadow_intensity=0.6,
        highlight_intensity=0.9,
        evolution_effect="power_ascension"
    ),

    8: StageVisuals(
        stage_id=8,
        name="Elder",
        name_cn="长者",
        min_level=51,
        head_size=(1.05, 1.05),
        body_size=(1.15, 1.2),
        ear_size=(1.0, 1.0),
        tail_length=1.1,
        float_amplitude=2.5,
        float_speed=0.06,
        breathing_intensity=0.02,
        breathing_speed=0.03,
        has_antenna=True,
        has_ears=True,
        has_tail=True,
        has_shadow=True,
        has_glow=True,
        particle_types=["sparkle", "star", "heart", "plus", "note", "code", "fire", "energy", "wisdom"],
        accessories=["tiny_antenna", "wrist_band", "shoulder_pad", "path_specific", "cape", "aura", "crown"],
        abilities=["basic_emotions", "particle_effects", "speech_bubbles", "double_xp", "dash", "focus_mode", "mentor_mode", "wisdom_boost"],
        supported_expressions=["happy", "surprised", "sleep", "confused", "excited", "proud", "love", "thinking", "determined", "wise"],
        depth_layers=9,
        shadow_intensity=0.7,
        highlight_intensity=1.0,
        evolution_effect="enlightenment"
    ),

    9: StageVisuals(
        stage_id=9,
        name="Ancient",
        name_cn="远古",
        min_level=71,
        head_size=(1.1, 1.1),
        body_size=(1.25, 1.3),
        ear_size=(1.1, 1.1),
        tail_length=1.3,
        float_amplitude=2.0,
        float_speed=0.04,
        breathing_intensity=0.02,
        breathing_speed=0.02,
        has_antenna=True,
        has_ears=True,
        has_tail=True,
        has_shadow=True,
        has_glow=True,
        particle_types=["sparkle", "star", "heart", "plus", "note", "code", "fire", "energy", "wisdom", "cosmic"],
        accessories=["tiny_antenna", "wrist_band", "shoulder_pad", "path_specific", "cape", "aura", "crown", "wings", "halo"],
        abilities=["basic_emotions", "particle_effects", "speech_bubbles", "double_xp", "dash", "focus_mode", "mentor_mode", "wisdom_boost", "legendary_aura", "time_warp"],
        supported_expressions=["happy", "surprised", "sleep", "confused", "excited", "proud", "love", "thinking", "determined", "wise", "transcendent"],
        depth_layers=10,
        shadow_intensity=0.8,
        highlight_intensity=1.2,
        evolution_effect="ascension"
    ),
}


# 等级要求映射
LEVEL_REQUIREMENTS = {
    0: 0,      # Egg
    1: 1,      # Hatchling
    2: 4,      # Baby
    3: 8,      # Child
    4: 13,     # Pre-Teen
    5: 19,     # Teen
    6: 26,     # Young Adult
    7: 36,     # Adult
    8: 51,     # Elder
    9: 71,     # Ancient
}


def get_stage_visuals(stage_id: int) -> StageVisuals:
    """获取指定阶段的视觉配置"""
    return STAGE_VISUALS.get(stage_id, STAGE_VISUALS[0])


def get_stage_for_level(level: int) -> int:
    """根据等级获取应该所处的阶段"""
    for stage_id in sorted(LEVEL_REQUIREMENTS.keys(), reverse=True):
        if level >= LEVEL_REQUIREMENTS[stage_id]:
            return stage_id
    return 0


def can_evolve_to(current_stage: int, target_level: int) -> bool:
    """检查是否可以进化到下一阶段"""
    if current_stage >= 9:
        return False
    next_stage = current_stage + 1
    required_level = LEVEL_REQUIREMENTS.get(next_stage, 999)
    return target_level >= required_level


def get_next_stage(current_stage: int) -> Optional[StageVisuals]:
    """获取下一阶段的配置"""
    if current_stage >= 9:
        return None
    return get_stage_visuals(current_stage + 1)


def get_stage_name(stage_id: int) -> str:
    """获取阶段名称"""
    visuals = get_stage_visuals(stage_id)
    return f"{visuals.name} ({visuals.name_cn})"


def get_all_stage_names() -> Dict[int, str]:
    """获取所有阶段名称"""
    return {stage_id: f"{v.name} ({v.name_cn})" for stage_id, v in STAGE_VISUALS.items()}


# 进化动画配置
EVOLUTION_ANIMATION_CONFIG = {
    "duration_ms": 3000,
    "phases": [
        {"time": 0, "effect": "screen_flash", "color": "white", "duration": 100},
        {"time": 100, "effect": "pet_glow", "intensity": 1.0},
        {"time": 500, "effect": "spiral_particles", "count": 20},
        {"time": 1000, "effect": "body_morph", "easing": "easeInOut"},
        {"time": 2000, "effect": "burst", "particle_type": "star"},
        {"time": 2500, "effect": "new_form_reveal"},
        {"time": 3000, "effect": "celebration", "duration": 2000}
    ],
    "sounds": {
        "start": "evolution_start.mp3",
        "mid": "evolution_mid.mp3",
        "end": "evolution_end.mp3"
    }
}


if __name__ == "__main__":
    # 测试阶段系统
    print("=== 10个进化阶段 ===")
    for stage_id in sorted(STAGE_VISUALS.keys()):
        visuals = STAGE_VISUALS[stage_id]
        print(f"阶段 {stage_id}: {visuals.name} ({visuals.name_cn}) - 需要等级 {visuals.min_level}")
        print(f"  尺寸: 头{visuals.head_size} 身{visuals.body_size}")
        print(f"  能力: {', '.join(visuals.abilities[:3])}{'...' if len(visuals.abilities) > 3 else ''}")
        print()

    # 测试等级到阶段映射
    print("=== 等级到阶段映射 ===")
    for level in [0, 1, 5, 10, 20, 30, 40, 60, 80]:
        stage = get_stage_for_level(level)
        print(f"等级 {level} -> 阶段 {stage}: {get_stage_name(stage)}")
