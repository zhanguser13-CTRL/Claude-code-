#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3D Pseudo-Rendering Engine for Claude Pet

Provides layered rendering to create a pseudo-3D effect using tkinter canvas.
"""
import math
import random
import time
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field

from .evolution_stages import StageVisuals, get_stage_visuals
from .evolution_paths import EvolutionPathVisuals, get_path_visuals
from .lighting import LightingSystem, LightingPreset
from .body_parts import BodyPartsManager


@dataclass
class RenderLayer:
    """渲染层定义"""
    name: str
    z_index: float          # Z轴深度，越小越靠后
    tag: str                # Canvas tag
    visible: bool = True
    offset_x: float = 0     # 视差偏移X
    offset_y: float = 0     # 视差偏移Y


@dataclass
class RenderContext:
    """渲染上下文"""
    stage: StageVisuals
    path: EvolutionPathVisuals
    lighting: LightingPreset
    position: Tuple[float, float]  # (x, y) 中心位置
    mood: str = "happy"
    scale: float = 1.0
    float_offset: float = 0
    breathing_scale: float = 1.0
    mouse_offset: Tuple[float, float] = (0, 0)


class Renderer3D:
    """伪3D分层渲染引擎"""

    def __init__(self, canvas, width: int, height: int):
        self.canvas = canvas
        self.width = width
        self.height = height

        # 渲染层堆叠
        self.layers: List[RenderLayer] = []
        self._init_layers()

        # 光照系统
        self.lighting = LightingSystem()

        # 身体部位管理器
        self.body_parts = BodyPartsManager()

        # 动画状态
        self.animation_frame = 0
        self.pulse_phase = 0
        self.breathing_phase = 0
        self.float_phase = 0

        # 鼠标追踪
        self.mouse_x = 0
        self.mouse_y = 0

        # 渲染缓存
        self.render_cache: Dict[str, int] = {}  # tag -> item_id

    def _init_layers(self):
        """初始化渲染层"""
        self.layers = [
            RenderLayer("bg_particles", -10, "bg_particles", offset_y=0.5),
            RenderLayer("shadow", -5, "pet_shadow", offset_x=0.3, offset_y=0.5),
            RenderLayer("tail", -2, "pet_tail"),
            RenderLayer("body_back", -1, "pet_body_back"),
            RenderLayer("body", 0, "pet_body"),
            RenderLayer("belly", 1, "pet_belly"),
            RenderLayer("highlight", 2, "pet_highlight"),
            RenderLayer("ears", 3, "pet_ears"),
            RenderLayer("face", 4, "pet_face"),
            RenderLayer("antenna", 5, "pet_antenna"),
            RenderLayer("accessories", 6, "pet_accessories"),
            RenderLayer("aura", 7, "pet_aura"),
            RenderLayer("fg_particles", 10, "fg_particles", offset_y=1.5),
        ]

    def update_mouse_position(self, x: float, y: float):
        """更新鼠标位置"""
        self.mouse_x = x
        self.mouse_y = y

    def update_animation(self, dt: float = 1.0):
        """更新动画状态"""
        self.animation_frame += 1 * dt
        self.pulse_phase += 0.1 * dt
        self.breathing_phase += 0.05 * dt
        self.float_phase += 0.08 * dt

    def get_float_offset(self, amplitude: float, speed: float) -> float:
        """获取浮动偏移"""
        return math.sin(self.float_phase * speed) * amplitude

    def get_breathing_scale(self, intensity: float, speed: float) -> float:
        """获取呼吸缩放"""
        return 1 + math.sin(self.breathing_phase * speed) * intensity

    def render_pet(self, context: RenderContext):
        """渲染完整宠物"""
        # 清除旧的渲染
        self._clear_render()

        # 计算基础位置和缩放
        cx, cy = context.position
        scale = context.scale

        # 应用呼吸和浮动
        breathing = self.get_breathing_scale(
            context.stage.breathing_intensity,
            context.stage.breathing_speed
        )
        float_y = self.get_float_offset(
            context.stage.float_amplitude,
            context.stage.float_speed
        )

        # 更新上下文
        context.breathing_scale = breathing
        context.float_offset = float_y

        # 按层级渲染
        for layer in sorted(self.layers, key=lambda l: l.z_index):
            if layer.visible:
                self._render_layer(layer, context)

    def _render_layer(self, layer: RenderLayer, context: RenderContext):
        """渲染单个层"""
        cx, cy = context.position
        stage = context.stage
        path = context.path

        # 应用视差偏移
        parallax_x = layer.offset_x * (self.mouse_x - cx) * 0.1
        parallax_y = layer.offset_y * (self.mouse_y - cy) * 0.1

        layer_x = cx + parallax_x
        layer_y = cy + context.float_offset + parallax_y

        if layer.name == "shadow":
            self._render_shadow(layer_x, layer_y, stage, context)

        elif layer.name == "tail":
            self._render_tail(layer_x, layer_y, stage, path, context)

        elif layer.name == "body" or layer.name == "body_back":
            self._render_body(layer_x, layer_y, stage, path, context, back=(layer.name == "body_back"))

        elif layer.name == "belly":
            self._render_belly(layer_x, layer_y, stage, path, context)

        elif layer.name == "highlight":
            self._render_highlight(layer_x, layer_y, stage, path, context)

        elif layer.name == "ears":
            self._render_ears(layer_x, layer_y, stage, path, context)

        elif layer.name == "face":
            self._render_face(layer_x, layer_y, stage, path, context)

        elif layer.name == "antenna":
            self._render_antenna(layer_x, layer_y, stage, path, context)

        elif layer.name == "accessories":
            self._render_accessories(layer_x, layer_y, stage, path, context)

        elif layer.name == "aura":
            self._render_aura(layer_x, layer_y, stage, path, context)

    def _render_shadow(self, x: float, y: float, stage: StageVisuals, context: RenderContext):
        """渲染阴影"""
        if not stage.has_shadow:
            return

        breathing = context.breathing_scale
        lighting = context.lighting

        # 阴影随呼吸变化
        shadow_scale = breathing * (1 - stage.shadow_intensity * 0.2)
        shadow_intensity = int(255 * (1 - lighting.shadow_intensity * 0.5))

        base_size = 40 * context.scale
        width = base_size * 2 * shadow_scale
        height = base_size * 0.5 * shadow_scale

        # 创建渐变阴影（多层椭圆）
        for i in range(3):
            alpha = int(50 - i * 15)
            size_factor = 1 + i * 0.2
            self.canvas.create_oval(
                x - width/2 * size_factor, y + 45,
                x + width/2 * size_factor, y + 45 + height * size_factor,
                fill=f"#{shadow_intensity:02x}{shadow_intensity:02x}{shadow_intensity:02x}",
                outline='', stipple='gray50',
                tags='pet_shadow'
            )

    def _render_tail(self, x: float, y: float, stage: StageVisuals, path: EvolutionPathVisuals, context: RenderContext):
        """渲染尾巴"""
        if not stage.has_tail or stage.tail_length <= 0:
            return

        tail_length = 30 * stage.tail_length * path.scale_tail * context.scale

        # 计算尾巴摆动
        sway = math.sin(time.time() * 5) * 5

        # 尾巴段
        segments = 5
        points = []

        base_x = x - 10
        base_y = y + 30

        for i in range(segments + 1):
            t = i / segments
            segment_x = base_x - t * tail_length * 0.3 + sway * t
            segment_y = base_y - t * tail_length * 0.5 + math.sin(t * math.pi) * 5
            points.extend([segment_x, segment_y])

        # 绘制尾巴（使用平滑曲线）
        if len(points) >= 6:
            # 创建尾巴的多边形
            tail_width = 8 * context.scale * (1 - stage.tail_length * 0.3)

            left_points = []
            right_points = []

            for i in range(0, len(points), 2):
                if i + 1 < len(points):
                    px, py = points[i], points[i + 1]
                    # 计算垂直于尾巴方向
                    if i > 1:
                        prev_x, prev_y = points[i - 2], points[i - 1]
                        dx, dy = px - prev_x, py - prev_y
                        length = math.sqrt(dx*dx + dy*dy)
                        if length > 0:
                            nx, ny = -dy / length, dx / length
                            left_points.extend([px + nx * tail_width/2, py + ny * tail_width/2])
                            right_points.extend([px - nx * tail_width/2, py - ny * tail_width/2])

            # 合并左右点形成多边形
            all_points = left_points + right_points[::-1]

            if len(all_points) >= 6:
                self.canvas.create_polygon(
                    all_points,
                    fill=path.secondary_base,
                    outline=path.primary_shadow,
                    width=1,
                    smooth=True,
                    tags='pet_tail'
                )

    def _render_body(self, x: float, y: float, stage: StageVisuals, path: EvolutionPathVisuals,
                     context: RenderContext, back: bool = False):
        """渲染身体"""
        base_size = 50 * context.scale
        body_w = base_size * stage.body_size[0] * path.scale_body
        body_h = base_size * stage.body_size[1] * path.scale_body

        breathing = context.breathing_scale

        # 应用呼吸缩放
        body_w *= breathing
        body_h *= breathing

        if back:
            # 后层 - 暗部
            for i in range(stage.depth_layers - 1):
                offset = (stage.depth_layers - 1 - i) * 2
                color = self._adjust_brightness(path.primary_shadow, -i * 10)
                self.canvas.create_oval(
                    x - body_w/2 - offset, y - body_h/2 - offset,
                    x + body_w/2 + offset, y + body_h/2 + offset,
                    fill=color, outline='',
                    tags='pet_body_back'
                )
        else:
            # 主身体 - 分层渲染创建3D效果
            for i in range(min(3, stage.depth_layers)):
                offset = i * 1.5
                if i == 0:
                    color = path.primary_shadow
                elif i == 1:
                    color = path.primary_base
                else:
                    color = path.primary_highlight

                self.canvas.create_oval(
                    x - body_w/2 + offset, y - body_h/2 + offset,
                    x + body_w/2 - offset, y + body_h/2 - offset,
                    fill=color, outline='',
                    tags='pet_body'
                )

    def _render_belly(self, x: float, y: float, stage: StageVisuals, path: EvolutionPathVisuals, context: RenderContext):
        """渲染肚皮"""
        base_size = 50 * context.scale
        body_w = base_size * stage.body_size[0] * path.scale_body
        body_h = base_size * stage.body_size[1] * path.scale_body

        belly_w = body_w * 0.6
        belly_h = body_h * 0.4

        self.canvas.create_oval(
            x - belly_w/2, y + body_h * 0.1,
            x + belly_w/2, y + body_h * 0.1 + belly_h,
            fill=path.belly_color, outline='',
            stipple='gray75',
            tags='pet_belly'
        )

    def _render_highlight(self, x: float, y: float, stage: StageVisuals, path: EvolutionPathVisuals, context: RenderContext):
        """渲染高光"""
        base_size = 50 * context.scale
        body_w = base_size * stage.body_size[0] * path.scale_body
        body_h = base_size * stage.body_size[1] * path.scale_body

        highlight_w = body_w * 0.4
        highlight_h = body_h * 0.25

        # 高光位置
        highlight_x = x - body_w * 0.15
        highlight_y = y + body_h * 0.15

        pulse = math.sin(self.pulse_phase) * 3

        self.canvas.create_oval(
            highlight_x - highlight_w/2 + pulse/2, highlight_y - highlight_h/2 + pulse/2,
            highlight_x + highlight_w/2 - pulse/2, highlight_y + highlight_h/2 - pulse/2,
            fill=path.primary_highlight, outline='',
            stipple='gray75',
            tags='pet_highlight'
        )

    def _render_ears(self, x: float, y: float, stage: StageVisuals, path: EvolutionPathVisuals, context: RenderContext):
        """渲染耳朵"""
        if not stage.has_ears:
            return

        base_size = 50 * context.scale
        ear_w = 15 * stage.ear_size[0] * path.scale_ears * context.scale
        ear_h = 25 * stage.ear_size[1] * path.scale_ears * context.scale

        ear_offset_y = -30

        # 左耳
        left_ear_points = [
            x - 20 - ear_w/2, y + ear_offset_y,
            x - 30 - ear_w/2, y + ear_offset_y - ear_h,
            x - 10 - ear_w/2, y + ear_offset_y - ear_h * 0.7,
        ]
        self.canvas.create_polygon(
            left_ear_points, fill=path.primary_base,
            outline=path.primary_shadow, width=1, smooth=True,
            tags='pet_ears'
        )

        # 右耳
        right_ear_points = [
            x + 20 + ear_w/2, y + ear_offset_y,
            x + 30 + ear_w/2, y + ear_offset_y - ear_h,
            x + 10 + ear_w/2, y + ear_offset_y - ear_h * 0.7,
        ]
        self.canvas.create_polygon(
            right_ear_points, fill=path.primary_base,
            outline=path.primary_shadow, width=1, smooth=True,
            tags='pet_ears'
        )

        # 耳朵内侧
        inner_ear_w = ear_w * 0.5
        inner_ear_h = ear_h * 0.6

        left_inner_points = [
            x - 20 - ear_w/2, y + ear_offset_y - 5,
            x - 28 - ear_w/2, y + ear_offset_y - ear_h + 5,
            x - 12 - ear_w/2, y + ear_offset_y - ear_h * 0.7,
        ]
        self.canvas.create_polygon(
            left_inner_points, fill=path.secondary_base,
            outline='', smooth=True,
            tags='pet_ears'
        )

        right_inner_points = [
            x + 20 + ear_w/2, y + ear_offset_y - 5,
            x + 28 + ear_w/2, y + ear_offset_y - ear_h + 5,
            x + 12 + ear_w/2, y + ear_offset_y - ear_h * 0.7,
        ]
        self.canvas.create_polygon(
            right_inner_points, fill=path.secondary_base,
            outline='', smooth=True,
            tags='pet_ears'
        )

    def _render_face(self, x: float, y: float, stage: StageVisuals, path: EvolutionPathVisuals, context: RenderContext):
        """渲染面部"""
        # 这里调用表情渲染
        # 简化版本，实际应该有完整表情系统
        self._render_eyes(x, y, stage, path, context)
        self._render_mouth(x, y, stage, path, context)

    def _render_eyes(self, x: float, y: float, stage: StageVisuals, path: EvolutionPathVisuals, context: RenderContext):
        """渲染眼睛"""
        eye_y = y - 10
        eye_spacing = 15 * context.scale
        eye_size = 8 * context.scale

        # 眼睛跟随鼠标
        dx = self.mouse_x - x
        dy = self.mouse_y - eye_y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 0:
            max_offset = 3
            offset = min(max_offset, dist / 50)
            eye_offset_x = (dx / dist) * offset
            eye_offset_y = (dy / dist) * offset
        else:
            eye_offset_x = 0
            eye_offset_y = 0

        # 根据眼睛风格渲染
        if path.eye_style == "pixel":
            # 像素风格眼睛
            self._render_pixel_eyes(x, eye_y, eye_spacing, eye_size, eye_offset_x, eye_offset_y, path)
        elif path.eye_style == "sharp":
            # 锐利风格眼睛
            self._render_sharp_eyes(x, eye_y, eye_spacing, eye_size, eye_offset_x, eye_offset_y, path)
        elif path.eye_style == "gentle":
            # 温和风格眼睛
            self._render_gentle_eyes(x, eye_y, eye_spacing, eye_size, eye_offset_x, eye_offset_y, path)
        else:
            # 默认圆形眼睛
            self._render_round_eyes(x, eye_y, eye_spacing, eye_size, eye_offset_x, eye_offset_y, path)

    def _render_round_eyes(self, x: float, y: float, spacing: float, size: float,
                          ox: float, oy: float, path: EvolutionPathVisuals):
        """圆形眼睛"""
        # 左眼
        self.canvas.create_oval(
            x - spacing - size + ox, y - size + oy,
            x - spacing + size + ox, y + size + oy,
            fill='#0c4a6e', outline='', tags='pet_face'
        )
        self.canvas.create_oval(
            x - spacing - size*0.4 + ox, y - size*0.4 + oy,
            x - spacing + size*0.4 + ox, y + size*0.4 + oy,
            fill='white', outline='', tags='pet_face'
        )
        self.canvas.create_oval(
            x - spacing - size*0.15 + ox, y - size*0.15 + oy,
            x - spacing + size*0.15 + ox, y + size*0.15 + oy,
            fill='#0c4a6e', outline='', tags='pet_face'
        )

        # 右眼
        self.canvas.create_oval(
            x + spacing - size + ox, y - size + oy,
            x + spacing + size + ox, y + size + oy,
            fill='#0c4a6e', outline='', tags='pet_face'
        )
        self.canvas.create_oval(
            x + spacing - size*0.4 + ox, y - size*0.4 + oy,
            x + spacing + size*0.4 + ox, y + size*0.4 + oy,
            fill='white', outline='', tags='pet_face'
        )
        self.canvas.create_oval(
            x + spacing - size*0.15 + ox, y - size*0.15 + oy,
            x + spacing + size*0.15 + ox, y + size*0.15 + oy,
            fill='#0c4a6e', outline='', tags='pet_face'
        )

    def _render_pixel_eyes(self, x: float, y: float, spacing: float, size: float,
                          ox: float, oy: float, path: EvolutionPathVisuals):
        """像素风格眼睛（Coder路径）"""
        eye_color = path.accent_color

        # 左眼 - 像素网格
        for i in range(3):
            for j in range(3):
                pixel_size = size * 0.3
                px = x - spacing - size + ox + i * pixel_size * 1.2
                py = y - size + oy + j * pixel_size * 1.2
                if (i + j) % 2 == 0:
                    self.canvas.create_rectangle(
                        px, py, px + pixel_size, py + pixel_size,
                        fill=eye_color, outline='', tags='pet_face'
                    )

        # 右眼
        for i in range(3):
            for j in range(3):
                pixel_size = size * 0.3
                px = x + spacing - size + ox + i * pixel_size * 1.2
                py = y - size + oy + j * pixel_size * 1.2
                if (i + j) % 2 == 0:
                    self.canvas.create_rectangle(
                        px, py, px + pixel_size, py + pixel_size,
                        fill=eye_color, outline='', tags='pet_face'
                    )

    def _render_sharp_eyes(self, x: float, y: float, spacing: float, size: float,
                          ox: float, oy: float, path: EvolutionPathVisuals):
        """锐利风格眼睛（Warrior/NightOwl路径）"""
        eye_color = path.accent_color

        # 左眼 - 菱形
        left_eye_points = [
            x - spacing + ox, y - size + oy,
            x - spacing + size*0.5 + ox, y + oy,
            x - spacing + ox, y + size + oy,
            x - spacing - size*0.5 + ox, y + oy,
        ]
        self.canvas.create_polygon(
            left_eye_points, fill=eye_color, outline=path.primary_shadow,
            width=1, tags='pet_face'
        )
        self.canvas.create_oval(
            x - spacing - size*0.2 + ox, y - size*0.2 + oy,
            x - spacing + size*0.2 + ox, y + size*0.2 + oy,
            fill='#fbbf24', outline='', tags='pet_face'
        )

        # 右眼
        right_eye_points = [
            x + spacing + ox, y - size + oy,
            x + spacing + size*0.5 + ox, y + oy,
            x + spacing + ox, y + size + oy,
            x + spacing - size*0.5 + ox, y + oy,
        ]
        self.canvas.create_polygon(
            right_eye_points, fill=eye_color, outline=path.primary_shadow,
            width=1, tags='pet_face'
        )
        self.canvas.create_oval(
            x + spacing - size*0.2 + ox, y - size*0.2 + oy,
            x + spacing + size*0.2 + ox, y + size*0.2 + oy,
            fill='#fbbf24', outline='', tags='pet_face'
        )

    def _render_gentle_eyes(self, x: float, y: float, spacing: float, size: float,
                           ox: float, oy: float, path: EvolutionPathVisuals):
        """温和风格眼睛（Balanced路径）"""
        # 大而温和的眼睛
        self.canvas.create_oval(
            x - spacing - size*1.2 + ox, y - size*0.8 + oy,
            x - spacing + size*1.2 + ox, y + size*1.2 + oy,
            fill=path.accent_color, outline='', tags='pet_face'
        )
        self.canvas.create_oval(
            x - spacing - size*0.5 + ox, y - size*0.3 + oy,
            x - spacing + size*0.5 + ox, y + size*0.3 + oy,
            fill='white', outline='', tags='pet_face'
        )

        self.canvas.create_oval(
            x + spacing - size*1.2 + ox, y - size*0.8 + oy,
            x + spacing + size*1.2 + ox, y + size*1.2 + oy,
            fill=path.accent_color, outline='', tags='pet_face'
        )
        self.canvas.create_oval(
            x + spacing - size*0.5 + ox, y - size*0.3 + oy,
            x + spacing + size*0.5 + ox, y + size*0.3 + oy,
            fill='white', outline='', tags='pet_face'
        )

    def _render_mouth(self, x: float, y: float, stage: StageVisuals, path: EvolutionPathVisuals, context: RenderContext):
        """渲染嘴巴"""
        mouth_y = y + 12

        # 根据心情绘制嘴巴
        mood = context.mood

        if mood == "happy":
            # 微笑
            self.canvas.create_arc(
                x - 10, mouth_y - 3, x + 10, mouth_y + 7,
                start=0, extent=180, style='arc',
                outline=path.accent_color, width=2, capstyle='round',
                tags='pet_face'
            )
        elif mood == "excited":
            # 大笑
            self.canvas.create_arc(
                x - 12, mouth_y - 5, x + 12, mouth_y + 10,
                start=0, extent=180, style='arc',
                outline=path.accent_color, width=3, capstyle='round',
                tags='pet_face'
            )
        elif mood == "surprised":
            # O型嘴
            self.canvas.create_oval(
                x - 5, mouth_y, x + 5, mouth_y + 10,
                fill=path.primary_shadow, outline=path.accent_color, width=1,
                tags='pet_face'
            )
        else:
            # 默认微笑
            self.canvas.create_line(
                x - 8, mouth_y + 5, x + 8, mouth_y + 3,
                fill=path.accent_color, width=2, capstyle='round',
                tags='pet_face'
            )

    def _render_antenna(self, x: float, y: float, stage: StageVisuals, path: EvolutionPathVisuals, context: RenderContext):
        """渲染天线"""
        if not stage.has_antenna:
            return

        antenna_y = y - 30
        bulb_size = 8 * context.scale

        # 天线杆
        self.canvas.create_line(
            x, antenna_y - 10, x, antenna_y - 25,
            fill=path.primary_highlight, width=2, capstyle='round',
            tags='pet_antenna'
        )

        # 天线球 - 带脉动效果
        pulse = math.sin(self.pulse_phase) * 2
        glow_intensity = int(150 + 100 * math.sin(self.pulse_phase))

        self.canvas.create_oval(
            x - bulb_size/2 + pulse/2, antenna_y - 25 - bulb_size + pulse/2,
            x + bulb_size/2 - pulse/2, antenna_y - 25 + pulse/2,
            fill=path.accent_color, outline='white', width=1,
            tags='pet_antenna'
        )

        # 发光效果
        for i in range(2):
            glow_size = bulb_size + (i + 1) * 4
            alpha = 50 - i * 20
            stipple = 'gray50' if i == 0 else 'gray25'
            self.canvas.create_oval(
                x - glow_size/2, antenna_y - 25 - glow_size/2,
                x + glow_size/2, antenna_y - 25 + glow_size/2,
                outline=path.glow_color, width=1, stipple=stipple,
                tags='pet_antenna'
            )

    def _render_accessories(self, x: float, y: float, stage: StageVisuals, path: EvolutionPathVisuals, context: RenderContext):
        """渲染配饰"""
        for accessory in stage.accessories:
            self._render_accessory(x, y, accessory, path, context)

        # 路径特定配饰
        path_stage_accessories = path.stage_accessories.get(stage.stage_id, [])
        for accessory in path_stage_accessories:
            self._render_accessory(x, y, accessory, path, context)

    def _render_accessory(self, x: float, y: float, accessory_id: str, path: EvolutionPathVisuals, context: RenderContext):
        """渲染单个配饰"""
        from .evolution_paths import get_accessory_config

        config = get_accessory_config(accessory_id)
        if not config:
            return

        acc_type = config.get("type")
        color = config.get("color", path.accent_color)

        if acc_type == "antenna":
            # 顶部天线装饰
            size = config.get("size", 5) * context.scale
            antenna_y = y - 55
            shape = config.get("shape", "circle")

            if shape == "star":
                self.canvas.create_text(
                    x, antenna_y, text="★",
                    fill=color, font=('Arial', int(size * 2)),
                    tags='pet_accessories'
                )
            elif shape == "sword":
                self.canvas.create_text(
                    x, antenna_y, text="⚔️",
                    fill=color, font=('Arial', int(size * 2)),
                    tags='pet_accessories'
                )
            elif shape == "heart":
                self.canvas.create_text(
                    x, antenna_y, text="♥",
                    fill=color, font=('Arial', int(size * 2)),
                    tags='pet_accessories'
                )
            else:
                self.canvas.create_oval(
                    x - size, antenna_y - size, x + size, antenna_y + size,
                    fill=color, outline='white', width=1,
                    tags='pet_accessories'
                )

        elif acc_type == "bow":
            # 蝴蝶结
            bow_y = y - 25
            bow_size = 12 * context.scale
            self.canvas.create_polygon(
                x - bow_size*2, bow_y,
                x - bow_size, bow_y - bow_size/2,
                x - bow_size, bow_y + bow_size/2,
                fill=color, outline=path.primary_shadow, width=1,
                smooth=True, tags='pet_accessories'
            )
            self.canvas.create_polygon(
                x + bow_size*2, bow_y,
                x + bow_size, bow_y - bow_size/2,
                x + bow_size, bow_y + bow_size/2,
                fill=color, outline=path.primary_shadow, width=1,
                smooth=True, tags='pet_accessories'
            )
            self.canvas.create_oval(
                x - 5, bow_y - 3, x + 5, bow_y + 3,
                fill=color, outline='', tags='pet_accessories'
            )

        elif acc_type == "aura":
            # 光环
            base_size = 60 * context.scale
            pulse = math.sin(self.pulse_phase) * 5

            for i in range(3):
                aura_size = base_size + i * 10 + pulse
                stipple = ['gray50', 'gray25', 'gray12'][i]
                self.canvas.create_oval(
                    x - aura_size, y - aura_size,
                    x + aura_size, y + aura_size,
                    outline=color, width=1, stipple=stipple,
                    tags='pet_aura'
                )

        elif acc_type == "halo":
            # 头顶光环
            halo_y = y - 50
            halo_width = 40 * context.scale
            symbol = config.get("symbol", "✦")

            self.canvas.create_arc(
                x - halo_width/2, halo_y - 10,
                x + halo_width/2, halo_y + 10,
                start=0, extent=180, style='arc',
                outline=color, width=2, tags='pet_accessories'
            )
            self.canvas.create_text(
                x, halo_y, text=symbol,
                fill=color, font=('Arial', 12),
                tags='pet_accessories'
            )

        elif acc_type == "cape":
            # 披风
            cape_points = [
                x - 20, y + 10,
                x - 30, y + 50,
                x, y + 45,
                x + 30, y + 50,
                x + 20, y + 10,
            ]
            self.canvas.create_polygon(
                cape_points, fill=color, outline=path.primary_shadow,
                width=1, smooth=True, stipple='gray75',
                tags='pet_accessories'
            )

    def _render_aura(self, x: float, y: float, stage: StageVisuals, path: EvolutionPathVisuals, context: RenderContext):
        """渲染光环效果"""
        if not stage.has_glow:
            return

        base_size = 55 * context.scale
        pulse = math.sin(self.pulse_phase * 0.5) * 3

        # 多层发光
        for i in range(3):
            glow_size = base_size + i * 8 + pulse
            stipple = ['gray25', 'gray12', 'gray6'][i]
            self.canvas.create_oval(
                x - glow_size, y - glow_size,
                x + glow_size, y + glow_size,
                outline=path.glow_color, width=1, stipple=stipple,
                tags='pet_aura'
            )

    def _clear_render(self):
        """清除渲染"""
        # 不需要在这里清除，因为我们会更新现有图形
        pass

    def _adjust_brightness(self, color: str, amount: int) -> str:
        """调整颜色亮度"""
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)

        r = max(0, min(255, r + amount))
        g = max(0, min(255, g + amount))
        b = max(0, min(255, b + amount))

        return f'#{r:02x}{g:02x}{b:02x}'

    def animate_evolution(self, from_stage: int, to_stage: int, callback: Optional[Callable] = None):
        """执行进化动画"""
        from .animations import EvolutionAnimation

        animation = EvolutionAnimation(self.canvas, self.width, self.height)
        animation.start(from_stage, to_stage, callback)


if __name__ == "__main__":
    import tkinter as tk

    # 测试渲染器
    root = tk.Tk()
    root.title("3D Pet Renderer Test")
    root.geometry("300x400")

    canvas = tk.Canvas(root, width=300, height=400, bg='#0f172a', highlightthickness=0)
    canvas.pack()

    renderer = Renderer3D(canvas, 300, 400)

    # 创建渲染上下文
    from .evolution_stages import get_stage_visuals
    from .evolution_paths import get_path_visuals
    from .lighting import LightingPreset

    stage = get_stage_visuals(5)  # Teen
    path = get_path_visuals("coder")
    lighting = LightingPreset(
        name="test",
        ambient_color=(1.0, 1.0, 1.0),
        shadow_intensity=0.4,
        highlight_intensity=0.8,
        glow_intensity=1.0
    )

    context = RenderContext(
        stage=stage,
        path=path,
        lighting=lighting,
        position=(150, 180),
        mood="happy",
        scale=1.2
    )

    # 绘制背景
    for i in range(50):
        color_val = int(15 + i * 0.2)
        color = f'#{color_val:02x}{color_val+10:02x}{color_val+30:02x}'
        y_start = i * 8
        canvas.create_rectangle(0, y_start, 300, y_start + 8, fill=color, outline='')

    # 渲染宠物
    renderer.render_pet(context)

    root.mainloop()
