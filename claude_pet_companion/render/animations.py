#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Animation System for Claude Pet

Handles evolution animations, transitions, and special effects.
"""
import math
import time
import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Callable
from enum import Enum
import tkinter as tk


class AnimationType(Enum):
    """动画类型"""
    IDLE = "idle"
    WALK = "walk"
    JUMP = "jump"
    ATTACK = "attack"
    EVOLUTION = "evolution"
    CELEBRATION = "celebration"
    HURT = "hurt"
    SLEEP = "sleep"
    EAT = "eat"


class EasingType(Enum):
    """缓动类型"""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    ELASTIC = "elastic"


@dataclass
class AnimationPhase:
    """动画阶段"""
    time: float                  # 开始时间（毫秒）
    duration: float              # 持续时间（毫秒）
    effect: str                  # 特效名称
    parameters: Dict = field(default_factory=dict)


@dataclass
class Particle:
    """粒子"""
    x: float
    y: float
    vx: float
    vy: float
    life: float                  # 生命周期
    max_life: float
    size: float
    color: str
    shape: str = "circle"
    rotation: float = 0
    rotation_speed: float = 0


class EvolutionAnimation:
    """进化动画"""

    def __init__(self, canvas: tk.Canvas, width: int, height: int):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.particles: List[Particle] = []
        self.is_playing = False
        self.start_time = 0
        self.from_stage = 0
        self.to_stage = 0
        self.callback: Optional[Callable] = None

        # 动画配置
        self.duration = 3000  # 总持续时间（毫秒）
        self.phases = [
            AnimationPhase(0, 100, "screen_flash", {"color": "white"}),
            AnimationPhase(100, 200, "pet_glow", {"intensity": 1.0}),
            AnimationPhase(300, 700, "spiral_particles", {"count": 20}),
            AnimationPhase(500, 1000, "body_morph", {"easing": "easeInOut"}),
            AnimationPhase(1500, 500, "energy_gather"),
            AnimationPhase(2000, 500, "burst", {"particle_type": "star"}),
            AnimationPhase(2500, 500, "new_form_reveal"),
            AnimationPhase(3000, 2000, "celebration"),
        ]

        # 渲染项
        self.render_items: Dict[str, int] = {}

    def start(self, from_stage: int, to_stage: int, callback: Optional[Callable] = None):
        """开始进化动画"""
        self.from_stage = from_stage
        self.to_stage = to_stage
        self.callback = callback
        self.is_playing = True
        self.start_time = time.time() * 1000
        self.particles.clear()

        # 开始动画循环
        self._animate()

    def _animate(self):
        """动画循环"""
        if not self.is_playing:
            return

        current_time = time.time() * 1000
        elapsed = current_time - self.start_time

        if elapsed >= self.duration + 2000:  # 包括庆祝动画
            self._finish()
            return

        # 清除上一帧
        self._clear_frame()

        # 更新和绘制粒子
        self._update_particles(elapsed)

        # 处理动画阶段
        self._process_phases(elapsed)

        # 绘制宠物状态
        self._render_pet_state(elapsed)

        # 继续动画
        self.canvas.after(16, self._animate)  # ~60 FPS

    def _process_phases(self, elapsed: float):
        """处理动画阶段"""
        for phase in self.phases:
            phase_start = phase.time
            phase_end = phase.time + phase.duration

            if phase_start <= elapsed < phase_end:
                progress = (elapsed - phase_start) / phase.duration
                self._apply_phase_effect(phase, progress)

    def _apply_phase_effect(self, phase: AnimationPhase, progress: float):
        """应用阶段特效"""
        effect = phase.effect
        params = phase.parameters

        if effect == "screen_flash":
            self._screen_flash(params.get("color", "white"), progress)

        elif effect == "pet_glow":
            self._pet_glow(params.get("intensity", 1.0), progress)

        elif effect == "spiral_particles":
            if progress < 0.5:
                count = params.get("count", 20)
                self._spawn_spiral_particles(count, progress * 2)

        elif effect == "body_morph":
            easing = params.get("easing", "easeInOut")
            self._body_morph(progress, easing)

        elif effect == "energy_gather":
            self._energy_gather(progress)

        elif effect == "burst":
            particle_type = params.get("particle_type", "star")
            if progress < 0.2:
                self._spawn_burst_particles(particle_type)

        elif effect == "new_form_reveal":
            self._new_form_reveal(progress)

        elif effect == "celebration":
            self._celebration(progress)

    def _screen_flash(self, color: str, progress: float):
        """屏幕闪白"""
        if progress < 0.5:
            alpha = int(255 * (1 - progress * 2))
            # 使用stipple模拟透明度
            stipple = self._alpha_to_stipple(alpha)
            self.canvas.create_rectangle(
                0, 0, self.width, self.height,
                fill=color, outline='', stipple=stipple,
                tags='evo_flash'
            )

    def _pet_glow(self, intensity: float, progress: float):
        """宠物发光"""
        cx, cy = self.width / 2, self.height / 2
        base_size = 60

        # 脉动发光
        pulse = math.sin(progress * math.pi * 4) * 10
        glow_size = base_size + pulse

        for i in range(3):
            size = glow_size + i * 15
            stipple = ['gray50', 'gray25', 'gray12'][i]
            self.canvas.create_oval(
                cx - size, cy - size, cx + size, cy + size,
                outline='#fbbf24', width=2, stipple=stipple,
                tags='evo_glow'
            )

    def _spawn_spiral_particles(self, count: int, progress: float):
        """生成螺旋粒子"""
        cx, cy = self.width / 2, self.height / 2

        # 每次调用添加几个粒子
        if random.random() < 0.3:
            angle = progress * math.pi * 8  # 2圈
            radius = 50 + progress * 30

            px = cx + math.cos(angle) * radius
            py = cy + math.sin(angle) * radius

            # 向中心移动
            vx = (cx - px) * 0.02
            vy = (cy - py) * 0.02

            self.particles.append(Particle(
                x=px, y=py, vx=vx, vy=vy,
                life=60, max_life=60,
                size=8,
                color=random.choice(['#fbbf24', '#f472b6', '#a78bfa']),
                shape=random.choice(['star', 'circle', 'diamond'])
            ))

    def _body_morph(self, progress: float, easing: str):
        """身体变形效果"""
        # 这里会由主渲染器处理
        pass

    def _energy_gather(self, progress: float):
        """能量聚集效果"""
        cx, cy = self.width / 2, self.height / 2

        # 能量环
        radius = 30 + progress * 40
        self.canvas.create_oval(
            cx - radius, cy - radius, cx + radius, cy + radius,
            outline='#60a5fa', width=2, stipple='gray50',
            tags='evo_energy'
        )

        # 能量线
        for i in range(8):
            angle = i * math.pi / 4 + progress * math.pi
            start_r = radius
            end_r = radius + 20

            x1 = cx + math.cos(angle) * start_r
            y1 = cy + math.sin(angle) * start_r
            x2 = cx + math.cos(angle) * end_r
            y2 = cy + math.sin(angle) * end_r

            self.canvas.create_line(
                x1, y1, x2, y2,
                fill='#60a5fa', width=1,
                tags='evo_energy'
            )

    def _spawn_burst_particles(self, particle_type: str):
        """生成爆发粒子"""
        cx, cy = self.width / 2, self.height / 2

        for _ in range(15):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 5)

            self.particles.append(Particle(
                x=cx, y=cy,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                life=random.randint(40, 60),
                max_life=60,
                size=random.randint(6, 12),
                color=random.choice(['#fbbf24', '#f472b6', '#a78bfa', '#4ade80']),
                shape=particle_type
            ))

    def _new_form_reveal(self, progress: float):
        """新形态揭示"""
        # 渐显效果
        if progress < 0.3:
            alpha = progress / 0.3
            # 添加揭示光芒
            cx, cy = self.width / 2, self.height / 2
            stipple = self._alpha_to_stipple(int(alpha * 255))
            self.canvas.create_oval(
                cx - 70, cy - 70, cx + 70, cy + 70,
                fill='white', outline='', stipple=stipple,
                tags='evo_reveal'
            )

    def _celebration(self, progress: float):
        """庆祝动画"""
        # 持续生成庆祝粒子
        if random.random() < 0.1:
            cx, cy = self.width / 2, self.height / 2

            for _ in range(3):
                px = cx + random.uniform(-50, 50)
                py = cy + random.uniform(-30, 30)

                self.particles.append(Particle(
                    x=px, y=py,
                    vx=random.uniform(-2, 2),
                    vy=random.uniform(-3, -1),
                    life=random.randint(30, 50),
                    max_life=50,
                    size=random.randint(8, 14),
                    color=random.choice(['#fbbf24', '#f472b6', '#a78bfa', '#4ade80']),
                    shape=random.choice(['star', 'heart', 'sparkle'])
                ))

    def _update_particles(self, elapsed: float):
        """更新粒子"""
        for particle in self.particles[:]:
            # 移动
            particle.x += particle.vx
            particle.y += particle.vy
            particle.rotation += particle.rotation_speed

            # 重力
            particle.vy += 0.1

            # 生命周期
            particle.life -= 1

            if particle.life <= 0:
                self.particles.remove(particle)
                continue

            # 绘制粒子
            self._draw_particle(particle)

    def _draw_particle(self, particle: Particle):
        """绘制粒子"""
        alpha = particle.life / particle.max_life
        stipple = self._alpha_to_stipple(int(alpha * 255))

        size = particle.size * alpha

        if particle.shape == "circle":
            self.canvas.create_oval(
                particle.x - size, particle.y - size,
                particle.x + size, particle.y + size,
                fill=particle.color, outline='', stipple=stipple,
                tags='evo_particle'
            )

        elif particle.shape == "star":
            self.canvas.create_text(
                particle.x, particle.y,
                text='★', fill=particle.color,
                font=('Arial', int(size * 1.5)),
                tags='evo_particle'
            )

        elif particle.shape == "heart":
            self.canvas.create_text(
                particle.x, particle.y,
                text='♥', fill=particle.color,
                font=('Arial', int(size * 1.5)),
                tags='evo_particle'
            )

        elif particle.shape == "diamond":
            points = [
                particle.x, particle.y - size,
                particle.x + size * 0.6, particle.y,
                particle.x, particle.y + size,
                particle.x - size * 0.6, particle.y,
            ]
            self.canvas.create_polygon(
                points, fill=particle.color, outline='',
                stipple=stipple, tags='evo_particle'
            )

        elif particle.shape == "sparkle":
            self.canvas.create_text(
                particle.x, particle.y,
                text='✦', fill=particle.color,
                font=('Arial', int(size * 1.5)),
                tags='evo_particle'
            )

    def _render_pet_state(self, elapsed: float):
        """渲染宠物状态"""
        cx, cy = self.width / 2, self.height / 2

        # 根据动画进度决定显示哪个阶段
        if elapsed < 1000:
            # 显示原形态
            scale = 1.0
            if elapsed > 500:
                # 缩小
                scale = 1.0 - (elapsed - 500) / 500 * 0.5
        elif elapsed < 2000:
            # 过渡期，能量形态
            self._draw_energy_form(cx, cy, elapsed)
            return
        else:
            # 显示新形态
            progress = (elapsed - 2000) / 500
            scale = 0.5 + progress * 0.5
            if scale > 1.0:
                scale = 1.0

        # 简化版宠物轮廓
        if elapsed < 2000:
            self._draw_pet_outline(cx, cy, scale, self.from_stage)
        else:
            self._draw_pet_outline(cx, cy, scale, self.to_stage)

    def _draw_pet_outline(self, cx: float, cy: float, scale: float, stage: int):
        """绘制宠物轮廓"""
        size = 40 * scale

        # 根据阶段调整大小
        stage_scale = 1.0 + stage * 0.05
        size *= stage_scale

        # 身体
        self.canvas.create_oval(
            cx - size, cy - size * 0.8,
            cx + size, cy + size * 0.8,
            fill='#38bdf8', outline='#0ea5e9', width=2,
            tags='evo_pet'
        )

        # 眼睛
        eye_y = cy - size * 0.1
        self.canvas.create_oval(
            cx - size * 0.3, eye_y - size * 0.15,
            cx - size * 0.1, eye_y + size * 0.15,
            fill='#0c4a6e', outline='', tags='evo_pet'
        )
        self.canvas.create_oval(
            cx + size * 0.1, eye_y - size * 0.15,
            cx + size * 0.3, eye_y + size * 0.15,
            fill='#0c4a6e', outline='', tags='evo_pet'
        )

    def _draw_energy_form(self, cx: float, cy: float, elapsed: float):
        """绘制能量形态"""
        progress = (elapsed - 1000) / 1000

        # 能量球
        base_size = 40
        pulse = math.sin(progress * math.pi * 4) * 10
        size = base_size + pulse

        # 多层能量
        colors = ['#fbbf24', '#f472b6', '#a78bfa', '#60a5fa']
        for i, color in enumerate(colors):
            layer_size = size + i * 8
            stipple = ['gray50', 'gray25', 'gray12', 'gray6'][i]
            self.canvas.create_oval(
                cx - layer_size, cy - layer_size,
                cx + layer_size, cy + layer_size,
                fill=color, outline='', stipple=stipple,
                tags='evo_pet'
            )

    def _clear_frame(self):
        """清除上一帧"""
        self.canvas.delete('evo_flash')
        self.canvas.delete('evo_glow')
        self.canvas.delete('evo_energy')
        self.canvas.delete('evo_reveal')
        self.canvas.delete('evo_particle')
        self.canvas.delete('evo_pet')

    def _alpha_to_stipple(self, alpha: int) -> str:
        """将alpha值转换为stipple"""
        if alpha >= 200:
            return ''
        elif alpha >= 150:
            return 'gray25'
        elif alpha >= 100:
            return 'gray50'
        elif alpha >= 50:
            return 'gray75'
        else:
            return 'gray87'

    def _finish(self):
        """完成动画"""
        self.is_playing = False
        self._clear_frame()

        if self.callback:
            self.callback()


class AnimationManager:
    """动画管理器"""

    def __init__(self, canvas: tk.Canvas, width: int, height: int):
        self.canvas = canvas
        self.width = width
        self.height = height

        self.current_animation: Optional[EvolutionAnimation] = None
        self.active_animations: List[Dict] = []

    def play_evolution(self, from_stage: int, to_stage: int, callback: Optional[Callable] = None):
        """播放进化动画"""
        animation = EvolutionAnimation(self.canvas, self.width, self.height)
        animation.start(from_stage, to_stage, callback)
        self.current_animation = animation

    def is_playing(self) -> bool:
        """检查是否有动画正在播放"""
        if self.current_animation:
            return self.current_animation.is_playing
        return False

    def play_idle_animation(self):
        """播放待机动画"""
        # 这里可以添加各种待机动画
        pass

    def play_emote_animation(self, emote: str):
        """播放表情动画"""
        animations = {
            "happy": self._happy_animation,
            "excited": self._excited_animation,
            "love": self._love_animation,
            "sleep": self._sleep_animation,
            "thinking": self._thinking_animation,
        }

        if emote in animations:
            animations[emote]()

    def _happy_animation(self):
        """开心动画"""
        # 简单的跳跃效果
        pass

    def _excited_animation(self):
        """兴奋动画"""
        pass

    def _love_animation(self):
        """喜爱动画"""
        pass

    def _sleep_animation(self):
        """睡眠动画"""
        pass

    def _thinking_animation(self):
        """思考动画"""
        pass

    @staticmethod
    def ease_linear(t: float) -> float:
        """线性缓动"""
        return t

    @staticmethod
    def ease_in(t: float) -> float:
        """缓入"""
        return t * t

    @staticmethod
    def ease_out(t: float) -> float:
        """缓出"""
        return 1 - (1 - t) * (1 - t)

    @staticmethod
    def ease_in_out(t: float) -> float:
        """缓入缓出"""
        return t * t * (3 - 2 * t)

    @staticmethod
    def ease_bounce(t: float) -> float:
        """弹跳缓动"""
        if t < 1/2.75:
            return 7.5625 * t * t
        elif t < 2/2.75:
            t -= 1.5/2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5/2.75:
            t -= 2.25/2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625/2.75
            return 7.5625 * t * t + 0.984375

    @staticmethod
    def ease_elastic(t: float) -> float:
        """弹性缓动"""
        if t == 0 or t == 1:
            return t
        return -math.pow(2, 10 * (t - 1)) * math.sin((t - 1.1) * 5 * math.pi)


if __name__ == "__main__":
    # 测试动画系统
    root = tk.Tk()
    root.title("Evolution Animation Test")
    root.geometry("400x400")

    canvas = tk.Canvas(root, width=400, height=400, bg='#0f172a', highlightthickness=0)
    canvas.pack()

    manager = AnimationManager(canvas, 400, 400)

    def on_evolution_complete():
        print("进化动画完成！")
        canvas.create_text(
            200, 350,
            text="进化完成！",
            fill='#4ade80', font=('Arial', 20, 'bold')
        )

    # 启动进化动画
    manager.play_evolution(0, 5, on_evolution_complete)

    root.mainloop()
