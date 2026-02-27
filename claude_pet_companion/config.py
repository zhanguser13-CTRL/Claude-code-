#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Pet Configuration System
"""
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class PetConfig:
    """宠物配置"""
    # 窗口设置
    width: int = 240
    height: int = 280
    dpi_scale: float = 1.5

    # 动画设置
    animation_speed: float = 1.0
    float_amplitude: float = 3.0
    float_speed: float = 0.08
    breathing_speed: float = 0.05
    breathing_amplitude: float = 0.03

    # 宠物信息
    pet_name: str = 'Claude'

    # 状态衰减速率 (每秒)
    hunger_decay: float = 0.5
    happiness_decay: float = 0.3
    energy_recovery: float = 2.0  # 睡眠时恢复

    # 主题
    theme: str = 'default'

    # 声音
    sound_enabled: bool = False

    # 粒子设置
    max_particles: int = 25
    particle_fade_speed: float = 1.0

    # 性能
    target_fps: int = 40
    enable_performance_mode: bool = False

    # 状态阈值
    hunger_warning: int = 30
    happiness_warning: int = 30
    energy_warning: int = 30

    # 守护进程与IPC设置
    daemon_enabled: bool = True
    ipc_host: str = '127.0.0.1'
    ipc_port: int = 15340
    single_instance: bool = True

    # 对话记忆设置
    conversation_enabled: bool = True
    conversation_auto_save: bool = True
    max_conversations: int = 1000

    def save(self, path: Optional[Path] = None):
        """保存配置"""
        if path is None:
            path = Path.home() / '.claude-pet-companion' / 'config.json'
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temporary file first for atomic operation
        temp_path = path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)
            # Atomic rename
            temp_path.replace(path)
            # Set restrictive permissions (owner read/write only)
            import os
            import stat
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            raise

    @classmethod
    def load(cls, path: Optional[Path] = None) -> 'PetConfig':
        """加载配置"""
        if path is None:
            path = Path.home() / '.claude-pet-companion' / 'config.json'

        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Validate data types before creating instance
                if not isinstance(data, dict):
                    raise TypeError("Configuration must be a dictionary")
                return cls(**data)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                # Log error but don't crash
                import logging
                logging.warning(f"Failed to load config from {path}: {e}")

        return cls()

    def update(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
