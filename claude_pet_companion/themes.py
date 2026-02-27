#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Pet Theme System
"""
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class ColorScheme:
    """颜色方案"""
    # 背景渐变 (从上到下)
    bg_top: str
    bg_bottom: str
    bg_grid: str

    # 宠物颜色
    pet_primary: str
    pet_secondary: str
    pet_tertiary: str
    pet_belly: str
    pet_highlight: str

    # UI 颜色
    ui_bg: str
    ui_border: str
    ui_text: str
    ui_text_dim: str

    # 状态颜色
    status_idle: str
    status_thinking: str
    status_working: str
    status_success: str
    status_error: str

    # 状态条颜色
    bar_high: str      # >= 60%
    bar_medium: str    # 30-60%
    bar_low: str       # < 30%

    # 发光效果
    glow_idle: str
    glow_active: str

    # 腮红颜色
    blush_color: str

    # 天线颜色
    antenna_bulb_idle: str
    antenna_bulb_thinking: str
    antenna_bulb_working: str
    antenna_bulb_error: str


# 预定义主题
THEMES: Dict[str, ColorScheme] = {
    'default': ColorScheme(
        bg_top='#0f172a',
        bg_bottom='#020617',
        bg_grid='#1e293b',
        pet_primary='#38bdf8',
        pet_secondary='#0ea5e9',
        pet_tertiary='#0284c7',
        pet_belly='#e0f2fe',
        pet_highlight='#ffffff',
        ui_bg='#1e293b',
        ui_border='#334155',
        ui_text='#e2e8f0',
        ui_text_dim='#64748b',
        status_idle='#94a3b8',
        status_thinking='#fbbf24',
        status_working='#22c55e',
        status_success='#4ade80',
        status_error='#ef4444',
        bar_high='#4ade80',
        bar_medium='#fbbf24',
        bar_low='#ef4444',
        glow_idle='#38bdf8',
        glow_active='#60a5fa',
        blush_color='#fda4af',
        antenna_bulb_idle='#fbbf24',
        antenna_bulb_thinking='#f59e0b',
        antenna_bulb_working='#22c55e',
        antenna_bulb_error='#ef4444',
    ),

    'pink': ColorScheme(
        bg_top='#2d1f3d',
        bg_bottom='#1a1025',
        bg_grid='#4a3060',
        pet_primary='#f472b6',
        pet_secondary='#ec4899',
        pet_tertiary='#db2777',
        pet_belly='#fce7f3',
        pet_highlight='#fff5f7',
        ui_bg='#3d2a4a',
        ui_border='#6b4c7a',
        ui_text='#fce7f3',
        ui_text_dim='#a87ab5',
        status_idle='#d8b4d8',
        status_thinking='#fbbf24',
        status_working='#c084fc',
        status_success='#f0abfc',
        status_error='#fb7185',
        bar_high='#f0abfc',
        bar_medium='#f9a8d4',
        bar_low='#fb7185',
        glow_idle='#f472b6',
        glow_active='#f9a8d4',
        blush_color='#fda4af',
        antenna_bulb_idle='#f472b6',
        antenna_bulb_thinking='#f9a8d4',
        antenna_bulb_working='#c084fc',
        antenna_bulb_error='#fb7185',
    ),

    'green': ColorScheme(
        bg_top='#0f2d1f',
        bg_bottom='#021a10',
        bg_grid='#1a4030',
        pet_primary='#4ade80',
        pet_secondary='#22c55e',
        pet_tertiary='#16a34a',
        pet_belly='#dcfce7',
        pet_highlight='#f0fdf4',
        ui_bg='#1a4030',
        ui_border='#2d6a4a',
        ui_text='#dcfce7',
        ui_text_dim='#6b9b7a',
        status_idle='#8bcca8',
        status_thinking='#fbbf24',
        status_working='#4ade80',
        status_success='#86efac',
        status_error='#fb7185',
        bar_high='#86efac',
        bar_medium='#fbbf24',
        bar_low='#fb7185',
        glow_idle='#4ade80',
        glow_active='#86efac',
        blush_color='#fda4af',
        antenna_bulb_idle='#4ade80',
        antenna_bulb_thinking='#fbbf24',
        antenna_bulb_working='#22c55e',
        antenna_bulb_error='#fb7185',
    ),

    'dark': ColorScheme(
        bg_top='#000000',
        bg_bottom='#0a0a0a',
        bg_grid='#1a1a1a',
        pet_primary='#6b7280',
        pet_secondary='#4b5563',
        pet_tertiary='#374151',
        pet_belly='#d1d5db',
        pet_highlight='#f3f4f6',
        ui_bg='#1f2937',
        ui_border='#374151',
        ui_text='#e5e7eb',
        ui_text_dim='#9ca3af',
        status_idle='#6b7280',
        status_thinking='#fbbf24',
        status_working='#4ade80',
        status_success='#22c55e',
        status_error='#ef4444',
        bar_high='#22c55e',
        bar_medium='#fbbf24',
        bar_low='#ef4444',
        glow_idle='#6b7280',
        glow_active='#9ca3af',
        blush_color='#d1d5db',
        antenna_bulb_idle='#6b7280',
        antenna_bulb_thinking='#fbbf24',
        antenna_bulb_working='#22c55e',
        antenna_bulb_error='#ef4444',
    ),

    'purple': ColorScheme(
        bg_top='#1e1b4b',
        bg_bottom='#0f0d2e',
        bg_grid='#312e81',
        pet_primary='#a78bfa',
        pet_secondary='#8b5cf6',
        pet_tertiary='#7c3aed',
        pet_belly='#ede9fe',
        pet_highlight='#f5f3ff',
        ui_bg='#312e81',
        ui_border='#4c1d95',
        ui_text='#ede9fe',
        ui_text_dim='#a5b4fc',
        status_idle='#a5b4fc',
        status_thinking='#fbbf24',
        status_working='#a78bfa',
        status_success='#c4b5fd',
        status_error='#fb7185',
        bar_high='#c4b5fd',
        bar_medium='#fbbf24',
        bar_low='#fb7185',
        glow_idle='#a78bfa',
        glow_active='#c4b5fd',
        blush_color='#fda4af',
        antenna_bulb_idle='#a78bfa',
        antenna_bulb_thinking='#fbbf24',
        antenna_bulb_working='#8b5cf6',
        antenna_bulb_error='#fb7185',
    ),
}


def get_theme(name: str = 'default') -> ColorScheme:
    """获取主题"""
    return THEMES.get(name, THEMES['default'])


def list_themes() -> list:
    """列出所有主题"""
    return list(THEMES.keys())
