#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evolution Paths Visual Configuration

Defines the visual appearance for each evolution path.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class AnimationStyle(Enum):
    """动画风格"""
    BOUNCY = "bouncy"      # 弹跳风格
    SMOOTH = "smooth"      # 平滑风格
    SHARP = "sharp"        # 锐利风格
    FLOATING = "floating"  # 漂浮风格


@dataclass
class EvolutionPathVisuals:
    """单条进化路径的完整视觉配置"""
    path_id: str
    name: str
    description: str

    # 基础颜色方案
    primary_base: str       # 主色（身体基色）
    primary_highlight: str  # 主色高光
    primary_shadow: str     # 主色阴影
    secondary_base: str     # 副色（耳朵、尾巴等）
    accent_color: str       # 强调色（眼睛、配饰）
    glow_color: str         # 发光色
    belly_color: str        # 肚皮颜色

    # 身体特征
    body_shape: str         # "round", "oval", "slender", "bulky"
    ear_type: str           # "round", "pointed", "long", "none"
    tail_type: str          # "none", "short", "long", "flowing"
    eye_style: str          # "round", "pixel", "sharp", "gentle"

    # 配饰（按阶段解锁）
    stage_accessories: Dict[int, List[str]] = field(default_factory=dict)

    # 粒子效果
    particle_types: List[str] = field(default_factory=list)

    # 动画风格
    animation_style: str = AnimationStyle.SMOOTH.value

    # 特殊效果
    special_effects: List[str] = field(default_factory=list)

    # 身体比例系数
    scale_head: float = 1.0
    scale_body: float = 1.0
    scale_ears: float = 1.0
    scale_tail: float = 1.0


# 五条路径的完整配置
EVOLUTION_PATHS: Dict[str, EvolutionPathVisuals] = {
    "coder": EvolutionPathVisuals(
        path_id="coder",
        name="代码师",
        description="精通代码之道，科技风格",
        # 蓝色科技风格
        primary_base="#1e40af",
        primary_highlight="#3b82f6",
        primary_shadow="#1e3a8a",
        secondary_base="#0891b2",
        accent_color="#22c55e",
        glow_color="#60a5fa",
        belly_color="#dbeafe",
        body_shape="slender",
        ear_type="pointed",
        tail_type="flowing",
        eye_style="pixel",
        stage_accessories={
            1: ["tiny_antenna"],
            3: ["data_goggles"],
            5: ["keyboard_cape"],
            7: ["circuit_aura"],
            9: ["halo_code"]
        },
        particle_types=["binary", "bracket", "semicolon"],
        animation_style=AnimationStyle.SMOOTH.value,
        special_effects=["data_stream", "glitch"],
        scale_head=0.95,
        scale_body=1.0,
        scale_ears=1.1,
        scale_tail=1.2
    ),

    "warrior": EvolutionPathVisuals(
        path_id="warrior",
        name="战士",
        description="Bug克星，战斗风格",
        # 橙红战斗风格
        primary_base="#c2410c",
        primary_highlight="#f97316",
        primary_shadow="#9a3412",
        secondary_base="#dc2626",
        accent_color="#fbbf24",
        glow_color="#fb923c",
        belly_color="#ffedd5",
        body_shape="bulky",
        ear_type="long",
        tail_type="short",
        eye_style="sharp",
        stage_accessories={
            1: ["bandana"],
            3: ["mini_shield"],
            5: ["sword_antenna"],
            7: ["flame_aura"],
            9: ["halo_fire"]
        },
        particle_types=["spark", "slash", "impact"],
        animation_style=AnimationStyle.SHARP.value,
        special_effects=["ember_trail", "shockwave"],
        scale_head=1.0,
        scale_body=1.15,
        scale_ears=0.9,
        scale_tail=0.8
    ),

    "social": EvolutionPathVisuals(
        path_id="social",
        name="社交达人",
        description="温暖友好，可爱风格",
        # 粉色可爱风格
        primary_base="#db2777",
        primary_highlight="#f472b6",
        primary_shadow="#be185d",
        secondary_base="#f9a8d4",
        accent_color="#fb7185",
        glow_color="#fda4af",
        belly_color="#fce7f3",
        body_shape="round",
        ear_type="round",
        tail_type="long",
        eye_style="round",
        stage_accessories={
            1: ["bow"],
            3: ["heart_charm"],
            5: ["ribbon_cape"],
            7: ["love_aura"],
            9: ["halo_heart"]
        },
        particle_types=["heart", "star", "sparkle"],
        animation_style=AnimationStyle.BOUNCY.value,
        special_effects=["sparkle_trail", "kawaii_pop"],
        scale_head=1.1,
        scale_body=0.95,
        scale_ears=1.0,
        scale_tail=1.1
    ),

    "night_owl": EvolutionPathVisuals(
        path_id="night_owl",
        name="夜猫",
        description="深夜编程者，神秘风格",
        # 紫色神秘风格
        primary_base="#5b21b6",
        primary_highlight="#8b5cf6",
        primary_shadow="#4c1d95",
        secondary_base="#6d28d9",
        accent_color="#fbbf24",
        glow_color="#a78bfa",
        belly_color="#ede9fe",
        body_shape="slender",
        ear_type="long",
        tail_type="flowing",
        eye_style="sharp",
        stage_accessories={
            1: ["moon_charm"],
            3: ["star_antenna"],
            5: ["night_cape"],
            7: ["cosmic_aura"],
            9: ["halo_moon"]
        },
        particle_types=["star", "moon", "dust"],
        animation_style=AnimationStyle.FLOATING.value,
        special_effects=["stardust_trail", "phase_shift"],
        scale_head=0.95,
        scale_body=1.05,
        scale_ears=1.15,
        scale_tail=1.3
    ),

    "balanced": EvolutionPathVisuals(
        path_id="balanced",
        name="平衡者",
        description="全面发展，和谐风格",
        # 青绿和谐风格
        primary_base="#059669",
        primary_highlight="#10b981",
        primary_shadow="#047857",
        secondary_base="#14b8a6",
        accent_color="#34d399",
        glow_color="#6ee7b7",
        belly_color="#d1fae5",
        body_shape="oval",
        ear_type="pointed",
        tail_type="long",
        eye_style="gentle",
        stage_accessories={
            1: ["leaf_mark"],
            3: ["balance_charm"],
            5: ["nature_cape"],
            7: ["harmony_aura"],
            9: ["halo_balance"]
        },
        particle_types=["leaf", "drop", "light"],
        animation_style=AnimationStyle.SMOOTH.value,
        special_effects=["nature_aura", "balance_glow"],
        scale_head=1.0,
        scale_body=1.0,
        scale_ears=1.0,
        scale_tail=1.0
    )
}


def get_path_visuals(path_id: str) -> EvolutionPathVisuals:
    """获取指定路径的视觉配置"""
    return EVOLUTION_PATHS.get(path_id, EVOLUTION_PATHS["balanced"])


def get_all_paths() -> List[str]:
    """获取所有路径ID"""
    return list(EVOLUTION_PATHS.keys())


def determine_evolution_path(stats: Dict[str, int]) -> str:
    """根据统计数据确定进化路径"""
    scores = {
        "coder": stats.get("files_created", 0) * 2 + stats.get("files_modified", 0),
        "warrior": stats.get("errors_fixed", 0) * 3,
        "social": stats.get("interactions", 0) * 2,
        "night_owl": stats.get("night_hours", 0) * 5,
    }

    # 平衡路径的分数是所有活动的平均值
    total_activity = sum(scores.values())
    scores["balanced"] = total_activity * 0.3

    return max(scores.keys(), key=lambda k: scores[k])


# 配饰渲染配置
ACCESSORY_RENDER_CONFIG = {
    # Coder path accessories
    "tiny_antenna": {
        "type": "antenna",
        "color": "#22c55e",
        "size": 5
    },
    "data_goggles": {
        "type": "goggles",
        "color": "#0891b2",
        "size": 15
    },
    "keyboard_cape": {
        "type": "cape",
        "color": "#1e40af",
        "pattern": "keyboard"
    },
    "circuit_aura": {
        "type": "aura",
        "color": "#60a5fa",
        "pattern": "circuit"
    },
    "halo_code": {
        "type": "halo",
        "color": "#22c55e",
        "symbol": "</>"
    },

    # Warrior path accessories
    "bandana": {
        "type": "headband",
        "color": "#dc2626"
    },
    "mini_shield": {
        "type": "shield",
        "color": "#fbbf24",
        "size": 12
    },
    "sword_antenna": {
        "type": "antenna",
        "color": "#f97316",
        "shape": "sword"
    },
    "flame_aura": {
        "type": "aura",
        "color": "#fb923c",
        "pattern": "flame"
    },
    "halo_fire": {
        "type": "halo",
        "color": "#fbbf24",
        "symbol": "🔥"
    },

    # Social path accessories
    "bow": {
        "type": "bow",
        "color": "#f472b6"
    },
    "heart_charm": {
        "type": "charm",
        "color": "#fb7185",
        "shape": "heart"
    },
    "ribbon_cape": {
        "type": "cape",
        "color": "#db2777",
        "pattern": "ribbon"
    },
    "love_aura": {
        "type": "aura",
        "color": "#fda4af",
        "pattern": "hearts"
    },
    "halo_heart": {
        "type": "halo",
        "color": "#fb7185",
        "symbol": "♥"
    },

    # Night Owl path accessories
    "moon_charm": {
        "type": "charm",
        "color": "#fbbf24",
        "shape": "moon"
    },
    "star_antenna": {
        "type": "antenna",
        "color": "#fbbf24",
        "shape": "star"
    },
    "night_cape": {
        "type": "cape",
        "color": "#5b21b6",
        "pattern": "stars"
    },
    "cosmic_aura": {
        "type": "aura",
        "color": "#a78bfa",
        "pattern": "cosmic"
    },
    "halo_moon": {
        "type": "halo",
        "color": "#fbbf24",
        "symbol": "🌙"
    },

    # Balanced path accessories
    "leaf_mark": {
        "type": "mark",
        "color": "#34d399",
        "shape": "leaf"
    },
    "balance_charm": {
        "type": "charm",
        "color": "#10b981",
        "shape": "yin_yang"
    },
    "nature_cape": {
        "type": "cape",
        "color": "#059669",
        "pattern": "leaves"
    },
    "harmony_aura": {
        "type": "aura",
        "color": "#6ee7b7",
        "pattern": "harmony"
    },
    "halo_balance": {
        "type": "halo",
        "color": "#34d399",
        "symbol": "☯"
    },
}


def get_accessory_config(accessory_id: str) -> Optional[Dict]:
    """获取配饰渲染配置"""
    return ACCESSORY_RENDER_CONFIG.get(accessory_id)


if __name__ == "__main__":
    # 测试路径系统
    for path_id, visuals in EVOLUTION_PATHS.items():
        print(f"{path_id}: {visuals.name} - {visuals.description}")
        print(f"  颜色: {visuals.primary_base}, {visuals.accent_color}")
        print(f"  特效: {', '.join(visuals.special_effects)}")
        print()

    # 测试路径确定
    test_stats = {
        "files_created": 20,
        "files_modified": 30,
        "errors_fixed": 5,
        "interactions": 10,
        "night_hours": 2
    }
    determined = determine_evolution_path(test_stats)
    print(f"根据统计确定的路径: {determined}")
