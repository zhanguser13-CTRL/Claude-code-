#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code Pet - Enhanced HD Version

Enhanced with 3D rendering, animations, particles, themes, and improved interactions
"""
import tkinter as tk
import math
import random
import time
import json
import threading
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque

from .config import PetConfig
from .themes import get_theme, ColorScheme

# Import 3D rendering system
try:
    from .render import (
        Renderer3D, BodyPartsManager, get_stage_visuals, get_path_visuals,
        LightingSystem, get_lighting_for_status, AnimationManager
    )
    from .render.evolution_stages import get_stage_for_level, LEVEL_REQUIREMENTS
    from .items import Inventory, EvolutionItemType
    RENDER_3D_AVAILABLE = True
except ImportError:
    RENDER_3D_AVAILABLE = False
    print("3D rendering system not available, using legacy renderer")


class FloatingNumber:
    """浮动数字效果"""

    def __init__(self, x, y, text, color='#4ade80'):
        """初始化浮动数字"""
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 60
        self.max_life = 60
        self.vy = -1.5

    def update(self):
        """更新位置和生命周期"""
        self.y += self.vy
        self.life -= 1
        return self.life > 0

    def get_alpha(self):
        """获取透明度"""
        return min(1.0, self.life / 20)


class Particle:
    """增强的粒子系统"""

    PARTICLE_TYPES = {
        'heart': {'char': '♥', 'color': '#f43f5e'},
        'star': {'char': '★', 'color': '#fbbf24'},
        'sparkle': {'char': '✦', 'color': '#fcd34d'},
        'note': {'char': '♪', 'color': '#c084fc'},
        'circle': {'char': '●', 'color': '#60a5fa'},
        'code': {'chars': ['{', '}', '</>', 'fn', 'var'], 'color': '#34d399'},
        'plus': {'char': '+', 'color': '#4ade80'},
        'xp': {'char': '⭐', 'color': '#fbbf24'},
    }

    def __init__(self, x, y, p_type, theme_colors=None):
        """初始化粒子"""
        self.x = x
        self.y = y
        self.type = p_type
        self.life = random.randint(30, 50)
        self.max_life = self.life
        self.size = random.randint(10, 16)

        # 速度
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-3, -0.5)

        # 颜色渐变
        self.start_color = self._get_color(p_type, theme_colors)
        self.end_color = self._get_fade_color(p_type)

        # 旋转
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-5, 5)

        # 字符
        self.char = self._get_char(p_type)

    def _get_char(self, p_type):
        """获取粒子字符"""
        info = self.PARTICLE_TYPES.get(p_type, self.PARTICLE_TYPES['star'])
        if 'chars' in info:
            return random.choice(info['chars'])
        return info.get('char', '★')

    def _get_color(self, p_type, theme_colors):
        """获取粒子颜色"""
        if theme_colors and p_type == 'star':
            return theme_colors.glow_active
        info = self.PARTICLE_TYPES.get(p_type, {})
        return info.get('color', '#fbbf24')

    def _get_fade_color(self, p_type):
        """获取粒子渐变颜色"""
        if p_type == 'heart':
            return '#fda4af'
        elif p_type == 'star':
            return '#fef3c7'
        return '#e2e8f0'

    def update(self, width, height):
        """更新粒子状态"""
        # 移动
        self.x += self.vx
        self.y += self.vy
        self.rotation += self.rotation_speed

        # 边界反弹
        if self.x < 10:
            self.vx = abs(self.vx) * 0.8
            self.x = 10
        elif self.x > width - 10:
            self.vx = -abs(self.vx) * 0.8
            self.x = width - 10

        if self.y < 10:
            self.vy = abs(self.vy) * 0.8
            self.y = 10

        # 重力
        self.vy += 0.05

        # 生命周期
        self.life -= 1
        return self.life > 0

    def get_alpha(self):
        """获取粒子透明度"""
        return min(1.0, self.life / 15)

    def get_size(self):
        """获取粒子大小"""
        alpha = self.get_alpha()
        return max(6, int(self.size * alpha))


class ClaudeCodePetHD:
    """Claude Code 桌面宠物 - 增强版"""

    def __init__(self):
        # 加载配置
        self.config = PetConfig.load()

        # 加载主题
        self.theme = get_theme(self.config.theme)
        self.colors = self.theme

        # 窗口设置
        self.width = self.config.width
        self.height = self.config.height

        # 拖拽物理
        self.drag_velocity_x = 0
        self.drag_velocity_y = 0
        self.elastic_offset_x = 0
        self.elastic_offset_y = 0

        # 创建窗口
        self.root = tk.Tk()
        self.root.title("")

        # 获取保存的位置
        self.get_saved_position()

        self.root.geometry(f"{self.width}x{self.height}+{self.x}+{self.y}")
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.95)
        self.root.resizable(False, False)
        self.root.overrideredirect(True)

        # 宠物状态
        self.state = {
            'name': self.config.pet_name,
            'mood': 'happy',
            'hunger': 100,
            'happiness': 100,
            'energy': 100,
            'level': 1,
            'xp': 0,
            'xp_to_next': 100,
            'is_sleeping': False,
            'combo': 0,  # 连击计数
            'last_combo_time': time.time(),
            'evolution_stage': 0,  # 0-9 进化阶段
            'evolution_path': 'balanced',  # 进化路径
            'interaction_count': 0,  # 互动计数
            'files_created_session': 0,  # 本次会话创建文件数
            'errors_fixed_session': 0,  # 本次会话修复错误数
            'night_coding_hours': 0,  # 深夜编程小时数
        }

        # Claude Code 实时状态
        self.claude_state = {
            'status': 'idle',
            'current_tool': None,
            'current_file': None,
            'files_created': 0,
            'files_modified': 0,
            'commands_run': 0,
            'errors_count': 0,
            'success_streak': 0,
            'last_activity': None,
            'session_start': datetime.now(),
            'tokens_used': 0,
            'requests_count': 0,
        }

        # 动画状态
        self.is_running = True
        self.animation_frame = 0
        self.last_blink = time.time()
        self.float_offset = 0
        self.float_direction = 1
        self.pulse_phase = 0
        self.breathing_phase = 0

        # 增强的粒子系统
        self.particles = deque(maxlen=self.config.max_particles)
        self.floating_numbers = deque(maxlen=10)

        # 耳朵和尾巴动画
        self.ear_left_angle = 0
        self.ear_right_angle = 0
        self.tail_angle = 0
        self.ear_twitch_timer = 0

        # 拖拽状态
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_last_x = 0
        self.drag_last_y = 0

        # 鼠标追踪
        self.mouse_x = 0
        self.mouse_y = 0

        # 心情计时器
        self.mood_timer = 0
        self.current_mood_duration = random.randint(100, 300)

        # 控制按钮显示
        self.controls_visible = False

        # 表情过渡
        self.current_expression = 'happy'
        self.target_expression = 'happy'
        self.expression_transition = 0

        # 星星背景
        self.stars = []
        for _ in range(20):
            self.stars.append({
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'size': random.randint(1, 2),
                'twinkle_speed': random.uniform(0.02, 0.08),
                'phase': random.uniform(0, math.pi * 2),
            })

        # 状态文件路径
        self.state_file = Path.home() / '.claude-pet-companion' / 'pet_state.json'
        self.activity_file = Path.home() / '.claude-pet-companion' / 'activity.json'
        self.stats_file = Path.home() / '.claude-pet-companion' / 'work_stats.json'

        # 生产力统计
        self.work_stats = {
            'productivity_score': 50,
            'focus_score': 0,
            'streak': {'current': 0, 'best': 0},
            'needs_break': False,
            'flow_state': False,
        }

        # 3D渲染系统
        self.renderer_3d = None
        self.body_parts_manager = None
        self.lighting_system = None
        self.animation_manager = None
        self.inventory = None

        # 记忆系统
        self.memory_manager = None
        self.last_memory_time = None
        self.task_memory_count = 0

        # 活动追踪
        self.last_activity_time = time.time()

        # IPC系统
        self.ipc_enabled = False
        self.ipc_server = None

        # 初始化3D渲染系统
        self._init_3d_system()

        # 初始化记忆系统
        self._init_memory_system()

        # 初始化IPC服务器
        self._init_ipc_server()

        # 创建UI
        self.setup_ui()
        self.setup_events()

        # 启动状态监控
        self.start_state_monitor()

        # 启动动画
        self.start_animation()

        # 启动状态衰减
        self.start_decay()

    def get_saved_position(self):
        """获取保存的位置"""
        state_file = Path.home() / '.claude-pet-companion' / 'pet_window_state.json'
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    data = json.load(f)
                    self.x = data.get('x', 100)
                    self.y = data.get('y', 100)
            except:
                pass

        # 默认位置 - 屏幕右下角
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        if not hasattr(self, 'x'):
            self.x = screen_width - 260
            self.y = screen_height - 320

        # 边缘检测
        self.x = max(0, min(self.x, screen_width - self.width))
        self.y = max(0, min(self.y, screen_height - self.height))

    def _init_3d_system(self):
        """初始化3D渲染系统"""
        if not RENDER_3D_AVAILABLE:
            return

        # 创建3D渲染器
        self.renderer_3d = Renderer3D(self.canvas, self.width, self.height)

        # 创建身体部位管理器
        self.body_parts_manager = BodyPartsManager()

        # 创建光照系统
        self.lighting_system = LightingSystem()
        self.lighting_system.update_time_lighting()

        # 创建动画管理器
        self.animation_manager = AnimationManager(self.canvas, self.width, self.height)

        # 创建物品栏
        self.inventory = Inventory()

        # 记忆系统
        self.memory_manager = None
        self.last_memory_time = None
        self.task_memory_count = 0

        # 应用当前阶段和路径配置
        self._update_render_config()

    def _init_memory_system(self):
        """初始化记忆系统"""
        try:
            from .memories import MemoryManager, MemoryType
            self.memory_manager = MemoryManager()
            self.memory_manager.start_session()
            print("[Memory] 记忆系统已启动")
        except ImportError:
            self.memory_manager = None

    def _remember_activity(self, activity_type, data, context=None):
        """记录活动到记忆系统"""
        if not self.memory_manager:
            return

        try:
            from .memories import MemoryType, MemoryImportance

            # 根据活动类型确定记忆类型
            memory_type_map = {
                'tool_change': MemoryType.TOOL_USE,
                'thinking': MemoryType.THINKING,
                'error': MemoryType.ERROR_OCCURRED,
                'success': MemoryType.SUCCESS,
                'file_edit': MemoryType.FILE_EDIT,
                'milestone': MemoryType.MILESTONE,
            }
            memory_type = memory_type_map.get(activity_type, MemoryType.COMMAND_RUN)

            # 根据活动类型设置重要性
            importance = MemoryImportance.NORMAL
            if activity_type in ['error', 'milestone', 'first_contact']:
                importance = MemoryImportance.HIGH
            elif activity_type == 'success':
                importance = MemoryImportance.HIGH

            # 提取相关文件和工具信息
            tool = context.get('current_tool', '') if context else ''
            related_files = []
            if context and 'current_file' in context:
                related_files = [context['current_file']]

            # 记录到记忆系统
            self.memory_manager.remember_task(
                tool=tool or 'claude-pet',
                input_data={'activity_type': activity_type, 'data': data},
                importance=importance,
                tags=[activity_type],
                files=related_files,
            )

            self.last_memory_time = time.time()
            self.task_memory_count += 1

        except Exception as e:
            print(f"[Memory] 记忆记录失败: {e}")

    def _check_memory_decay(self):
        """检查并处理记忆衰减"""
        if not self.memory_manager:
            return

        try:
            # 检查是否需要衰减（每5分钟检查一次）
            if self.last_memory_time and (time.time() - self.last_memory_time) > 300:
                self.memory_manager.decay_all_memories(days=0.1)  # 轻微衰减
                self.memory_manager.save()
                self.last_memory_time = time.time()
        except Exception as e:
            print(f"[Memory] 记忆衰减检查失败: {e}")

    def _init_ipc_server(self):
        """初始化IPC服务器"""
        if not self.config.daemon_enabled:
            return

        try:
            from .ipc import IPCServer, get_ipc_server
            from .ipc.protocol import MessageType, build_status_payload
            from .daemon import get_daemon_manager

            # 启动守护进程
            daemon = get_daemon_manager()
            if not daemon.start():
                print("[IPC] Warning: Could not acquire daemon lock")
                return

            # 获取IPC服务器实例
            self.ipc_server = get_ipc_server()

            # 设置回调
            self.ipc_server.set_state_callback(self._get_ipc_state)
            self.ipc_server.set_action_callback(self._handle_ipc_action)

            # 设置对话回调
            if self.memory_manager:
                self._setup_conversation_callbacks()

            # 启动服务器
            if self.ipc_server.start():
                self.ipc_enabled = True
                print(f"[IPC] Server started on {self.config.ipc_host}:{self.config.ipc_port}")

                # 启动状态广播
                self._start_state_broadcast()

            else:
                print("[IPC] Failed to start IPC server")
                self.ipc_enabled = False

        except ImportError as e:
            print(f"[IPC] IPC module not available: {e}")
            self.ipc_enabled = False
        except Exception as e:
            print(f"[IPC] Failed to initialize IPC server: {e}")
            self.ipc_enabled = False

    def _get_ipc_state(self) -> dict:
        """获取用于IPC的状态"""
        state = {
            'name': self.state.get('name', self.config.pet_name),
            'level': self.state.get('level', 1),
            'xp': self.state.get('xp', 0),
            'xp_to_next': self.state.get('xp_to_next', 100),
            'hunger': self.state.get('hunger', 100),
            'happiness': self.state.get('happiness', 100),
            'energy': self.state.get('energy', 100),
            'mood': self.state.get('mood', 'happy'),
            'is_sleeping': self.state.get('is_sleeping', False),
            'evolution_stage': self.state.get('evolution_stage', 0),
            'evolution_path': self.state.get('evolution_path', 'balanced'),
        }
        return state

    def _handle_ipc_action(self, action: str, payload: dict) -> dict:
        """处理来自IPC的动作请求"""
        result = {'success': True, 'message': ''}

        if action == 'feed':
            self.feed()
            result['message'] = 'Yummy!'
        elif action == 'play':
            self.play()
            result['message'] = 'Wheee!'
        elif action == 'sleep':
            self.toggle_sleep()
            result['message'] = 'Zzz...' if self.state['is_sleeping'] else 'Wake up!'
        elif action == 'status':
            result['state'] = self._get_ipc_state()
        else:
            result['success'] = False
            result['message'] = f'Unknown action: {action}'

        return result

    def _setup_conversation_callbacks(self):
        """设置对话相关回调"""
        from .memories.conversation_store import get_conversation_store

        try:
            store = get_conversation_store()

            # 开始对话
            def start_conversation(payload):
                title = payload.get('title', 'Untitled')
                tags = payload.get('tags', [])
                conv_id = store.start_conversation(title, tags)
                return {'conversation_id': conv_id, 'title': title}

            # 列出对话
            def list_conversations(payload):
                limit = payload.get('limit', 50)
                return {'conversations': store.list_conversations(limit)}

            # 获取对话
            def get_conversation(payload):
                conv_id = payload.get('conversation_id')
                conv = store.get_conversation(conv_id)
                return conv.to_dict() if conv else None

            # 恢复上下文
            def restore_context(payload):
                from .memories.context_builder import ContextBuilder
                conv_id = payload.get('conversation_id')
                builder = ContextBuilder(store)
                context = builder.build_context(conv_id)
                return {'context': context}

            self.ipc_server.set_conversation_callback('start', start_conversation)
            self.ipc_server.set_conversation_callback('list', list_conversations)
            self.ipc_server.set_conversation_callback('get', get_conversation)
            self.ipc_server.set_conversation_callback('restore', restore_context)

        except Exception as e:
            print(f"[IPC] Failed to setup conversation callbacks: {e}")

    def _start_state_broadcast(self):
        """启动状态广播"""
        def broadcast():
            if self.ipc_enabled and hasattr(self, 'ipc_server'):
                self.ipc_server.broadcast_state(self._get_ipc_state())
            # 每秒广播一次
            if self.is_running:
                self.root.after(1000, broadcast)

        # 启动广播
        broadcast()

    def _shutdown_ipc(self):
        """关闭IPC服务器"""
        if hasattr(self, 'ipc_enabled') and self.ipc_enabled:
            if hasattr(self, 'ipc_server') and self.ipc_server:
                self.ipc_server.stop()

            # 清理守护进程
            try:
                from .daemon import get_daemon_manager
                daemon = get_daemon_manager()
                daemon._cleanup()
            except:
                pass

            print("[IPC] Server stopped")

    def _update_render_config(self):
        """更新渲染配置"""
        if not RENDER_3D_AVAILABLE:
            return

        # 获取当前阶段和路径配置
        stage = get_stage_visuals(self.state['evolution_stage'])
        path = get_path_visuals(self.state['evolution_path'])

        # 应用到身体部位管理器
        self.body_parts_manager.apply_stage_modifications(stage)
        self.body_parts_manager.apply_path_modifications(path)

    def get_render_context(self):
        """获取渲染上下文"""
        if not RENDER_3D_AVAILABLE:
            return None

        from .render.renderer_3d import RenderContext

        stage = get_stage_visuals(self.state['evolution_stage'])
        path = get_path_visuals(self.state['evolution_path'])
        lighting = self.lighting_system.get_current_preset()

        return RenderContext(
            stage=stage,
            path=path,
            lighting=lighting,
            position=(self.width // 2, 130),
            mood=self.state['mood'],
            scale=1.0 + self.state['evolution_stage'] * 0.05,
            mouse_offset=(self.mouse_x - self.width // 2, self.mouse_y - 130)
        )

    def setup_ui(self):
        """创建UI"""
        # 主画布
        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            highlightthickness=0,
            bd=0,
            bg=self.colors.bg_top
        )
        self.canvas.pack(fill='both', expand=True)

        # 绘制背景
        self.draw_background()

        # 绘制宠物
        self.draw_pet()

        # 绘制UI元素
        self.draw_ui()

        # 绘制控制按钮
        self.draw_controls()

        # 绑定悬停
        self.canvas.bind('<Enter>', self.show_controls)
        self.canvas.bind('<Leave>', self.hide_controls)
        self.canvas.bind('<Motion>', self.on_mouse_move)

    def draw_background(self):
        """绘制增强背景"""
        c = self.canvas
        w, h = self.width, self.height

        # 平滑渐变背景
        steps = 50
        for i in range(steps):
            ratio = i / steps
            r1, g1, b1 = self._hex_to_rgb(self.colors.bg_top)
            r2, g2, b2 = self._hex_to_rgb(self.colors.bg_bottom)
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            color = f'#{r:02x}{g:02x}{b:02x}'
            y_start = int(i * h / steps)
            y_end = int((i + 1) * h / steps)
            c.create_rectangle(0, y_start, w, y_end, fill=color, outline='', tags='bg')

        # 发光网格
        grid_color = self.colors.bg_grid
        for i in range(0, w, 30):
            alpha = 0.3 + 0.2 * math.sin(i * 0.05)
            c.create_line(i, 0, i, h, fill=grid_color, width=1, stipple='gray25', tags='bg_grid')
        for i in range(0, h, 30):
            c.create_line(0, i, w, i, fill=grid_color, width=1, stipple='gray25', tags='bg_grid')

        # 星星 (单独tag以便动画)
        self.star_items = []
        for star in self.stars:
            item = c.create_oval(
                star['x'], star['y'],
                star['x'] + star['size'], star['y'] + star['size'],
                fill='#ffffff', outline='',
                tags='stars'
            )
            self.star_items.append(item)

        # 底部状态栏 (毛玻璃效果)
        self.status_bar_bg = c.create_rectangle(
            8, h - 68, w - 8, h - 8,
            fill=self.colors.ui_bg, outline=self.colors.ui_border, width=1,
            stipple='gray75', tags='ui_bg'
        )

    def _hex_to_rgb(self, hex_color):
        """转换hex颜色为RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def draw_pet(self):
        """绘制宠物主体"""
        # 使用3D渲染器（如果可用）
        if RENDER_3D_AVAILABLE and self.renderer_3d:
            self.draw_pet_3d()
            return

        # 旧版2D渲染
        self.draw_pet_legacy()

    def draw_pet_3d(self):
        """使用3D渲染器绘制宠物"""
        c = self.canvas
        cx, cy = self.width // 2, 130

        # 保存原始中心
        self.pet_center = (cx, cy)
        self.body_cx, self.body_cy = cx, cy

        # 更新渲染器的鼠标位置
        if self.renderer_3d:
            self.renderer_3d.update_mouse_position(self.mouse_x, self.mouse_y)

        # 获取渲染上下文并渲染
        context = self.get_render_context()
        if context and self.renderer_3d:
            self.renderer_3d.render_pet(context)

    def draw_pet_legacy(self):
        """旧版2D渲染（保持兼容性）"""
        c = self.canvas
        cx, cy = self.width // 2, 100

        # 身体尺寸
        body_size = 100

        # 保存原始中心
        self.pet_center = (cx, cy)
        self.body_cx, self.body_cy = cx, cy

        # 外发光层
        for i in range(3):
            glow_size = 8 + i * 6
            tag = f'pet_glow_{i}'
            c.create_oval(
                cx - body_size//2 - glow_size//2, cy - body_size//2 - glow_size//2,
                cx + body_size//2 + glow_size//2, cy + body_size//2 + glow_size//2,
                outline=self.colors.glow_idle, width=2,
                stipple='gray12', tags=tag
            )

        # 阴影 (随浮动变化)
        self.pet_shadow = c.create_oval(
            cx - 40, cy + 45,
            cx + 40, cy + 55,
            fill='#020617', outline='', stipple='gray50',
            tags='pet_shadow'
        )

        # 尾巴
        self.tail_points = [
            cx - 10, cy + 30,
            cx - 25, cy + 35,
            cx - 30, cy + 20,
            cx - 20, cy + 15,
        ]
        self.pet_tail = c.create_polygon(
            self.tail_points, fill=self.colors.pet_secondary,
            outline=self.colors.pet_tertiary, width=1, smooth=True,
            tags='pet_tail'
        )

        # 身体层
        body_colors = [self.colors.pet_primary, self.colors.pet_secondary, self.colors.pet_tertiary]
        for i, color in enumerate(reversed(body_colors)):
            offset = i * 1.5
            c.create_oval(
                cx - body_size//2 + offset, cy - body_size//2 + offset,
                cx + body_size//2 - offset, cy + body_size//2 - offset,
                fill=color, outline='', tags='pet_body'
            )

        # 肚子
        c.create_oval(
            cx - 30, cy - 5,
            cx + 30, cy + 35,
            fill=self.colors.pet_belly, outline='', tags='pet_belly'
        )

        # 高光
        self.pet_highlight = c.create_oval(
            cx - 20, cy + 5,
            cx + 20, cy + 25,
            fill=self.colors.pet_highlight, outline='', stipple='gray75',
            tags='pet_highlight'
        )

        # 左耳
        self.ear_left_points = [
            cx - 35, cy - 35,
            cx - 45, cy - 55,
            cx - 25, cy - 45,
        ]
        self.pet_ear_left = c.create_polygon(
            self.ear_left_points, fill=self.colors.pet_primary,
            outline=self.colors.pet_tertiary, width=1, smooth=True,
            tags='pet_ear_left'
        )

        # 右耳
        self.ear_right_points = [
            cx + 35, cy - 35,
            cx + 45, cy - 55,
            cx + 25, cy - 45,
        ]
        self.pet_ear_right = c.create_polygon(
            self.ear_right_points, fill=self.colors.pet_primary,
            outline=self.colors.pet_tertiary, width=1, smooth=True,
            tags='pet_ear_right'
        )

        # 绘制面部
        self.draw_face()

    def draw_face(self):
        """绘制面部表情"""
        c = self.canvas
        cx, cy = self.pet_center
        mood = self.state['mood']
        status = self.claude_state['status']

        # 清除旧面部
        c.delete('face')

        eye_y = cy - 12

        # 根据状态和心情选择表情
        if status == 'thinking':
            self._draw_thinking_face(cx, eye_y, cy)
        elif status == 'working':
            self._draw_working_face(cx, eye_y, cy)
        elif status == 'error':
            self._draw_error_face(cx, eye_y, cy)
        elif status == 'success':
            self._draw_success_face(cx, eye_y, cy)
        elif mood == 'sleepy':
            self._draw_sleepy_face(cx, eye_y, cy)
        elif mood == 'surprised':
            self._draw_surprised_face(cx, eye_y, cy)
        elif mood == 'proud':
            self._draw_proud_face(cx, eye_y, cy)
        elif mood == 'confused':
            self._draw_confused_face(cx, eye_y, cy)
        elif mood == 'excited':
            self._draw_excited_face(cx, eye_y, cy)
        else:
            self._draw_happy_face(cx, eye_y, cy)

        # 天线
        self._draw_antenna(cx, cy)

        # 状态指示器
        self._draw_status_indicator(cx, cy)

    def _draw_happy_face(self, cx, eye_y, cy):
        """开心表情"""
        c = self.canvas

        # 计算鼠标方向偏移
        eye_offset = self._get_eye_offset(cx, eye_y)

        # 笑眼
        c.create_line(cx-20+eye_offset, eye_y-6, cx-12+eye_offset, eye_y,
                     fill='#0c4a6e', width=2.5, capstyle=tk.ROUND, tags='face')
        c.create_line(cx-10+eye_offset, eye_y-3, cx-7+eye_offset, eye_y,
                     fill='#0c4a6e', width=2.5, capstyle=tk.ROUND, tags='face')
        c.create_line(cx+7+eye_offset, eye_y, cx+10+eye_offset, eye_y-3,
                     fill='#0c4a6e', width=2.5, capstyle=tk.ROUND, tags='face')
        c.create_line(cx+12+eye_offset, eye_y, cx+20+eye_offset, eye_y-6,
                     fill='#0c4a6e', width=2.5, capstyle=tk.ROUND, tags='face')

        # 大笑嘴
        c.create_arc(cx-12, cy+5, cx+12, cy+18, start=0, extent=180,
                    style='arc', outline='#f472b6', width=3, tags='face')

        # 腮红
        c.create_oval(cx-35, cy-2, cx-22, cy+10, fill=self.colors.blush_color,
                     outline='', stipple='gray50', tags='face')
        c.create_oval(cx+22, cy-2, cx+35, cy+10, fill=self.colors.blush_color,
                     outline='', stipple='gray50', tags='face')

    def _draw_surprised_face(self, cx, eye_y, cy):
        """惊讶表情"""
        c = self.canvas

        # 睁大的眼睛
        c.create_oval(cx-18, eye_y-8, cx-8, eye_y+4, fill='#0c4a6e', outline='', tags='face')
        c.create_oval(cx+8, eye_y-8, cx+18, eye_y+4, fill='#0c4a6e', outline='', tags='face')
        c.create_oval(cx-15, eye_y-5, cx-11, eye_y, fill='#ffffff', outline='', tags='face')
        c.create_oval(cx+11, eye_y-5, cx+15, eye_y, fill='#ffffff', outline='', tags='face')
        c.create_oval(cx-13, eye_y-2, cx-12, eye_y-1, fill='#0c4a6e', outline='', tags='face')
        c.create_oval(cx+12, eye_y-2, cx+13, eye_y-1, fill='#0c4a6e', outline='', tags='face')

        # 张开的嘴
        c.create_oval(cx-6, cy+6, cx+6, cy+14, fill='#1e293b', outline='#f472b6', width=2, tags='face')

        # 腮红
        c.create_oval(cx-32, cy, cx-22, cy+8, fill='#fde68a', outline='', stipple='gray75', tags='face')
        c.create_oval(cx+22, cy, cx+32, cy+8, fill='#fde68a', outline='', stipple='gray75', tags='face')

    def _draw_excited_face(self, cx, eye_y, cy):
        """兴奋表情"""
        c = self.canvas

        # 闪闪眼
        c.create_text(cx-15, eye_y-2, text='✦', fill='#fbbf24', font=('Arial', 14), tags='face')
        c.create_text(cx+15, eye_y-2, text='✦', fill='#fbbf24', font=('Arial', 14), tags='face')

        # 超大笑容
        c.create_arc(cx-15, cy+5, cx+15, cy+22, start=0, extent=180,
                    style='arc', outline='#f472b6', width=3, tags='face')

        # 庆祝符号
        c.create_text(cx-35, cy-30, text='✨', font=('Arial', 10), tags='face')
        c.create_text(cx+35, cy-30, text='✨', font=('Arial', 10), tags='face')

        # 超级腮红
        c.create_oval(cx-38, cy-3, cx-18, cy+12, fill='#fda4af', outline='', stipple='gray25', tags='face')
        c.create_oval(cx+18, cy-3, cx+38, cy+12, fill='#fda4af', outline='', stipple='gray25', tags='face')

    def _draw_proud_face(self, cx, eye_y, cy):
        """得意表情"""
        c = self.canvas

        # 略微眯眼
        c.create_line(cx-20, eye_y-3, cx-10, eye_y-1, fill='#0c4a6e', width=2.5, tags='face')
        c.create_line(cx+10, eye_y-1, cx+20, eye_y-3, fill='#0c4a6e', width=2.5, tags='face')

        # 自信的微笑
        c.create_line(cx-8, cy+10, cx+8, cy+8, fill='#f472b6', width=2, capstyle=tk.ROUND, tags='face')

        # 眉毛上扬
        c.create_line(cx-20, eye_y-10, cx-12, eye_y-8, fill='#0c4a6e', width=2, tags='face')
        c.create_line(cx+12, eye_y-8, cx+20, eye_y-10, fill='#0c4a6e', width=2, tags='face')

    def _draw_confused_face(self, cx, eye_y, cy):
        """困惑表情"""
        c = self.canvas

        # 一高一低的眼睛
        c.create_oval(cx-18, eye_y-4, cx-10, eye_y+4, fill='#0c4a6e', outline='', tags='face')
        c.create_oval(cx+10, eye_y-6, cx+18, eye_y+2, fill='#0c4a6e', outline='', tags='face')
        c.create_oval(cx-15, eye_y-1, cx-13, eye_y+1, fill='#ffffff', outline='', tags='face')
        c.create_oval(cx+13, eye_y-3, cx+15, eye_y-1, fill='#ffffff', outline='', tags='face')

        # 歪嘴
        c.create_line(cx-6, cy+8, cx+6, cy+12, fill='#64748b', width=2, capstyle=tk.ROUND, tags='face')

        # 问号
        c.create_text(cx+35, cy-35, text='?', fill='#fbbf24', font=('Arial', 14, 'bold'), tags='face')

    def _draw_thinking_face(self, cx, eye_y, cy):
        """思考表情"""
        c = self.canvas

        eye_offset = math.sin(time.time() * 3) * 2

        c.create_oval(cx-18+eye_offset, eye_y-6, cx-10+eye_offset, eye_y+2,
                     fill='#0c4a6e', outline='', tags='face')
        c.create_oval(cx+10+eye_offset, eye_y-6, cx+18+eye_offset, eye_y+2,
                     fill='#0c4a6e', outline='', tags='face')
        c.create_oval(cx-16+eye_offset, eye_y-4, cx-12+eye_offset, eye_y,
                     fill='#ffffff', outline='', tags='face')
        c.create_oval(cx+12+eye_offset, eye_y-4, cx+16+eye_offset, eye_y,
                     fill='#ffffff', outline='', tags='face')

        c.create_oval(cx-5, cy+8, cx+5, cy+13, fill='#cbd5e1', outline='', tags='face')

        c.create_oval(cx+30, cy-40, cx+45, cy-25, fill='#fef3c7',
                     outline='#fbbf24', width=2, tags='face')
        c.create_text(cx+37, cy-32, text='?', fill='#f59e0b',
                     font=('Arial', 12, 'bold'), tags='face')

    def _draw_working_face(self, cx, eye_y, cy):
        """工作表情"""
        c = self.canvas

        c.create_oval(cx-20, eye_y-7, cx-8, eye_y+5, fill='#0c4a6e', outline='', tags='face')
        c.create_oval(cx+8, eye_y-7, cx+20, eye_y+5, fill='#0c4a6e', outline='', tags='face')
        c.create_oval(cx-17, eye_y-4, cx-11, eye_y+2, fill='#ffffff', outline='', tags='face')
        c.create_oval(cx+11, eye_y-4, cx+17, eye_y+2, fill='#ffffff', outline='', tags='face')
        c.create_oval(cx-14, eye_y-1, cx-12, eye_y+1, fill='#0c4a6e', outline='', tags='face')
        c.create_oval(cx+12, eye_y-1, cx+14, eye_y+1, fill='#0c4a6e', outline='', tags='face')

        c.create_line(cx-6, cy+10, cx+6, cy+10, fill='#64748b', width=2, capstyle=tk.ROUND, tags='face')
        c.create_text(cx+32, cy-25, text='💧', font=('Arial', 10), tags='face')

    def _draw_error_face(self, cx, eye_y, cy):
        """错误表情"""
        c = self.canvas

        c.create_line(cx-18, eye_y-6, cx-10, eye_y+2, fill='#dc2626', width=2, tags='face')
        c.create_line(cx-10, eye_y-6, cx-18, eye_y+2, fill='#dc2626', width=2, tags='face')
        c.create_line(cx+10, eye_y-6, cx+18, eye_y+2, fill='#dc2626', width=2, tags='face')
        c.create_line(cx+18, eye_y-6, cx+10, eye_y+2, fill='#dc2626', width=2, tags='face')

        c.create_line(cx-8, cy+12, cx+8, cy+8, fill='#64748b', width=2, capstyle=tk.ROUND, tags='face')
        c.create_text(cx+35, cy-30, text='😵', font=('Arial', 14), tags='face')

        c.create_oval(cx-38, cy-5, cx-20, cy+12, fill='#fecaca', outline='', stipple='gray50', tags='face')
        c.create_oval(cx+20, cy-5, cx+38, cy+12, fill='#fecaca', outline='', stipple='gray50', tags='face')

    def _draw_success_face(self, cx, eye_y, cy):
        """成功表情"""
        c = self.canvas

        c.create_text(cx-15, eye_y-2, text='★', fill='#fbbf24', font=('Arial', 14), tags='face')
        c.create_text(cx+15, eye_y-2, text='★', fill='#fbbf24', font=('Arial', 14), tags='face')
        c.create_arc(cx-15, cy+5, cx+15, cy+20, start=0, extent=180,
                    style='arc', outline='#22c55e', width=3, tags='face')

        for _ in range(3):
            self.add_particle('star')

        c.create_oval(cx-38, cy-3, cx-18, cy+12, fill='#86efac', outline='', stipple='gray25', tags='face')
        c.create_oval(cx+18, cy-3, cx+38, cy+12, fill='#86efac', outline='', stipple='gray25', tags='face')

    def _draw_sleepy_face(self, cx, eye_y, cy):
        """睡眠表情"""
        c = self.canvas

        c.create_line(cx-20, eye_y-2, cx-10, eye_y-2, fill='#475569', width=2, tags='face')
        c.create_line(cx+10, eye_y-2, cx+20, eye_y-2, fill='#475569', width=2, tags='face')
        c.create_oval(cx-5, cy+8, cx+5, cy+13, fill='#cbd5e1', outline='', tags='face')
        c.create_text(cx+35, cy-35, text='Z', fill='#94a3b8', font=('Arial', 10), tags='face')
        c.create_text(cx+42, cy-45, text='z', fill='#94a3b8', font=('Arial', 8), tags='face')
        c.create_text(cx+48, cy-53, text='z', fill='#94a3b8', font=('Arial', 6), tags='face')

    def _get_eye_offset(self):
        """计算眼睛跟随鼠标的偏移"""
        if not hasattr(self, 'pet_center'):
            return 0

        cx, cy = self.pet_center
        dx = self.mouse_x - cx
        dy = self.mouse_y - (cy - 12)

        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 0:
            max_offset = 3
            offset = min(max_offset, dist / 50)
            return (dx / dist) * offset
        return 0

    def _draw_antenna(self, cx, cy):
        """绘制天线"""
        c = self.canvas
        status = self.claude_state['status']

        colors = {
            'idle': self.colors.antenna_bulb_idle,
            'thinking': self.colors.antenna_bulb_thinking,
            'working': self.colors.antenna_bulb_working,
            'error': self.colors.antenna_bulb_error,
            'success': self.colors.status_success,
        }
        bulb_color = colors.get(status, self.colors.antenna_bulb_idle)

        c.create_line(cx, cy-55, cx, cy-68, fill='#bae6fd', width=3, tags='face')

        pulse = math.sin(self.pulse_phase) * 3
        c.create_oval(cx-6+pulse, cy-74+pulse, cx+6-pulse, cy-62-pulse,
                     fill=bulb_color, outline='#ffffff', width=1, tags='face')

    def _draw_status_indicator(self, cx, cy):
        """绘制状态指示器"""
        c = self.canvas
        status = self.claude_state['status']

        status_texts = {
            'idle': 'Idle',
            'thinking': 'Thinking...',
            'working': 'Working',
            'error': 'Error!',
            'success': 'Success!',
        }

        c.create_text(cx, cy-82, text=status_texts.get(status, 'Idle'),
                     fill=self.colors.ui_text_dim, font=('Segoe UI', 8), tags='status_text')

    def draw_ui(self):
        """绘制UI元素"""
        c = self.canvas
        w, h = self.width, self.height

        # 等级
        self.level_badge = c.create_text(
            12, 12,
            text=f'Lv.{self.state["level"]}',
            fill=self.colors.ui_text,
            font=('Segoe UI Semibold', 11, 'bold'),
            anchor='w',
            tags='ui'
        )

        # XP 条背景
        c.create_rectangle(
            12, 28, 80, 34,
            fill=self.colors.bg_bottom, outline=self.colors.ui_border, width=1,
            tags='ui_bg'
        )

        # XP 条 (带阈值颜色)
        xp_ratio = self.state['xp'] / self.state['xp_to_next']
        xp_color = self._get_bar_color(self.state['xp'], self.state['xp_to_next'])
        self.xp_bar = c.create_rectangle(
            12, 28, 12 + int(68 * xp_ratio), 34,
            fill=xp_color, outline='', width=0,
            tags='ui'
        )

        # XP 文字
        self.xp_text = c.create_text(
            85, 31,
            text=f'{self.state["xp"]}/{self.state["xp_to_next"]} XP',
            fill=self.colors.ui_text_dim,
            font=('Segoe UI', 7),
            anchor='w',
            tags='ui'
        )

        # 状态指示灯
        self.status_light = c.create_oval(
            w-22, 10, w-10, 22,
            fill=self.colors.status_idle, outline=self.colors.ui_text, width=1,
            tags='ui'
        )

        # Claude 状态
        self.claude_status = c.create_text(
            w//2, h-58,
            text='● Idle',
            fill=self.colors.ui_text_dim,
            font=('Consolas', 9),
            tags='ui'
        )

        # 活动统计 - 增强版显示生产力
        self.activity_text = c.create_text(
            w//2, h-42,
            text=f'📁 {self.claude_state["files_created"]}+{self.claude_state["files_modified"]} | 💻 {self.claude_state["commands_run"]}',
            fill=self.colors.ui_text_dim,
            font=('Segoe UI', 8),
            tags='ui'
        )

        # 生产力评分条
        c.create_rectangle(
            12, 42, w-12, 46,
            fill=self.colors.bg_bottom, outline=self.colors.ui_border, width=1,
            tags='ui_bg'
        )
        self.productivity_bar = c.create_rectangle(
            12, 42, 12, 46,
            fill=self.colors.bar_high, outline='', width=0,
            tags='ui'
        )

        # 连击显示
        self.combo_text = c.create_text(
            w-12, 50,
            text='',
            fill=self.colors.glow_active,
            font=('Segoe UI Semibold', 8),
            anchor='e',
            tags='ui'
        )

        # 当前工具/文件
        self.tool_text = c.create_text(
            w//2, h-26,
            text='',
            fill='#3b82f6',
            font=('Consolas', 8),
            tags='ui'
        )

        # 时间
        self.time_text = c.create_text(
            w-12, h-14,
            text='',
            fill=self.colors.ui_text_dim,
            font=('Consolas', 8),
            anchor='e',
            tags='ui'
        )

        # 心情显示
        mood_icons = {
            'happy': '😊',
            'excited': '🎉',
            'love': '😍',
            'worried': '😟',
            'sleepy': '😴',
            'idle': '😌',
            'surprised': '😲',
            'proud': '😏',
            'confused': '😕',
        }
        mood_icon = mood_icons.get(self.state['mood'], '😊')
        self.mood_indicator = c.create_text(
            20, h-14,
            text=f'{mood_icon}',
            font=('Segoe UI', 10),
            anchor='w',
            tags='ui'
        )

    def _get_bar_color(self, value, max_value):
        """根据值获取状态条颜色"""
        ratio = value / max_value if max_value > 0 else 0
        if ratio >= 0.6:
            return self.colors.bar_high
        elif ratio >= 0.3:
            return self.colors.bar_medium
        else:
            return self.colors.bar_low

    def load_work_stats(self):
        """加载生产力统计"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.work_stats = json.load(f)

                # 检查是否需要休息提醒
                if self.work_stats.get('needs_break') and not getattr(self, 'break_reminded', False):
                    self.break_reminded = True
                    self.show_break_notification()
                elif not self.work_stats.get('needs_break'):
                    self.break_reminded = False

                # 心流状态检测
                if self.work_stats.get('focus_score', 0) >= 80:
                    if not self.work_stats.get('flow_state'):
                        self.work_stats['flow_state'] = True
                        # 心流状态粒子效果
                        if self.animation_frame % 30 == 0:
                            self.add_particle('sparkle')
                else:
                    self.work_stats['flow_state'] = False

            except (json.JSONDecodeError, KeyError):
                pass

    def draw_controls(self):
        """绘制控制按钮"""
        c = self.canvas
        w = self.width

        self.close_btn = c.create_oval(
            w-36, 4, w-20, 20,
            fill='#ef4444', outline=self.colors.ui_text, width=1,
            state='hidden', tags='controls'
        )
        c.create_text(w-28, 12, text='✕', fill=self.colors.ui_text, font=('Segoe UI', 8, 'bold'),
                     state='hidden', tags='controls')

        self.menu_btn = c.create_oval(
            20, 4, 36, 20,
            fill='#3b82f6', outline=self.colors.ui_text, width=1,
            state='hidden', tags='controls'
        )
        c.create_text(28, 12, text='≡', fill=self.colors.ui_text, font=('Segoe UI', 10, 'bold'),
                     state='hidden', tags='controls')

        c.tag_bind('controls', '<Button-1>', self.on_control_click)

    def show_controls(self, event=None):
        """显示控制按钮"""
        self.controls_visible = True
        self.canvas.itemconfig('controls', state='normal')

    def hide_controls(self, event=None):
        """隐藏控制按钮"""
        self.controls_visible = False
        self.canvas.itemconfig('controls', state='hidden')

    def on_control_click(self, event):
        """处理控制按钮点击"""
        w = self.width
        x, y = event.x, event.y

        if w-36 <= x <= w-20 and 4 <= y <= 20:
            self.do_quit()
        elif 20 <= x <= 36 and 4 <= y <= 20:
            self.show_menu()

    def setup_events(self):
        """设置事件绑定"""
        self.canvas.bind('<Button-1>', self.on_drag_start)
        self.canvas.bind('<B1-Motion>', self.on_drag_motion)
        self.canvas.bind('<ButtonRelease-1>', self.on_drag_end)
        self.canvas.bind('<Double-Button-1>', self.on_double_click)
        self.canvas.bind('<Button-3>', self.show_menu)

    def on_mouse_move(self, event):
        """处理鼠标移动（用于眼睛跟随）"""
        self.mouse_x = event.x
        self.mouse_y = event.y

    def on_drag_start(self, event):
        """开始拖拽"""
        if self.controls_visible:
            w = self.width
            if (20 <= event.x <= 36 and 4 <= event.y <= 20) or (self.width-36 <= event.x <= self.width-20 and 4 <= event.y <= 20):
                return

        self.dragging = True
        self.drag_start_x = event.x_root - self.root.winfo_x()
        self.drag_start_y = event.y_root - self.root.winfo_y()
        self.drag_last_x = event.x_root
        self.drag_last_y = event.y_root
        self.drag_velocity_x = 0
        self.drag_velocity_y = 0

        # 拖拽时改变表情
        self.state['mood'] = 'surprised'
        self.draw_face()

    def on_drag_motion(self, event):
        """处理拖拽移动"""
        if self.dragging:
            # 计算速度
            self.drag_velocity_x = event.x_root - self.drag_last_x
            self.drag_velocity_y = event.y_root - self.drag_last_y
            self.drag_last_x = event.x_root
            self.drag_last_y = event.y_root

            x = event.x_root - self.drag_start_x
            y = event.y_root - self.drag_start_y

            # 边缘检测
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()

            x = max(0, min(x, screen_width - self.width))
            y = max(0, min(y, screen_height - self.height))

            # 弹性偏移
            self.elastic_offset_x = (event.x_root - self.drag_start_x) - x
            self.elastic_offset_y = (event.y_root - self.drag_start_y) - y

            self.root.geometry(f"+{x}+{y}")

    def on_drag_end(self, event):
        """结束拖拽"""
        self.dragging = False
        self.save_position()

        # 回弹效果
        if abs(self.elastic_offset_x) > 5 or abs(self.elastic_offset_y) > 5:
            self.apply_bounce_effect()

        # 恢复表情
        self.state['mood'] = 'happy'
        self.draw_face()

    def apply_bounce_effect(self):
        """应用回弹效果"""
        cx, cy = self.pet_center
        for _ in range(3):
            offset = 5
            self.canvas.move('pet_body', 0, -offset)
            self.canvas.move('pet_belly', 0, -offset)
            self.canvas.move('pet_highlight', 0, -offset)
            self.canvas.move('face', 0, -offset)
            self.root.update()
            time.sleep(0.03)

            self.canvas.move('pet_body', 0, offset)
            self.canvas.move('pet_belly', 0, offset)
            self.canvas.move('pet_highlight', 0, offset)
            self.canvas.move('face', 0, offset)
            self.root.update()
            time.sleep(0.03)

    def on_double_click(self, event):
        """双击互动"""
        self.state['happiness'] = min(100, self.state['happiness'] + 10)
        self.state['mood'] = random.choice(['happy', 'excited', 'love'])

        # 跳跃动画
        for i in range(3):
            y = self.root.winfo_y()
            self.root.geometry(f"+{self.root.winfo_x()}+{y - 12}")
            self.root.update()
            time.sleep(0.06)
            self.root.geometry(f"+{self.root.winfo_x()}+{y + 12}")
            self.root.update()
            time.sleep(0.06)

        for _ in range(5):
            self.add_particle('heart')

        self.draw_face()

        self.root.after(2000, lambda: self._set_mood_and_draw('idle'))

    def _set_mood_and_draw(self, mood):
        """设置心情并重绘"""
        self.state['mood'] = mood
        self.draw_face()

    def show_menu(self, event=None):
        if event:
            x, y = event.x_root, event.y_root
        else:
            x, y = self.root.winfo_x() + 40, self.root.winfo_y() + 40

        menu = tk.Menu(self.root, tearoff=0,
                      bg=self.colors.ui_bg, fg=self.colors.ui_text,
                      activebackground='#3b82f6',
                      activeforeground='white',
                      font=('Segoe UI', 9),
                      borderwidth=0,
                      relief='flat')

        menu.add_command(label="🍖 喂食 (+30 饱食)", command=self.feed)
        menu.add_command(label="🎾 玩耍 (+25 快乐)", command=self.play)
        menu.add_command(label="❤️ 互动 (+10 快乐)", command=self.interact)
        menu.add_separator()
        menu.add_command(label="😴 睡眠/醒来", command=self.toggle_sleep)
        menu.add_separator()
        menu.add_command(label="📊 详细状态", command=self.show_status)
        if RENDER_3D_AVAILABLE:
            menu.add_command(label="🎒 物品栏", command=self.show_inventory)
            # 显示当前阶段和路径
            from .render.evolution_stages import get_stage_visuals
            stage_info = get_stage_visuals(self.state['evolution_stage'])
            menu.add_command(label=f"🧬 进化: {stage_info.name} ({self.state['evolution_path'].title()})", state='disabled')
        menu.add_separator()
        menu.add_command(label="🎨 主题", command=self.show_theme_menu)
        menu.add_separator()
        menu.add_command(label="❌ 退出", command=self.do_quit)

        menu.post(x, y)

    def show_theme_menu(self):
        """显示主题选择菜单"""
        x, y = self.root.winfo_x() + 40, self.root.winfo_y() + 40

        menu = tk.Menu(self.root, tearoff=0,
                      bg=self.colors.ui_bg, fg=self.colors.ui_text,
                      activebackground='#3b82f6',
                      activeforeground='white',
                      font=('Segoe UI', 9))

        from .themes import list_themes
        for theme in list_themes():
            menu.add_command(label=f"● {theme.title()}", command=lambda t=theme: self.change_theme(t))

        menu.post(x, y)

    def change_theme(self, theme_name):
        """更改主题"""
        self.config.theme = theme_name
        self.config.save()

        # 重新绘制
        self.colors = get_theme(theme_name)
        self.canvas.delete('all')
        self.draw_background()
        self.draw_pet()
        self.draw_ui()
        self.draw_controls()

        # 更新光照系统
        if RENDER_3D_AVAILABLE and self.lighting_system:
            self.lighting_system.update_time_lighting()

    def feed(self):
        """喂食"""
        self.state['hunger'] = min(100, self.state['hunger'] + 30)
        self.state['happiness'] = min(100, self.state['happiness'] + 5)
        self.add_xp(10)
        self.state['mood'] = 'happy'
        self.draw_face()
        self.update_ui()

    def play(self):
        """玩耍"""
        self.state['happiness'] = min(100, self.state['happiness'] + 25)
        self.state['energy'] = max(0, self.state['energy'] - 10)
        self.add_xp(15)
        self.state['mood'] = 'excited'

        for _ in range(6):
            self.add_particle('star')

        self.draw_face()
        self.update_ui()

        self.root.after(2000, lambda: self._set_mood_and_draw('idle'))

    def interact(self):
        """互动"""
        self.state['happiness'] = min(100, self.state['happiness'] + 10)
        self.state['mood'] = 'love'
        self.state['interaction_count'] += 1

        # 检查互动奖励（友谊徽章）
        if RENDER_3D_AVAILABLE and self.inventory:
            if self.state['interaction_count'] % 50 == 0:
                self.inventory.add_item(EvolutionItemType.FRIENDSHIP_BADGE)
                self.show_item_notification(EvolutionItemType.FRIENDSHIP_BADGE)

        for _ in range(5):
            self.add_particle('heart')

        self.draw_face()
        self.update_ui()

        self.root.after(2000, lambda: self._set_mood_and_draw('idle'))

    def toggle_sleep(self):
        """切换睡眠"""
        self.state['is_sleeping'] = not self.state['is_sleeping']
        if self.state['is_sleeping']:
            self.state['energy'] = min(100, self.state['energy'] + 30)
            self.state['mood'] = 'sleepy'
            self.claude_state['status'] = 'idle'
        else:
            self.state['mood'] = 'idle'
        self.draw_face()

    def show_status(self):
        """显示详细状态"""
        status = tk.Toplevel(self.root)
        status.geometry("260x200")
        bg = self.colors.ui_bg
        status.configure(bg=bg)
        status.attributes('-topmost', True)
        status.overrideredirect(True)

        pet_x = self.root.winfo_x()
        pet_y = self.root.winfo_y()
        status.geometry(f"260x200+{pet_x + self.width + 5}+{pet_y}")

        c = tk.Canvas(status, width=260, height=200, bg=bg, highlightthickness=0)
        c.pack(fill='both', expand=True)

        info = f"""  🤖 Claude Pet Enhanced

  等级: {self.state['level']}
  经验: {self.state['xp']} / {self.state['xp_to_next']}

  🍖 饱食度: {self.state['hunger']}/100
  😊 快乐值: {self.state['happiness']}/100
  ⚡ 能量: {self.state['energy']}/100

  状态: {self.claude_state['status'].title()}
  文件: {self.claude_state['files_created']}+{self.claude_state['files_modified']}
  命令: {self.claude_state['commands_run']}
"""

        c.create_text(15, 15, text=info, anchor='nw', fill=self.colors.ui_text, font=('Consolas', 10))

        def close(): status.destroy()
        c.create_rectangle(230, 5, 255, 25, fill='#ef4444', outline='')
        c.create_text(242, 15, text='✕', fill='white', font=('Arial', 8, 'bold'))
        c.bind('<Button-1>', lambda e: close() if 230 < e.x < 255 and 5 < e.y < 25 else None)

        status.after(4000, close)

    def show_break_notification(self):
        """显示休息提醒通知"""
        notification = tk.Toplevel(self.root)
        notification.geometry("200x80")
        bg = self.colors.ui_bg
        notification.configure(bg=bg)
        notification.attributes('-topmost', True)
        notification.overrideredirect(True)

        pet_x = self.root.winfo_x()
        pet_y = self.root.winfo_y()
        notification.geometry(f"200x80+{pet_x}+{pet_y - 90}")

        c = tk.Canvas(notification, width=200, height=80, bg=bg, highlight_thickness=0)
        c.pack(fill='both', expand=True)

        # 圆角背景
        c.create_rectangle(5, 5, 195, 75, fill='#fef3c7', outline='#fbbf24', width=2, tags='bg')

        # 文字
        c.create_text(100, 25, text='☕ 休息提醒', fill='#92400e', font=('Segoe UI', 10, 'bold'), tags='text')
        c.create_text(100, 45, text='已连续工作50分钟', fill='#78350f', font=('Segoe UI', 8), tags='text')
        c.create_text(100, 62, text='喝杯水，放松一下!', fill='#78350f', font=('Segoe UI', 7), tags='text')

        def close():
            notification.destroy()

        # 点击关闭
        c.bind('<Button-1>', lambda e: close())

        # 自动关闭
        notification.after(10000, close)

    def add_particle(self, p_type):
        """添加粒子"""
        cx, cy = self.pet_center
        self.particles.append(Particle(cx, cy, p_type, self.colors))

    def add_xp(self, amount):
        """添加XP并显示浮动数字"""
        old_level = self.state['level']
        old_stage = self.state['evolution_stage']
        self.state['xp'] += amount

        # 检查升级
        while self.state['xp'] >= self.state['xp_to_next']:
            self.state['xp'] -= self.state['xp_to_next']
            self.state['level'] += 1
            self.state['xp_to_next'] = int(100 * (1.2 ** (self.state['level'] - 1)))

        # 检查进化阶段
        new_stage = get_stage_for_level(self.state['level']) if RENDER_3D_AVAILABLE else old_stage
        self.state['evolution_stage'] = new_stage

        # 显示浮动数字
        cx, _ = self.pet_center
        self.floating_numbers.append(FloatingNumber(cx, 60, f'+{amount} XP'))

        # 如果升级了
        if self.state['level'] > old_level:
            self.celebrate_level_up()

        # 如果进化了
        if new_stage > old_stage and RENDER_3D_AVAILABLE:
            self._on_evolution(old_stage, new_stage)
            self._update_render_config()

    def celebrate_level_up(self):
        """升级庆祝动画"""
        # 升级光环
        cx, cy = self.pet_center
        ring = self.canvas.create_oval(
            cx - 50, cy - 50, cx + 50, cy + 50,
            outline=self.colors.glow_active, width=3,
            tags='level_up_ring'
        )

        def expand_ring(step=0):
            if step < 20:
                size = 50 + step * 5
                alpha_step = 1 - step / 20
                self.canvas.coords(ring, cx - size, cy - size, cx + size, cy + size)
                self.root.after(30, lambda: expand_ring(step + 1))
            else:
                self.canvas.delete(ring)

        expand_ring()

        # 粒子爆发
        for _ in range(15):
            p_type = random.choice(['star', 'sparkle', 'plus'])
            self.add_particle(p_type)

    def update_particles(self):
        """更新粒子"""
        self.canvas.delete('particles')

        for p in list(self.particles):
            if p.update(self.width, self.height):
                alpha = p.get_alpha()
                size = p.get_size()

                # 根据alpha调整颜色明度
                color = p.start_color if alpha > 0.5 else p.end_color

                self.canvas.create_text(
                    p.x, p.y, text=p.char,
                    fill=color, font=('Segoe UI', size),
                    tags='particles'
                )
            else:
                self.particles.remove(p)

    def update_floating_numbers(self):
        """更新浮动数字"""
        self.canvas.delete('floating_numbers')

        for fn in list(self.floating_numbers):
            if fn.update():
                self.canvas.create_text(
                    fn.x, fn.y, text=fn.text,
                    fill=fn.color, font=('Segoe UI Semibold', 10, 'bold'),
                    tags='floating_numbers'
                )
            else:
                self.floating_numbers.remove(fn)

    def update_stars(self):
        """更新星星闪烁"""
        for i, star in enumerate(self.stars):
            star['phase'] += star['twinkle_speed']
            brightness = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(star['phase']))

            # 更新星星大小来模拟闪烁
            if i < len(self.star_items):
                size = star['size'] * brightness
                self.canvas.coords(
                    self.star_items[i],
                    star['x'], star['y'],
                    star['x'] + size, star['y'] + size
                )

    def update_ui(self):
        """更新UI"""
        c = self.canvas

        # 加载生产力统计
        self.load_work_stats()

        c.itemconfig(self.level_badge, text=f'Lv.{self.state["level"]}')

        xp_ratio = self.state['xp'] / self.state['xp_to_next']
        xp_color = self._get_bar_color(self.state['xp'], self.state['xp_to_next'])
        c.coords(self.xp_bar, 12, 28, 12 + int(68 * xp_ratio), 34)
        c.itemconfig(self.xp_bar, fill=xp_color)
        c.itemconfig(self.xp_text, text=f'{self.state["xp"]}/{self.state["xp_to_next"]} XP')

        status_colors = {
            'idle': self.colors.status_idle,
            'thinking': self.colors.status_thinking,
            'working': self.colors.status_working,
            'error': self.colors.status_error,
            'success': self.colors.status_success,
        }
        c.itemconfig(self.status_light, fill=status_colors.get(self.claude_state['status'], self.colors.status_idle))

        status_texts = {
            'idle': '● Idle',
            'thinking': '● Thinking...',
            'working': '⚡ Working',
            'error': '❌ Error!',
            'success': '✓ Success!',
        }
        c.itemconfig(self.claude_status, text=status_texts.get(self.claude_state['status'], '● Idle'))

        c.itemconfig(self.activity_text,
                    text=f'📁 {self.claude_state["files_created"]}+{self.claude_state["files_modified"]} | 💻 {self.claude_state["commands_run"]}')

        tool_text = ''
        if self.claude_state['current_tool']:
            tool = self.claude_state['current_tool']
            if tool == 'Write':
                tool_text = '📝 Writing...'
            elif tool == 'Edit':
                tool_text = '✏️ Editing...'
            elif tool == 'Bash':
                tool_text = '💻 Running...'
            elif tool == 'Read':
                tool_text = '📖 Reading...'
        c.itemconfig(self.tool_text, text=tool_text)

        c.itemconfig(self.time_text, text=datetime.now().strftime('%H:%M'))

        mood_icons = {
            'happy': '😊',
            'excited': '🎉',
            'love': '😍',
            'worried': '😟',
            'sleepy': '😴',
            'idle': '😌',
            'surprised': '😲',
            'proud': '😏',
            'confused': '😕',
        }
        mood_icon = mood_icons.get(self.state['mood'], '😊')
        c.itemconfig(self.mood_indicator, text=f'{mood_icon}')

        # 更新生产力条
        prod_score = self.work_stats.get('productivity_score', 50)
        prod_color = self._get_bar_color(prod_score, 100)
        w = self.width
        c.coords(self.productivity_bar, 12, 42, 12 + int((w - 24) * prod_score / 100), 46)
        c.itemconfig(self.productivity_bar, fill=prod_color)

        # 更新连击显示
        combo = self.state.get('combo', 0)
        if combo >= 3:
            c.itemconfig(self.combo_text, text=f'🔥 {combo}x')
        else:
            c.itemconfig(self.combo_text, text='')

    def update_animation(self):
        """更新动画"""
        cx, cy = self.pet_center

        # 浮动动画
        self.float_offset += self.config.float_speed * self.float_direction
        if abs(self.float_offset) > self.config.float_amplitude:
            self.float_direction *= -1

        float_y = self.float_offset

        # 呼吸动画
        self.breathing_phase += self.config.breathing_speed
        breathing_scale = 1 + self.config.breathing_amplitude * math.sin(self.breathing_phase)

        # 移动身体 (应用呼吸效果)
        for tag in ['pet_body', 'pet_belly', 'pet_highlight']:
            self.canvas.move(tag, 0, float_y * 0.3)

        # 更新阴影随浮动变化
        shadow_scale = 1 - 0.1 * math.sin(self.breathing_phase)
        shadow_offset = 5 * math.sin(self.breathing_phase)
        self.canvas.coords(
            self.pet_shadow,
            cx - 40 * shadow_scale, cy + 45 + shadow_offset,
            cx + 40 * shadow_scale, cy + 55 + shadow_offset
        )

        # 耳朵动画
        self.ear_twitch_timer += 1
        if self.ear_twitch_timer > random.randint(100, 300):
            self.ear_twitch_timer = 0
            self.twitch_ear()

        # 尾巴摇摆
        self.tail_angle += 0.08
        tail_sway = 5 * math.sin(self.tail_angle)
        base_points = [
            cx - 10, cy + 30,
            cx - 25, cy + 35,
            cx - 30 + tail_sway, cy + 20,
            cx - 20, cy + 15,
        ]
        self.canvas.coords(self.pet_tail, *base_points)

        # 脉冲动画
        self.pulse_phase += 0.1

        # 心情随机变化
        self.mood_timer += 1
        if self.mood_timer >= self.current_mood_duration:
            self.mood_timer = 0
            self.current_mood_duration = random.randint(120, 350)
            if self.claude_state['status'] == 'idle' and not self.state['is_sleeping']:
                moods = ['happy', 'idle', 'happy']
                self.state['mood'] = random.choice(moods)
                self.draw_face()

    def twitch_ear(self):
        """抽动耳朵"""
        cx, cy = self.pet_center

        # 左耳抽动
        left_sway = 3 if random.random() > 0.5 else -3
        new_left = [
            cx - 35, cy - 35,
            cx - 45, cy - 55,
            cx - 25 + left_sway, cy - 45,
        ]
        self.canvas.coords(self.pet_ear_left, *new_left)

        # 有时右耳也抽动
        if random.random() > 0.7:
            right_sway = -3 if random.random() > 0.5 else 3
            new_right = [
                cx + 35, cy - 35,
                cx + 45, cy - 55,
                cx + 25 + right_sway, cy - 45,
            ]
            self.canvas.coords(self.pet_ear_right, *new_right)

    def blink(self):
        """眨眼"""
        cx, cy = self.pet_center
        eye_y = cy - 12

        self.canvas.itemconfig('face', state='hidden')

        self.canvas.create_line(cx-20, eye_y-2, cx-10, eye_y-2, fill='#0c4a6e', width=2.5, tags='blink')
        self.canvas.create_line(cx+10, eye_y-2, cx+20, eye_y-2, fill='#0c4a6e', width=2.5, tags='blink')

        def restore():
            self.canvas.delete('blink')
            self.canvas.itemconfig('face', state='normal')

        self.root.after(100, restore)

    def start_state_monitor(self):
        """启动状态监控"""
        def monitor():
            while self.is_running:
                try:
                    if self.state_file.exists():
                        try:
                            with open(self.state_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)

                                new_files = data.get('files_created', 0) + data.get('files_modified', 0)
                                old_files = self.claude_state['files_created'] + self.claude_state['files_modified']

                                if new_files > old_files:
                                    self.claude_state['status'] = 'success'
                                    old_files_created = self.claude_state['files_created']
                                    self.claude_state['files_created'] = data.get('files_created', 0)
                                    self.claude_state['files_modified'] = data.get('files_modified', 0)

                                    # 追踪文件创建（用于道具掉落）
                                    files_created_delta = self.claude_state['files_created'] - old_files_created
                                    self.state['files_created_session'] += files_created_delta

                                    # 检查道具掉落（代码碎片）
                                    if RENDER_3D_AVAILABLE and self.inventory:
                                        from .items import ItemDropManager
                                        item = ItemDropManager.check_file_creation_drop(self.state['files_created_session'])
                                        if item:
                                            self.inventory.add_item(item)
                                            self.show_item_notification(item)

                                    # 连击检测
                                    if time.time() - self.state['last_combo_time'] < 5:
                                        self.state['combo'] += 1
                                    else:
                                        self.state['combo'] = 1
                                    self.state['last_combo_time'] = time.time()

                                    # 连击奖励
                                    xp_gain = 5 + self.state['combo'] * 2
                                    self.add_xp(xp_gain)
                                    self.last_activity_time = time.time()

                                    self.state['mood'] = 'excited'
                                    self.draw_face()

                                self.claude_state['commands_run'] = data.get('commands_run', 0)

                                errors = data.get('consecutive_failures', 0)
                                if errors > self.claude_state['errors_count']:
                                    # 追踪错误修复（假设错误被修复了）
                                    errors_fixed_delta = errors - self.claude_state['errors_count']
                                    self.state['errors_fixed_session'] += errors_fixed_delta

                                    self.claude_state['errors_count'] = errors
                                    self.claude_state['status'] = 'error'
                                    self.state['mood'] = 'worried'
                                    self.draw_face()

                                    # 检查道具掉落（除虫剑）
                                    if RENDER_3D_AVAILABLE and self.inventory:
                                        from .items import ItemDropManager
                                        item = ItemDropManager.check_error_fix_drop(self.state['errors_fixed_session'])
                                        if item:
                                            self.inventory.add_item(item)
                                            self.show_item_notification(item)

                                self.state['hunger'] = data.get('hunger', 100)
                                self.state['happiness'] = data.get('happiness', 100)
                                self.state['energy'] = data.get('energy', 100)
                                self.state['level'] = data.get('level', 1)

                        except (json.JSONDecodeError, KeyError):
                            pass

                    if self.activity_file.exists():
                        try:
                            with open(self.activity_file, 'r', encoding='utf-8') as f:
                                activity = json.load(f)
                                current_tool = activity.get('current_tool')

                                if current_tool and current_tool != self.claude_state['current_tool']:
                                    self.claude_state['current_tool'] = current_tool
                                    self.claude_state['status'] = 'working'
                                    self.last_activity_time = time.time()

                                    # 记录到记忆系统
                                    self._remember_activity('tool_change', current_tool, activity)
                                    self.draw_face()

                                is_thinking = activity.get('is_thinking', False)
                                if is_thinking:
                                    self.claude_state['status'] = 'thinking'
                                    self._remember_activity('thinking', None, activity)

                                self.claude_state['requests_count'] = activity.get('requests_count', 0)

                        except (json.JSONDecodeError, KeyError):
                            pass

                    # 记录定期记忆检查
                    self._check_memory_decay()

                    if time.time() - self.last_activity_time > 3:
                        if self.claude_state['status'] not in ['error', 'sleepy']:
                            self.claude_state['status'] = 'idle'
                            self.claude_state['current_tool'] = None
                            self.draw_face()

                except (json.JSONDecodeError, KeyError, IOError) as e:
                    # 静默处理预期的文件读取错误
                    pass
                except Exception as e:
                    # 记录其他未预期的错误
                    print(f"[StateMonitor] Error: {e}")

                time.sleep(0.2)

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def start_decay(self):
        """启动状态衰减"""
        def decay():
            while self.is_running:
                try:
                    if not self.state['is_sleeping']:
                        self.state['hunger'] = max(0, self.state['hunger'] - self.config.hunger_decay)
                        self.state['happiness'] = max(0, self.state['happiness'] - self.config.happiness_decay)
                    else:
                        self.state['energy'] = min(100, self.state['energy'] + self.config.energy_recovery)

                    # 低状态警告
                    if (self.state['hunger'] < self.config.hunger_warning or
                        self.state['happiness'] < self.config.happiness_warning or
                        self.state['energy'] < self.config.energy_warning):
                        if self.claude_state['status'] != 'error':
                            self.state['mood'] = 'worried'

                except (KeyError, AttributeError) as e:
                    # 静默处理状态访问错误
                    pass
                except Exception as e:
                    # 记录其他未预期的错误
                    print(f"[Decay] Error: {e}")

                time.sleep(1)

        thread = threading.Thread(target=decay, daemon=True)
        thread.start()

    def start_animation(self):
        """启动动画循环"""
        def animate():
            if not self.is_running:
                return

            self.animation_frame += 1

            self.update_animation()
            self.update_particles()
            self.update_floating_numbers()
            self.update_stars()

            if self.animation_frame % 5 == 0:
                self.update_ui()

            current_time = time.time()
            if current_time - self.last_blink > random.uniform(2.5, 6):
                self.blink()
                self.last_blink = current_time

            fps_delay = int(1000 / self.config.target_fps)
            self.root.after(fps_delay, animate)

        animate()

    def save_position(self):
        """保存位置"""
        state_file = Path.home() / '.claude-pet-companion' / 'pet_window_state.json'
        state_file.parent.mkdir(parents=True, exist_ok=True)

        data = {'x': self.root.winfo_x(), 'y': self.root.winfo_y()}
        with open(state_file, 'w') as f:
            json.dump(data, f)

    # ===== 进化系统方法 =====

    def _on_evolution(self, from_stage: int, to_stage: int):
        """进化事件处理"""
        # 播放进化动画
        if self.animation_manager:
            def on_animation_complete():
                self.show_evolution_notification(from_stage, to_stage)
                self.check_evolution_path()

            self.animation_manager.play_evolution(from_stage, to_stage, on_animation_complete)

    def check_evolution_path(self):
        """检查并更新进化路径"""
        if not RENDER_3D_AVAILABLE:
            return

        from .render.evolution_paths import determine_evolution_path

        stats = {
            'files_created': self.state.get('files_created_session', 0),
            'files_modified': self.claude_state.get('files_modified', 0),
            'errors_fixed': self.state.get('errors_fixed_session', 0),
            'interactions': self.state.get('interaction_count', 0),
            'night_hours': self.state.get('night_coding_hours', 0),
        }

        new_path = determine_evolution_path(stats)
        if new_path != self.state['evolution_path']:
            self.state['evolution_path'] = new_path
            self._update_render_config()

    def show_evolution_notification(self, from_stage: int, to_stage: int):
        """显示进化通知"""
        if not RENDER_3D_AVAILABLE:
            return

        from .render.evolution_stages import get_stage_visuals

        from_stage_info = get_stage_visuals(from_stage)
        to_stage_info = get_stage_visuals(to_stage)

        notification = tk.Toplevel(self.root)
        notification.geometry("250x100")
        bg = self.colors.ui_bg
        notification.configure(bg=bg)
        notification.attributes('-topmost', True)
        notification.overrideredirect(True)

        pet_x = self.root.winfo_x()
        pet_y = self.root.winfo_y()
        notification.geometry(f"250x100+{pet_x}+{pet_y - 110}")

        c = tk.Canvas(notification, width=250, height=100, bg=bg, highlightthickness=0)
        c.pack(fill='both', expand=True)

        # 进化动画背景
        c.create_rectangle(5, 5, 245, 95, fill='#fef3c7', outline='#fbbf24', width=2)

        # 文字
        c.create_text(125, 20, text='🌟 进化!', fill='#92400e', font=('Segoe UI', 12, 'bold'))
        c.create_text(125, 45, text=f'{from_stage_info.name} → {to_stage_info.name}',
                     fill='#78350f', font=('Segoe UI', 10))
        c.create_text(125, 65, text=f'({to_stage_info.name_cn})',
                     fill='#78350f', font=('Segoe UI', 8))

        def close():
            notification.destroy()

        c.bind('<Button-1>', lambda e: close())
        notification.after(5000, close)

    def show_item_notification(self, item_type: EvolutionItemType):
        """显示道具获得通知"""
        if not RENDER_3D_AVAILABLE:
            return

        from .items import get_item_display_name, get_item_icon, get_item_color

        notification = tk.Toplevel(self.root)
        notification.geometry("200x80")
        bg = self.colors.ui_bg
        notification.configure(bg=bg)
        notification.attributes('-topmost', True)
        notification.overrideredirect(True)

        pet_x = self.root.winfo_x()
        pet_y = self.root.winfo_y()
        notification.geometry(f"200x80+{pet_x}+{pet_y - 90}")

        c = tk.Canvas(notification, width=200, height=80, bg=bg, highlightthickness=0)
        c.pack(fill='both', expand=True)

        # 背景
        c.create_rectangle(5, 5, 195, 75, fill='#dbeafe', outline='#3b82f6', width=2)

        # 文字
        icon = get_item_icon(item_type)
        name = get_item_display_name(item_type)
        c.create_text(100, 20, text=f'{icon} 获得道具!', fill='#1e40af', font=('Segoe UI', 10, 'bold'))
        c.create_text(100, 45, text=name, fill='#1e3a8a', font=('Segoe UI', 9))

        def close():
            notification.destroy()

        c.bind('<Button-1>', lambda e: close())
        notification.after(3000, close)

    def show_inventory(self):
        """显示物品栏"""
        if not RENDER_3D_AVAILABLE or not self.inventory:
            return

        from .items import get_item_display_name, get_item_icon, get_item_color

        inventory = tk.Toplevel(self.root)
        inventory.geometry("300x400")
        bg = self.colors.ui_bg
        inventory.configure(bg=bg)
        inventory.attributes('-topmost', True)
        inventory.overrideredirect(True)

        pet_x = self.root.winfo_x()
        pet_y = self.root.winfo_y()
        inventory.geometry(f"300x400+{pet_x + self.width + 5}+{pet_y}")

        c = tk.Canvas(inventory, width=300, height=400, bg=bg, highlightthickness=0)
        c.pack(fill='both', expand=True)

        # 标题
        c.create_text(150, 20, text='🎒 物品栏', fill=self.colors.ui_text, font=('Segoe UI', 14, 'bold'))

        # 显示道具
        items = self.inventory.get_all_items()
        y_offset = 50

        if not items:
            c.create_text(150, 150, text='暂无道具', fill=self.colors.ui_text_dim, font=('Segoe UI', 10))
        else:
            for item_type, count in items.items():
                icon = get_item_icon(item_type)
                name = get_item_display_name(item_type)
                color = get_item_color(item_type)

                c.create_rectangle(20, y_offset, 280, y_offset + 45,
                                  fill=color, outline=self.colors.ui_border, width=1)
                c.create_text(40, y_offset + 22, text=icon, font=('Segoe UI', 16))
                c.create_text(70, y_offset + 12, text=name, fill='white' if count > 0 else self.colors.ui_text,
                             font=('Segoe UI', 10, 'bold'), anchor='w')
                c.create_text(70, y_offset + 32, text=f'x{count}', fill='white',
                             font=('Segoe UI', 9), anchor='w')

                y_offset += 55

        # 关闭按钮
        def close(): inventory.destroy()
        c.create_rectangle(260, 5, 295, 25, fill='#ef4444', outline='')
        c.create_text(277, 15, text='✕', fill='white', font=('Arial', 8, 'bold'))
        c.bind('<Button-1>', lambda e: close() if 260 < e.x < 295 and 5 < e.y < 25 else None)

        inventory.after(10000, close)

    def do_quit(self):
        """退出"""
        self.is_running = False
        self.save_position()

        save_file = Path.home() / '.claude-pet-companion' / 'pet_state.json'
        save_file.parent.mkdir(parents=True, exist_ok=True)

        def serialize_state(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_state(v) for k, v in obj.items()}
            else:
                return obj

        save_data = serialize_state({**self.state, **self.claude_state})

        with open(save_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        # 保存记忆系统
        if self.memory_manager:
            self.memory_manager.end_session()
            self.memory_manager.save()

        # 关闭IPC服务器
        self._shutdown_ipc()

        self.root.destroy()

    def run(self):
        """运行"""
        def autosave():
            if self.is_running and self.root.winfo_exists():
                save_file = Path.home() / '.claude-pet-companion' / 'pet_state.json'
                save_file.parent.mkdir(parents=True, exist_ok=True)

                def to_serializable(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    elif isinstance(obj, dict):
                        return {k: to_serializable(v) for k, v in obj.items()}
                    else:
                        return obj

                save_data = to_serializable({**self.state, **self.claude_state})
                save_data['last_updated'] = datetime.now().isoformat()

                with open(save_file, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, indent=2, ensure_ascii=False)

                self.root.after(20000, autosave)

        autosave()
        self.root.mainloop()


def main():
    pet = ClaudeCodePetHD()
    pet.run()


if __name__ == "__main__":
    main()
