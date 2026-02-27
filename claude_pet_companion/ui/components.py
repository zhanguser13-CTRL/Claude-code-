"""
UI Components Library for Claude Pet Companion

Provides modern, reusable UI components with:
- Smooth animations
- Hover effects
- Theme support
- Responsive layout
- Accessibility features
"""

import tkinter as tk
from tkinter import ttk, font
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import math

from ..themes import ThemeManager


class ButtonStyle(Enum):
    """Button style variants."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    DANGER = "danger"
    WARNING = "warning"
    GHOST = "ghost"
    OUTLINE = "outline"


class AnimationState(Enum):
    """Animation states."""
    IDLE = "idle"
    HOVER = "hover"
    PRESSED = "pressed"
    FOCUS = "focus"
    DISABLED = "disabled"


@dataclass
class AnimationConfig:
    """Animation configuration."""
    duration: int = 200  # milliseconds
    easing: str = "ease-out"
    delay: int = 0


class ModernButton(tk.Canvas):
    """Modern button with smooth animations and effects."""

    def __init__(self, parent, text: str = "", command: Callable = None,
                 style: ButtonStyle = ButtonStyle.PRIMARY,
                 width: int = 120, height: int = 40,
                 corner_radius: int = 8,
                 **kwargs):
        self.text = text
        self.command = command
        self.style = style
        self.corner_radius = corner_radius
        self.animation_state = AnimationState.IDLE
        self.hover_progress = 0.0
        self.press_progress = 0.0

        # Theme colors
        self._load_colors()

        # Create canvas
        super().__init__(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            bg=self.parent_bg,
            **kwargs
        )

        # Bind events
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_press)
        self.bind('<ButtonRelease-1>', self._on_release)

        # Initial draw
        self.draw()

    def _load_colors(self):
        """Load colors from theme."""
        theme = ThemeManager.get_current_theme()

        self.color_map = {
            ButtonStyle.PRIMARY: {
                'bg': theme.primary_color,
                'fg': theme.primary_text,
                'hover': theme.primary_hover,
                'active': theme.primary_active,
            },
            ButtonStyle.SECONDARY: {
                'bg': theme.secondary_color,
                'fg': theme.secondary_text,
                'hover': theme.secondary_hover,
                'active': theme.secondary_active,
            },
            ButtonStyle.SUCCESS: {
                'bg': '#10b981',
                'fg': '#ffffff',
                'hover': '#059669',
                'active': '#047857',
            },
            ButtonStyle.DANGER: {
                'bg': '#ef4444',
                'fg': '#ffffff',
                'hover': '#dc2626',
                'active': '#b91c1c',
            },
            ButtonStyle.WARNING: {
                'bg': '#f59e0b',
                'fg': '#ffffff',
                'hover': '#d97706',
                'active': '#b45309',
            },
            ButtonStyle.GHOST: {
                'bg': '',
                'fg': theme.text_color,
                'hover': theme.hover_color,
                'active': theme.active_color,
            },
            ButtonStyle.OUTLINE: {
                'bg': '',
                'fg': theme.primary_color,
                'hover': theme.hover_color,
                'active': theme.active_color,
            },
        }

        self.parent_bg = theme.background_color

    def get_current_bg(self) -> str:
        """Get current background color based on state."""
        colors = self.color_map.get(self.style, self.color_map[ButtonStyle.PRIMARY])

        if self.animation_state == AnimationState.PRESSED:
            base = colors['active'] if colors['active'] else colors['hover']
            return self._interpolate_color(colors['bg'], base, 0.5 + self.press_progress * 0.5)

        if self.animation_state == AnimationState.HOVER:
            hover = colors['hover'] if colors['hover'] else colors['bg']
            return self._interpolate_color(colors['bg'], hover, self.hover_progress)

        return colors['bg'] if colors['bg'] else self.parent_bg

    def get_current_fg(self) -> str:
        """Get current foreground color."""
        colors = self.color_map.get(self.style, self.color_map[ButtonStyle.PRIMARY])
        return colors['fg']

    def _interpolate_color(self, color1: str, color2: str, t: float) -> str:
        """Interpolate between two hex colors."""
        c1 = self._hex_to_rgb(color1)
        c2 = self._hex_to_rgb(color2)

        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)

        return f'#{r:02x}{g:02x}{b:02x}'

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16)
        )

    def _on_enter(self, event):
        """Handle mouse enter."""
        self.animation_state = AnimationState.HOVER
        self._animate_hover(1.0)

    def _on_leave(self, event):
        """Handle mouse leave."""
        if self.animation_state != AnimationState.PRESSED:
            self.animation_state = AnimationState.IDLE
        self._animate_hover(0.0)

    def _on_press(self, event):
        """Handle button press."""
        self.animation_state = AnimationState.PRESSED
        self._animate_press(1.0)

    def _on_release(self, event):
        """Handle button release."""
        if self.command:
            self.command()
        self.animation_state = AnimationState.HOVER
        self._animate_press(0.0)

    def _animate_hover(self, target: float):
        """Animate hover transition."""
        self._animate_value('hover_progress', target, 150, self.draw)

    def _animate_press(self, target: float):
        """Animate press transition."""
        self._animate_value('press_progress', target, 100, self.draw)

    def _animate_value(self, attr: str, target: float, duration: int, callback: Callable):
        """Animate a value over time."""
        current = getattr(self, attr)
        if abs(current - target) < 0.01:
            setattr(self, attr, target)
            callback()
            return

        steps = 10
        step_size = (target - current) / steps
        delay = max(1, duration // steps)

        def step(step_num):
            if step_num < steps:
                setattr(self, attr, current + step_size * (step_num + 1))
                callback()
                self.after(delay, lambda: step(step_num + 1))
            else:
                setattr(self, attr, target)
                callback()

        step(0)

    def draw(self):
        """Draw the button."""
        self.delete('all')

        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1:
            w = int(self['width'])
        if h <= 1:
            h = int(self['height'])

        bg = self.get_current_bg()
        fg = self.get_current_fg()

        # Draw background
        if bg:
            self._draw_rounded_rect(0, 0, w, h, self.corner_radius, bg, '')

        # Draw outline for outline style
        if self.style == ButtonStyle.OUTLINE:
            self._draw_rounded_rect(0, 0, w, h, self.corner_radius, '', fg)

        # Draw shadow on hover
        if self.hover_progress > 0.5:
            shadow_alpha = int((self.hover_progress - 0.5) * 0.3 * 255)
            self._draw_shadow(shadow_alpha)

        # Draw text
        self._draw_text(w, h, fg)

    def _draw_rounded_rect(self, x1: int, y1: int, x2: int, y2: int,
                          r: int, fill: str, outline: str):
        """Draw a rounded rectangle."""
        points = [
            x1 + r, y1,
            x1 + r, y1,
            x2 - r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1 + r,
            x1, y1,
        ]
        self.create_polygon(points, fill=fill, outline=outline, smooth=True)

    def _draw_shadow(self, alpha: int):
        """Draw shadow effect."""
        w = self.winfo_width()
        h = self.winfo_height()
        offset = int(3 * self.press_progress + 1)

        shadow_color = f'#000000{alpha:02x}'
        self._draw_rounded_rect(offset, offset, w + offset, h + offset,
                              self.corner_radius, shadow_color, '')

    def _draw_text(self, w: int, h: int, color: str):
        """Draw button text."""
        self.create_text(
            w // 2, h // 2,
            text=self.text,
            fill=color,
            font=('Segoe UI', 10, 'normal')
        )

    def set_text(self, text: str):
        """Update button text."""
        self.text = text
        self.draw()

    def set_style(self, style: ButtonStyle):
        """Update button style."""
        self.style = style
        self._load_colors()
        self.draw()


class ProgressBar(tk.Canvas):
    """Modern progress bar with smooth animations."""

    def __init__(self, parent, value: float = 0.0, maximum: float = 100.0,
                 height: int = 8, corner_radius: int = 4,
                 show_text: bool = False,
                 **kwargs):
        self._value = value
        self._maximum = maximum
        self._display_value = value  # For animation
        self.corner_radius = corner_radius
        self.show_text = show_text
        self.target_value = value

        theme = ThemeManager.get_current_theme()
        self.bg_color = theme.progress_bg
        self.fill_color = theme.progress_fill

        super().__init__(
            parent,
            height=height,
            highlightthickness=0,
            bg=theme.background_color,
            **kwargs
        )

        self.draw()

    def set(self, value: float):
        """Set progress value with animation."""
        self.target_value = max(0, min(value, self._maximum))
        self._animate_to_value()

    def get(self) -> float:
        """Get current value."""
        return self._value

    def _animate_to_value(self):
        """Animate to target value."""
        diff = self.target_value - self._display_value
        if abs(diff) < 0.1:
            self._display_value = self.target_value
            self._value = self.target_value
            self.draw()
            return

        step = diff * 0.15
        self._display_value += step
        self.draw()
        self.after(16, self._animate_to_value)

    def draw(self):
        """Draw the progress bar."""
        self.delete('all')

        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1:
            w = 200  # Default width
        if h <= 1:
            h = int(self['height'])

        # Calculate fill width
        fill_width = int((self._display_value / self._maximum) * w)

        # Draw background
        self._draw_rounded_rect(0, 0, w, h, self.corner_radius, self.bg_color, '')

        # Draw fill
        if fill_width > 0:
            # Adjust for rounded corners
            fill_w = min(fill_width + self.corner_radius, w)
            self._draw_rounded_rect(0, 0, fill_w, h, self.corner_radius, self.fill_color, '')

        # Draw text
        if self.show_text:
            percentage = int((self._display_value / self._maximum) * 100)
            self.create_text(
                w // 2, h // 2,
                text=f"{percentage}%",
                fill='white' if fill_width > w / 2 else self.fill_color,
                font=('Segoe UI', 8, 'bold')
            )

    def _draw_rounded_rect(self, x1: int, y1: int, x2: int, y2: int, r: int, fill: str, outline: str):
        """Draw a rounded rectangle."""
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y2 - r,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y1 + r,
        ]
        self.create_polygon(points, fill=fill, outline=outline, smooth=True)


class Card(tk.Frame):
    """Modern card component with shadow and rounded corners."""

    def __init__(self, parent, title: str = "", content: str = "",
                 icon: str = "", corner_radius: int = 12,
                 **kwargs):
        self.corner_radius = corner_radius
        self.title_text = title
        self.content_text = content
        self.icon = icon

        theme = ThemeManager.get_current_theme()
        self.bg_color = theme.card_bg
        self.title_color = theme.title_color
        self.text_color = theme.text_color
        self.shadow_color = theme.shadow_color

        # Create canvas for custom drawing
        self.canvas = tk.Canvas(
            parent,
            highlightthickness=0,
            bg=theme.background_color,
            **kwargs
        )

        # Content frame
        self.content_frame = tk.Frame(self.canvas, bg=self.bg_color)

        super().__init__(self.canvas, bg=self.bg_color, **kwargs)

        self._setup_ui()
        self._draw()

    def _setup_ui(self):
        """Setup UI elements."""
        if self.title_text:
            title_label = tk.Label(
                self.content_frame,
                text=self.icon + " " + self.title_text if self.icon else self.title_text,
                bg=self.bg_color,
                fg=self.title_color,
                font=('Segoe UI', 12, 'bold'),
                anchor='w'
            )
            title_label.pack(fill='x', padx=16, pady=(16, 8))

        if self.content_text:
            content_label = tk.Label(
                self.content_frame,
                text=self.content_text,
                bg=self.bg_color,
                fg=self.text_color,
                font=('Segoe UI', 10),
                anchor='w',
                justify='left',
                wraplength=300
            )
            content_label.pack(fill='both', expand=True, padx=16, pady=(0, 16))

    def _draw(self):
        """Draw card with shadow."""
        self.canvas.delete('all')

        w = 300  # Default width
        h = 100

        # Draw shadow
        for i in range(5):
            alpha = int(20 - i * 4)
            shadow_color = f'#000000{alpha:02x}'
            offset = 5 - i
            self._draw_rounded_rect(
                offset, offset,
                w + offset, h + offset,
                self.corner_radius,
                shadow_color
            )

        # Draw card background
        self._draw_rounded_rect(0, 0, w, h, self.corner_radius, self.bg_color)

    def _draw_rounded_rect(self, x1: int, y1: int, x2: int, y2: int, r: int, color: str):
        """Draw a rounded rectangle."""
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y2 - r,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y1 + r,
        ]
        self.canvas.create_polygon(points, fill=color, outline='', smooth=True)

    def pack(self, **kwargs):
        """Pack both canvas and content frame."""
        self.canvas.pack(**kwargs)
        self.content_frame.place(x=0, y=0, relwidth=1, relheight=1)


class StatBar(tk.Frame):
    """Stat bar for displaying pet stats (health, hunger, etc.)."""

    def __init__(self, parent, label: str = "", value: float = 100,
                 max_value: float = 100, color: str = "#10b981",
                 height: int = 24, **kwargs):
        self.label_text = label
        self._value = value
        self.max_value = max_value
        self.bar_color = color
        self.height = height

        theme = ThemeManager.get_current_theme()

        super().__init__(parent, bg=theme.background_color, **kwargs)

        # Label
        self.label = tk.Label(
            self,
            text=label,
            bg=theme.background_color,
            fg=theme.text_color,
            font=('Segoe UI', 9),
            width=8,
            anchor='w'
        )
        self.label.pack(side='left')

        # Progress bar canvas
        self.canvas = tk.Canvas(
            self,
            height=height,
            highlightthickness=0,
            bg=theme.stat_bar_bg,
            **kwargs
        )
        self.canvas.pack(side='left', fill='x', expand=True, padx=(8, 0))

        # Value label
        self.value_label = tk.Label(
            self,
            text=f"{int(value)}/{int(max_value)}",
            bg=theme.background_color,
            fg=theme.text_color,
            font=('Segoe UI', 9),
            width=8
        )
        self.value_label.pack(side='right')

        self.draw()

    def set_value(self, value: float):
        """Update stat value."""
        self._value = max(0, min(value, self.max_value))
        self.value_label.config(text=f"{int(self._value)}/{int(self.max_value)}")
        self.draw()

    def draw(self):
        """Draw the stat bar."""
        self.canvas.delete('all')

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1:
            w = 150

        # Calculate fill
        fill_width = int((self._value / self.max_value) * w)

        # Draw background
        self.canvas.create_rectangle(0, 0, w, h, fill='#e5e7eb', outline='')

        # Draw fill with rounded corners
        if fill_width > 0:
            self.canvas.create_rectangle(0, 0, fill_width, h, fill=self.bar_color, outline='')

    def get_color_for_value(self) -> str:
        """Get color based on value."""
        ratio = self._value / self.max_value
        if ratio > 0.6:
            return "#10b981"  # Green
        elif ratio > 0.3:
            return "#f59e0b"  # Orange
        else:
            return "#ef4444"  # Red


if __name__ == "__main__":
    # Test UI components
    root = tk.Tk()
    root.title("UI Components Test")
    root.geometry("400x300")

    # Modern button
    btn = ModernButton(root, text="Click Me", style=ButtonStyle.PRIMARY)
    btn.pack(pady=20)

    # Progress bar
    pb = ProgressBar(root, value=50, show_text=True)
    pb.pack(fill='x', padx=20, pady=10)

    # Stat bar
    stat = StatBar(root, label="Health", value=75, color="#ef4444")
    stat.pack(fill='x', padx=20, pady=10)

    root.mainloop()
