#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lighting System for Claude Pet

Provides dynamic lighting based on time of day and pet status.
"""
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional, List
from enum import Enum
from datetime import datetime, time
import math


class TimeOfDay(Enum):
    """一天中的时段"""
    DAWN = "dawn"           # 黎明 (5-7)
    MORNING = "morning"     # 早晨 (7-11)
    NOON = "noon"           # 正午 (11-14)
    AFTERNOON = "afternoon" # 下午 (14-17)
    EVENING = "evening"     # 傍晚 (17-20)
    NIGHT = "night"         # 夜晚 (20-5)
    MIDNIGHT = "midnight"   # 午夜 (0-2)


class StatusLighting(Enum):
    """状态灯光"""
    CODING = "coding"       # 编程中
    WORKING = "working"     # 工作中
    THINKING = "thinking"   # 思考中
    ERROR = "error"         # 错误
    SUCCESS = "success"     # 成功
    IDLE = "idle"           # 空闲
    SLEEPING = "sleeping"   # 睡眠


@dataclass
class LightingPreset:
    """光照预设"""
    name: str

    # 环境光 RGB (0-2, 1为正常)
    ambient_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)

    # 阴影强度 (0-1)
    shadow_intensity: float = 0.4

    # 高光强度 (0-1)
    highlight_intensity: float = 0.8

    # 发光强度 (0-2)
    glow_intensity: float = 1.0

    # 光源方向 (角度，0=从上方)
    light_direction: float = 45

    # 颜色叠加
    color_overlay: Optional[Tuple[int, int, int]] = None

    # 特效
    special_effects: List[str] = field(default_factory=list)


# 时间光照预设
TIME_LIGHTING_PRESETS: Dict[TimeOfDay, LightingPreset] = {
    TimeOfDay.DAWN: LightingPreset(
        name="dawn",
        ambient_color=(1.1, 0.95, 0.9),    # 暖橙色调
        shadow_intensity=0.3,
        highlight_intensity=0.7,
        glow_intensity=1.2,
        light_direction=30,
        color_overlay=(255, 200, 150),
        special_effects=["warm_glow", "dawn_mist"]
    ),

    TimeOfDay.MORNING: LightingPreset(
        name="morning",
        ambient_color=(1.2, 1.1, 0.95),    # 明亮暖色
        shadow_intensity=0.3,
        highlight_intensity=0.8,
        glow_intensity=1.0,
        light_direction=45,
        color_overlay=(255, 240, 200),
        special_effects=["morning_rays"]
    ),

    TimeOfDay.NOON: LightingPreset(
        name="noon",
        ambient_color=(1.0, 1.0, 1.0),     # 中性明亮
        shadow_intensity=0.4,
        highlight_intensity=1.0,
        glow_intensity=0.8,
        light_direction=90,
        special_effects=["bright_light"]
    ),

    TimeOfDay.AFTERNOON: LightingPreset(
        name="afternoon",
        ambient_color=(1.0, 0.95, 0.9),    # 略暖
        shadow_intensity=0.45,
        highlight_intensity=0.9,
        glow_intensity=0.9,
        light_direction=120,
        color_overlay=(255, 230, 200),
        special_effects=["afternoon_warmth"]
    ),

    TimeOfDay.EVENING: LightingPreset(
        name="evening",
        ambient_color=(0.9, 0.85, 1.0),    # 冷色调
        shadow_intensity=0.5,
        highlight_intensity=0.6,
        glow_intensity=1.2,
        light_direction=150,
        color_overlay=(200, 200, 255),
        special_effects=["evening_calm"]
    ),

    TimeOfDay.NIGHT: LightingPreset(
        name="night",
        ambient_color=(0.6, 0.6, 0.8),     # 暗蓝
        shadow_intensity=0.7,
        highlight_intensity=0.4,
        glow_intensity=1.5,                # 夜晚发光增强
        light_direction=180,
        color_overlay=(100, 100, 150),
        special_effects=["night_glow", "star_twinkle"]
    ),

    TimeOfDay.MIDNIGHT: LightingPreset(
        name="midnight",
        ambient_color=(0.4, 0.4, 0.7),     # 深蓝
        shadow_intensity=0.8,
        highlight_intensity=0.3,
        glow_intensity=2.0,                # 午夜最强发光
        light_direction=180,
        color_overlay=(80, 80, 150),
        special_effects=["midnight_aura", "dream_particles"]
    ),
}


# 状态光照预设
STATUS_LIGHTING_PRESETS: Dict[StatusLighting, LightingPreset] = {
    StatusLighting.CODING: LightingPreset(
        name="coding",
        ambient_color=(0.8, 1.0, 0.9),     # 绿色调
        shadow_intensity=0.4,
        highlight_intensity=0.9,
        glow_intensity=1.2,
        light_direction=60,
        special_effects=["code_particles", "focus_glow"]
    ),

    StatusLighting.WORKING: LightingPreset(
        name="working",
        ambient_color=(0.9, 0.95, 1.0),    # 蓝白色
        shadow_intensity=0.4,
        highlight_intensity=1.0,
        glow_intensity=1.1,
        light_direction=45,
        special_effects=["work_aura"]
    ),

    StatusLighting.THINKING: LightingPreset(
        name="thinking",
        ambient_color=(1.0, 0.9, 0.7),     # 黄色调
        shadow_intensity=0.35,
        highlight_intensity=0.8,
        glow_intensity=1.3,
        light_direction=30,
        special_effects=["thought_bubbles", "wonder_glow"]
    ),

    StatusLighting.ERROR: LightingPreset(
        name="error",
        ambient_color=(1.0, 0.6, 0.6),     # 红色调
        shadow_intensity=0.6,
        highlight_intensity=0.5,
        glow_intensity=1.5,
        light_direction=45,
        color_overlay=(255, 100, 100),
        special_effects=["error_shake", "alert_glow"]
    ),

    StatusLighting.SUCCESS: LightingPreset(
        name="success",
        ambient_color=(1.0, 1.0, 0.7),     # 金色调
        shadow_intensity=0.3,
        highlight_intensity=1.2,
        glow_intensity=1.8,
        light_direction=60,
        color_overlay=(255, 255, 150),
        special_effects=["success_sparkles", "achievement_glow"]
    ),

    StatusLighting.IDLE: LightingPreset(
        name="idle",
        ambient_color=(1.0, 1.0, 1.0),     # 默认
        shadow_intensity=0.4,
        highlight_intensity=0.8,
        glow_intensity=1.0,
        light_direction=45,
        special_effects=["gentle_breathing"]
    ),

    StatusLighting.SLEEPING: LightingPreset(
        name="sleeping",
        ambient_color=(0.5, 0.5, 0.7),     # 睡眠蓝
        shadow_intensity=0.5,
        highlight_intensity=0.3,
        glow_intensity=0.5,
        light_direction=180,
        color_overlay=(100, 100, 150),
        special_effects=["sleep_bubbles", "zzz_particles"]
    ),
}


class LightingSystem:
    """光照系统"""

    def __init__(self):
        self.current_preset = LightingPreset("default")
        self.time_preset = LightingPreset("time_default")
        self.status_preset = LightingPreset("status_default")

        # 过渡状态
        self.transition_progress = 1.0  # 0-1
        self.from_preset = None
        self.to_preset = None

    def get_time_of_day(self) -> TimeOfDay:
        """获取当前时段"""
        now = datetime.now()
        hour = now.hour

        if 5 <= hour < 7:
            return TimeOfDay.DAWN
        elif 7 <= hour < 11:
            return TimeOfDay.MORNING
        elif 11 <= hour < 14:
            return TimeOfDay.NOON
        elif 14 <= hour < 17:
            return TimeOfDay.AFTERNOON
        elif 17 <= hour < 20:
            return TimeOfDay.EVENING
        elif 20 <= hour < 24 or hour == 0:
            return TimeOfDay.NIGHT
        else:  # 0-2
            return TimeOfDay.MIDNIGHT

    def update_time_lighting(self):
        """更新时间光照"""
        time_of_day = self.get_time_of_day()
        self.time_preset = TIME_LIGHTING_PRESETS.get(time_of_day, TIME_LIGHTING_PRESETS[TimeOfDay.NOON])
        self._update_combined_preset()

    def set_status_lighting(self, status: StatusLighting):
        """设置状态光照"""
        self.status_preset = STATUS_LIGHTING_PRESETS.get(status, STATUS_LIGHTING_PRESETS[StatusLighting.IDLE])
        self._update_combined_preset()

    def _update_combined_preset(self):
        """合并时间和状态光照"""
        # 状态优先级高于时间
        combined = LightingPreset("combined")

        # 环境光相乘混合
        time_ambient = self.time_preset.ambient_color
        status_ambient = self.status_preset.ambient_color

        combined.ambient_color = (
            time_ambient[0] * status_ambient[0],
            time_ambient[1] * status_ambient[1],
            time_ambient[2] * status_ambient[2]
        )

        # 其他属性取平均值
        combined.shadow_intensity = (self.time_preset.shadow_intensity + self.status_preset.shadow_intensity) / 2
        combined.highlight_intensity = (self.time_preset.highlight_intensity + self.status_preset.highlight_intensity) / 2
        combined.glow_intensity = max(self.time_preset.glow_intensity, self.status_preset.glow_intensity)

        # 合并特效
        combined.special_effects = self.time_preset.special_effects + self.status_preset.special_effects

        # 如果状态有颜色叠加，优先使用
        combined.color_overlay = self.status_preset.color_overlay or self.time_preset.color_overlay

        self.current_preset = combined

    def transition_to(self, target_preset: LightingPreset, duration: float = 1.0):
        """过渡到新的光照预设"""
        self.from_preset = self.current_preset
        self.to_preset = target_preset
        self.transition_progress = 0

    def update_transition(self, dt: float):
        """更新过渡"""
        if self.transition_progress < 1.0:
            self.transition_progress += dt / 1.0  # 假设duration为1秒
            self.transition_progress = min(1.0, self.transition_progress)

            if self.from_preset and self.to_preset:
                t = self._ease_in_out(self.transition_progress)
                self.current_preset = self._lerp_preset(self.from_preset, self.to_preset, t)

    def _ease_in_out(self, t: float) -> float:
        """缓动函数"""
        return t * t * (3 - 2 * t)

    def _lerp_preset(self, from_p: LightingPreset, to_p: LightingPreset, t: float) -> LightingPreset:
        """在两个预设之间插值"""
        result = LightingPreset(f"lerp_{from_p.name}_to_{to_p.name}")

        result.ambient_color = (
            self._lerp(from_p.ambient_color[0], to_p.ambient_color[0], t),
            self._lerp(from_p.ambient_color[1], to_p.ambient_color[1], t),
            self._lerp(from_p.ambient_color[2], to_p.ambient_color[2], t),
        )
        result.shadow_intensity = self._lerp(from_p.shadow_intensity, to_p.shadow_intensity, t)
        result.highlight_intensity = self._lerp(from_p.highlight_intensity, to_p.highlight_intensity, t)
        result.glow_intensity = self._lerp(from_p.glow_intensity, to_p.glow_intensity, t)
        result.light_direction = self._lerp(from_p.light_direction, to_p.light_direction, t)

        return result

    def _lerp(self, a: float, b: float, t: float) -> float:
        """线性插值"""
        return a + (b - a) * t

    def apply_lighting_to_color(self, base_color: str) -> str:
        """应用光照到颜色"""
        # 解析基础颜色
        color = base_color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)

        # 应用环境光
        ambient = self.current_preset.ambient_color
        r = min(255, int(r * ambient[0]))
        g = min(255, int(g * ambient[1]))
        b = min(255, int(b * ambient[2]))

        # 应用颜色叠加
        if self.current_preset.color_overlay:
            overlay = self.current_preset.color_overlay
            r = min(255, int((r + overlay[0]) / 2))
            g = min(255, int((g + overlay[1]) / 2))
            b = min(255, int((b + overlay[2]) / 2))

        return f'#{r:02x}{g:02x}{b:02x}'

    def get_shadow_color(self, base_color: str) -> str:
        """获取阴影颜色"""
        intensity = self.current_preset.shadow_intensity
        return self._adjust_color_brightness(base_color, -int(100 * intensity))

    def get_highlight_color(self, base_color: str) -> str:
        """获取高光颜色"""
        intensity = self.current_preset.highlight_intensity
        return self._adjust_color_brightness(base_color, int(50 * intensity))

    def get_glow_color(self, base_color: str) -> str:
        """获取发光颜色"""
        intensity = self.current_preset.glow_intensity
        return self._adjust_color_brightness(base_color, int(30 * (intensity - 1)))

    def _adjust_color_brightness(self, color: str, amount: int) -> str:
        """调整颜色亮度"""
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)

        r = max(0, min(255, r + amount))
        g = max(0, min(255, g + amount))
        b = max(0, min(255, b + amount))

        return f'#{r:02x}{g:02x}{b:02x}'

    def has_effect(self, effect_name: str) -> bool:
        """检查是否有特定特效"""
        return effect_name in self.current_preset.special_effects

    def get_current_preset(self) -> LightingPreset:
        """获取当前光照预设"""
        return self.current_preset


def get_lighting_for_status(status: str) -> LightingPreset:
    """根据状态字符串获取光照"""
    status_map = {
        "thinking": StatusLighting.THINKING,
        "working": StatusLighting.WORKING,
        "coding": StatusLighting.CODING,
        "error": StatusLighting.ERROR,
        "success": StatusLighting.SUCCESS,
        "idle": StatusLighting.IDLE,
        "sleeping": StatusLighting.SLEEPING,
    }
    status_enum = status_map.get(status.lower(), StatusLighting.IDLE)
    return STATUS_LIGHTING_PRESETS.get(status_enum, STATUS_LIGHTING_PRESETS[StatusLighting.IDLE])


if __name__ == "__main__":
    # 测试光照系统
    lighting = LightingSystem()

    print("=== 时间光照测试 ===")
    for time_of_day, preset in TIME_LIGHTING_PRESETS.items():
        print(f"{time_of_day.value}:")
        print(f"  环境光: {preset.ambient_color}")
        print(f"  发光强度: {preset.glow_intensity}")
        print(f"  特效: {preset.special_effects}")
        print()

    print("=== 当前时段 ===")
    lighting.update_time_lighting()
    current_time = lighting.get_time_of_day()
    print(f"当前时段: {current_time.value}")
    print(f"环境光: {lighting.current_preset.ambient_color}")

    print("\n=== 状态光照测试 ===")
    lighting.set_status_lighting(StatusLighting.CODING)
    print(f"编程状态环境光: {lighting.current_preset.ambient_color}")

    lighting.set_status_lighting(StatusLighting.ERROR)
    print(f"错误状态环境光: {lighting.current_preset.ambient_color}")

    print("\n=== 颜色变换测试 ===")
    test_color = "#38bdf8"
    print(f"原始颜色: {test_color}")
    print(f"应用光照后: {lighting.apply_lighting_to_color(test_color)}")
    print(f"阴影颜色: {lighting.get_shadow_color(test_color)}")
    print(f"高光颜色: {lighting.get_highlight_color(test_color)}")
