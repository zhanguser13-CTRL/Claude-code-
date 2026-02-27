#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Body Parts System for Claude Pet

Defines and manages individual body parts with their visual properties.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Callable
from enum import Enum
import math
import time


class BodyPartType(Enum):
    """身体部位类型"""
    HEAD = "head"
    BODY = "body"
    EARS = "ears"
    TAIL = "tail"
    EYES = "eyes"
    MOUTH = "mouth"
    ANTENNA = "antenna"
    BELLY = "belly"
    WINGS = "wings"
    ACCESSORY = "accessory"


@dataclass
class BodyPartConfig:
    """身体部位配置"""
    part_type: BodyPartType
    name: str

    # 基础属性
    enabled: bool = True
    visible: bool = True

    # 尺寸 (相对于基准尺寸的倍数)
    scale_x: float = 1.0
    scale_y: float = 1.0

    # 位置偏移
    offset_x: float = 0
    offset_y: float = 0

    # 3D深度
    z_depth: float = 0

    # 颜色
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None

    # 动画
    animated: bool = False
    animation_speed: float = 1.0
    animation_amplitude: float = 1.0

    # 特殊效果
    glow: bool = False
    shadow: bool = True
    gradient: bool = False


@dataclass
class BodyPartState:
    """身体部位状态"""
    config: BodyPartConfig

    # 当前变换
    current_scale_x: float = 1.0
    current_scale_y: float = 1.0
    current_offset_x: float = 0
    current_offset_y: float = 0
    current_rotation: float = 0

    # 动画相位
    animation_phase: float = 0

    # 眨眼状态
    is_blinking: bool = False
    blink_progress: float = 0

    # 特殊状态
    twitch_intensity: float = 0
    shake_intensity: float = 0


class BodyPart:
    """身体部位类"""

    def __init__(self, config: BodyPartConfig):
        self.config = config
        self.state = BodyPartState(config)
        self.children: List['BodyPart'] = []
        self.parent: Optional['BodyPart'] = None

    def update(self, dt: float = 1.0):
        """更新部位状态"""
        if self.config.animated:
            self.state.animation_phase += self.config.animation_speed * dt

        # 更新眨眼
        if self.state.is_blinking:
            self.state.blink_progress += dt * 0.1
            if self.state.blink_progress >= 1.0:
                self.state.is_blinking = False
                self.state.blink_progress = 0

        # 衰减抽动和震动
        self.state.twitch_intensity *= 0.9
        self.state.shake_intensity *= 0.8

        # 更新子部位
        for child in self.children:
            child.update(dt)

    def add_child(self, child: 'BodyPart'):
        """添加子部位"""
        child.parent = self
        self.children.append(child)

    def get_world_position(self, base_x: float, base_y: float) -> Tuple[float, float]:
        """获取世界坐标位置"""
        x = base_x + self.config.offset_x + self.state.current_offset_x
        y = base_y + self.config.offset_y + self.state.current_offset_y

        if self.parent:
            parent_x, parent_y = self.parent.get_world_position(base_x, base_y)
            x += parent_x - base_x
            y += parent_y - base_y

        return x, y

    def get_world_scale(self) -> Tuple[float, float]:
        """获取世界缩放"""
        sx = self.config.scale_x * self.state.current_scale_x
        sy = self.config.scale_y * self.state.current_scale_y

        if self.parent:
            px, py = self.parent.get_world_scale()
            sx *= px
            sy *= py

        return sx, sy

    def trigger_blink(self):
        """触发眨眼"""
        if self.config.part_type == BodyPartType.EYES:
            self.state.is_blinking = True
            self.state.blink_progress = 0

    def trigger_twitch(self, intensity: float = 1.0):
        """触发抽动"""
        self.state.twitch_intensity = intensity

    def trigger_shake(self, intensity: float = 1.0):
        """触发震动"""
        self.state.shake_intensity = intensity


class EyePart(BodyPart):
    """眼睛部位"""

    def __init__(self, side: str = "left", **kwargs):
        config = BodyPartConfig(
            part_type=BodyPartType.EYES,
            name=f"{side}_eye",
            animated=True,
            animation_speed=0.5,
            **kwargs
        )
        super().__init__(config)
        self.side = side  # "left" or "right"
        self.pupil_offset_x = 0
        self.pupil_offset_y = 0

    def look_at(self, target_x: float, target_y: float, center_x: float, center_y: float):
        """让眼睛看向目标"""
        dx = target_x - center_x
        dy = target_y - center_y
        dist = math.sqrt(dx*dx + dy*dy)
        max_offset = 3
        if dist > 0:
            offset = min(max_offset, dist / 50)
            self.pupil_offset_x = (dx / dist) * offset
            self.pupil_offset_y = (dy / dist) * offset


class EarPart(BodyPart):
    """耳朵部位"""

    def __init__(self, side: str = "left", ear_type: str = "pointed", **kwargs):
        config = BodyPartConfig(
            part_type=BodyPartType.EARS,
            name=f"{side}_ear",
            animated=True,
            animation_speed=0.3,
            **kwargs
        )
        super().__init__(config)
        self.side = side
        self.ear_type = ear_type
        self.flop_angle = 0

    def set_flop(self, angle: float):
        """设置耳朵下垂角度"""
        self.flop_angle = max(-30, min(30, angle))

    def twitch(self):
        """抽动耳朵"""
        self.trigger_twitch(1.0)


class TailPart(BodyPart):
    """尾巴部位"""

    def __init__(self, tail_type: str = "long", **kwargs):
        config = BodyPartConfig(
            part_type=BodyPartType.TAIL,
            name="tail",
            animated=True,
            animation_speed=2.0,
            animation_amplitude=5.0,
            **kwargs
        )
        super().__init__(config)
        self.tail_type = tail_type
        self.segments = 5
        self.wave_phase = 0

    def update(self, dt: float = 1.0):
        super().update(dt)
        self.wave_phase += self.config.animation_speed * dt * 0.1

    def wag(self):
        """摇尾巴"""
        self.state.animation_phase += math.pi


class AntennaPart(BodyPart):
    """天线部位"""

    def __init__(self, **kwargs):
        config = BodyPartConfig(
            part_type=BodyPartType.ANTENNA,
            name="antenna",
            animated=True,
            animation_speed=0.5,
            glow=True,
            **kwargs
        )
        super().__init__(config)
        self.pulse_phase = 0
        self.bulb_color = None

    def update(self, dt: float = 1.0):
        super().update(dt)
        self.pulse_phase += 0.1 * dt

    def set_bulb_color(self, color: str):
        """设置灯泡颜色"""
        self.bulb_color = color

    def get_pulse_scale(self) -> float:
        """获取脉动缩放"""
        return 1 + math.sin(self.pulse_phase) * 0.1


@dataclass
class PetBodyConfiguration:
    """宠物整体身体配置"""

    # 头部
    head: BodyPartConfig = field(default_factory=lambda: BodyPartConfig(
        part_type=BodyPartType.HEAD,
        name="head",
        scale_x=1.0, scale_y=1.0,
        offset_y=-10,
        z_depth=0
    ))

    # 身体
    body: BodyPartConfig = field(default_factory=lambda: BodyPartConfig(
        part_type=BodyPartType.BODY,
        name="body",
        scale_x=1.0, scale_y=1.0,
        offset_y=10,
        z_depth=-1
    ))

    # 耳朵
    ears: BodyPartConfig = field(default_factory=lambda: BodyPartConfig(
        part_type=BodyPartType.EARS,
        name="ears",
        scale_x=1.0, scale_y=1.0,
        offset_y=-40,
        z_depth=1,
        animated=True
    ))

    # 尾巴
    tail: BodyPartConfig = field(default_factory=lambda: BodyPartConfig(
        part_type=BodyPartType.TAIL,
        name="tail",
        scale_x=1.0, scale_y=1.0,
        offset_x=-15, offset_y=25,
        z_depth=-2,
        animated=True
    ))

    # 天线
    antenna: BodyPartConfig = field(default_factory=lambda: BodyPartConfig(
        part_type=BodyPartType.ANTENNA,
        name="antenna",
        scale_x=1.0, scale_y=1.0,
        offset_y=-60,
        z_depth=2,
        animated=True,
        glow=True
    ))

    # 眼睛
    eyes: BodyPartConfig = field(default_factory=lambda: BodyPartConfig(
        part_type=BodyPartType.EYES,
        name="eyes",
        scale_x=1.0, scale_y=1.0,
        offset_y=-10,
        z_depth=3,
        animated=True
    ))

    # 嘴巴
    mouth: BodyPartConfig = field(default_factory=lambda: BodyPartConfig(
        part_type=BodyPartType.MOUTH,
        name="mouth",
        scale_x=1.0, scale_y=1.0,
        offset_y=15,
        z_depth=3
    ))

    # 肚皮
    belly: BodyPartConfig = field(default_factory=lambda: BodyPartConfig(
        part_type=BodyPartType.BELLY,
        name="belly",
        scale_x=0.6, scale_y=0.4,
        offset_y=10,
        z_depth=1
    ))


class BodyPartsManager:
    """身体部位管理器"""

    def __init__(self, config: Optional[PetBodyConfiguration] = None):
        self.config = config or PetBodyConfiguration()
        self.parts: Dict[str, BodyPart] = {}
        self._init_parts()

    def _init_parts(self):
        """初始化所有部位"""
        self.parts = {
            "head": BodyPart(self.config.head),
            "body": BodyPart(self.config.body),
            "left_ear": EarPart("left"),
            "right_ear": EarPart("right"),
            "tail": TailPart(),
            "antenna": AntennaPart(),
            "left_eye": EyePart("left"),
            "right_eye": EyePart("right"),
            "mouth": BodyPart(self.config.mouth),
            "belly": BodyPart(self.config.belly),
        }

        # 建立父子关系
        self.parts["body"].add_child(self.parts["head"])
        self.parts["head"].add_child(self.parts["left_ear"])
        self.parts["head"].add_child(self.parts["right_ear"])
        self.parts["head"].add_child(self.parts["antenna"])
        self.parts["head"].add_child(self.parts["left_eye"])
        self.parts["head"].add_child(self.parts["right_eye"])
        self.parts["head"].add_child(self.parts["mouth"])
        self.parts["body"].add_child(self.parts["belly"])
        self.parts["body"].add_child(self.parts["tail"])

    def update(self, dt: float = 1.0):
        """更新所有部位"""
        for part in self.parts.values():
            part.update(dt)

    def get_part(self, name: str) -> Optional[BodyPart]:
        """获取部位"""
        return self.parts.get(name)

    def trigger_ear_twitch(self, side: str = "random"):
        """触发耳朵抽动"""
        if side == "random":
            import random
            side = random.choice(["left", "right", "both"])

        if side in ["left", "both"]:
            ear = self.parts.get("left_ear")
            if isinstance(ear, EarPart):
                ear.twitch()
        if side in ["right", "both"]:
            ear = self.parts.get("right_ear")
            if isinstance(ear, EarPart):
                ear.twitch()

    def trigger_blink(self):
        """触发眨眼"""
        for eye_name in ["left_eye", "right_eye"]:
            eye = self.parts.get(eye_name)
            if isinstance(eye, EyePart):
                eye.trigger_blink()

    def tail_wag(self):
        """摇尾巴"""
        tail = self.parts.get("tail")
        if isinstance(tail, TailPart):
            tail.wag()

    def update_eye_look(self, target_x: float, target_y: float, center_x: float, center_y: float):
        """更新眼睛注视方向"""
        for eye_name in ["left_eye", "right_eye"]:
            eye = self.parts.get(eye_name)
            if isinstance(eye, EyePart):
                eye.look_at(target_x, target_y, center_x, center_y)

    def apply_stage_modifications(self, stage_visuals):
        """根据阶段修改身体部位"""
        scale_mod = stage_visuals.body_size[0]

        # 更新各部位的缩放
        if "head" in self.parts:
            self.parts["head"].config.scale_x = stage_visuals.head_size[0]
            self.parts["head"].config.scale_y = stage_visuals.head_size[1]

        if "body" in self.parts:
            self.parts["body"].config.scale_x = stage_visuals.body_size[0]
            self.parts["body"].config.scale_y = stage_visuals.body_size[1]

        if "left_ear" in self.parts and "right_ear" in self.parts:
            self.parts["left_ear"].config.scale_x = stage_visuals.ear_size[0]
            self.parts["left_ear"].config.scale_y = stage_visuals.ear_size[1]
            self.parts["right_ear"].config.scale_x = stage_visuals.ear_size[0]
            self.parts["right_ear"].config.scale_y = stage_visuals.ear_size[1]

        if "tail" in self.parts:
            tail = self.parts["tail"]
            if isinstance(tail, TailPart):
                tail.config.scale_x = stage_visuals.tail_length
                tail.config.scale_y = stage_visuals.tail_length

    def apply_path_modifications(self, path_visuals):
        """根据路径修改身体部位"""
        # 应用路径特定的颜色和样式
        for part_name, part in self.parts.items():
            if hasattr(path_visuals, 'primary_base'):
                part.config.primary_color = path_visuals.primary_base

    def get_visible_parts(self) -> List[BodyPart]:
        """获取所有可见部位"""
        return [p for p in self.parts.values() if p.config.visible]

    def get_parts_by_type(self, part_type: BodyPartType) -> List[BodyPart]:
        """根据类型获取部位"""
        return [p for p in self.parts.values() if p.config.part_type == part_type]


# 预定义的身体形状配置
BODY_SHAPES = {
    "round": PetBodyConfiguration(
        head=BodyPartConfig(BodyPartType.HEAD, "head", scale_x=1.1, scale_y=1.1),
        body=BodyPartConfig(BodyPartType.BODY, "body", scale_x=1.15, scale_y=1.1),
    ),
    "oval": PetBodyConfiguration(
        head=BodyPartConfig(BodyPartType.HEAD, "head", scale_x=1.0, scale_y=1.0),
        body=BodyPartConfig(BodyPartType.BODY, "body", scale_x=1.0, scale_y=1.05),
    ),
    "slender": PetBodyConfiguration(
        head=BodyPartConfig(BodyPartType.HEAD, "head", scale_x=0.95, scale_y=1.0),
        body=BodyPartConfig(BodyPartType.BODY, "body", scale_x=0.9, scale_y=1.1),
    ),
    "bulky": PetBodyConfiguration(
        head=BodyPartConfig(BodyPartType.HEAD, "head", scale_x=1.0, scale_y=1.0),
        body=BodyPartConfig(BodyPartType.BODY, "body", scale_x=1.2, scale_y=1.15),
    ),
}


def get_body_shape(shape_name: str) -> PetBodyConfiguration:
    """获取身体形状配置"""
    return BODY_SHAPES.get(shape_name, BODY_SHAPES["oval"])


if __name__ == "__main__":
    # 测试身体部位系统
    manager = BodyPartsManager()

    print("身体部位:")
    for name, part in manager.parts.items():
        print(f"  {name}: {part.config.name} (type: {part.config.part_type.value})")

    # 测试更新
    manager.update(1.0)

    # 测试眨眼
    manager.trigger_blink()
    print("\n触发眨眼后:")
    eye = manager.get_part("left_eye")
    if isinstance(eye, EyePart):
        print(f"  左眼正在眨眼: {eye.state.is_blinking}")

    # 测试耳朵抽动
    manager.trigger_ear_twitch("left")
    print("\n触发左耳抽动后:")
    ear = manager.get_part("left_ear")
    if isinstance(ear, EarPart):
        print(f"  左耳抽动强度: {ear.state.twitch_intensity}")
