"""
Glassmorphism UI Panel for Claude Pet Companion

Provides modern glass-effect panels with:
- Blur effect simulation
- Semi-transparent backgrounds
- Subtle borders
- Vibrancy effects
- Smooth animations
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Tuple, List
from PIL import Image, ImageTk, ImageFilter, ImageDraw
import math


class GlassPanel(tk.Frame):
    """
    A glassmorphism-style panel.

    Note: True blur effects require platform-specific APIs.
    This implementation simulates the glass effect with
    transparency and subtle styling.
    """

    def __init__(self, parent,
                 blur_radius: int = 20,
                 opacity: float = 0.85,
                 corner_radius: int = 16,
                 border_color: str = "rgba(255, 255, 255, 0.2)",
                 border_width: int = 1,
                 shadow_intensity: float = 0.1,
                 **kwargs):
        self.blur_radius = blur_radius
        self.opacity = opacity
        self.corner_radius = corner_radius
        self.border_color = border_color
        self.border_width = border_width
        self.shadow_intensity = shadow_intensity

        # Calculate actual background color
        self._setup_colors()

        # Configure the frame
        kwargs.pop('bg', None)  # Remove bg if provided
        super().__init__(parent, bg=self.bg_color, **kwargs)

        # Create canvas for drawing effects
        self.canvas = tk.Canvas(
            self,
            highlightthickness=0,
            bg=self.bg_color,
            insertbackground='white'
        )
        self.canvas.pack(fill='both', expand=True)

        # Content container
        self.content_frame = tk.Frame(self.canvas, bg=self.bg_color)
        self.content_frame.place(relx=0.5, rely=0.5, anchor='center')

        # Bind events
        self.bind('<Configure>', self._on_resize)
        self.bind('<Map>', self._on_map)

        self._needs_redraw = True

    def _setup_colors(self):
        """Setup glass effect colors."""
        # Use a semi-transparent white/gray as base
        # The alpha is simulated by blending with a typical background
        base_opacity = int(self.opacity * 255)

        # Light theme glass color
        r, g, b = 250, 250, 255
        self.bg_color = f'#{r:02x}{g:02x}{b:02x}'

        # Border color (semi-transparent)
        self.actual_border_color = self._parse_rgba(self.border_color)
        self.shadow_color = f'#{int(0):02x}{int(0):02x}{int(0):02x}'

    def _parse_rgba(self, rgba: str) -> str:
        """Parse rgba string to hex."""
        if rgba.startswith('#'):
            return rgba

        # Parse rgba(r, g, b, a) format
        import re
        match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)', rgba)
        if match:
            r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
            a = float(match.group(4)) if match.group(4) else 1.0
            # Blend with white for transparency simulation
            r = int(r * a + 255 * (1 - a))
            g = int(g * a + 255 * (1 - a))
            b = int(b * a + 255 * (1 - a))
            return f'#{r:02x}{g:02x}{b:02x}'

        return '#ffffff'

    def _on_resize(self, event):
        """Handle resize events."""
        self._needs_redraw = True
        self._draw_effects()

    def _on_map(self, event):
        """Handle widget mapping."""
        self._draw_effects()

    def _draw_effects(self):
        """Draw glass effects."""
        if not self._needs_redraw:
            return

        self.canvas.delete('all')

        w = self.winfo_width()
        h = self.winfo_height()

        if w <= 1 or h <= 1:
            self.after(100, self._draw_effects)
            return

        # Draw shadow
        self._draw_shadow(w, h)

        # Draw background with rounded corners
        self._draw_rounded_rect(w, h)

        # Draw border
        if self.border_width > 0:
            self._draw_border(w, h)

        # Update content frame size
        self._needs_redraw = False

    def _draw_shadow(self, w: int, h: int):
        """Draw shadow effect."""
        shadow_offset = 8
        shadow_alpha = int(self.shadow_intensity * 50)

        for i in range(5):
            offset = shadow_offset - i
            alpha = max(0, shadow_alpha - i * 10)
            color = f'#{0:02x}{0:02x}{0:02x}'  # Black shadow

            # Draw shadow layers
            self.canvas.create_polygon(
                self._rounded_polygon_coords(
                    offset, offset,
                    w + offset - shadow_offset // 2,
                    h + offset - shadow_offset // 2,
                    self.corner_radius
                ),
                fill=color,
                outline='',
                smooth=True
            )

    def _draw_rounded_rect(self, w: int, h: int):
        """Draw the main rounded rectangle."""
        coords = self._rounded_polygon_coords(
            0, 0, w, h, self.corner_radius
        )
        self.canvas.create_polygon(
            coords,
            fill=self.bg_color,
            outline='',
            smooth=True
        )

    def _draw_border(self, w: int, h: int):
        """Draw border with rounded corners."""
        # Inner border
        inset = self.border_width // 2
        coords = self._rounded_polygon_coords(
            inset, inset,
            w - inset, h - inset,
            self.corner_radius - 1
        )
        self.canvas.create_polygon(
            coords,
            fill='',
            outline=self.actual_border_color,
            width=self.border_width,
            smooth=True
        )

    def _rounded_polygon_coords(self, x1: int, y1: int, x2: int, y2: int, r: int) -> List[float]:
        """Generate coordinates for a rounded rectangle polygon."""
        r = min(r, (x2 - x1) // 2, (y2 - y1) // 2)
        if r <= 0:
            return [x1, y1, x2, y1, x2, y2, x1, y2]

        # Number of points for the arc
        arc_points = 8

        coords = []

        # Top edge
        coords.extend([x1 + r, y1])
        coords.extend([x2 - r, y1])

        # Top-right corner
        for i in range(arc_points + 1):
            angle = -math.pi / 2 + (math.pi / 2) * (i / arc_points)
            coords.extend([x2 - r + r * math.cos(angle), y1 + r + r * math.sin(angle)])

        # Right edge
        coords.extend([x2, y1 + r])
        coords.extend([x2, y2 - r])

        # Bottom-right corner
        for i in range(arc_points + 1):
            angle = 0 + (math.pi / 2) * (i / arc_points)
            coords.extend([x2 - r + r * math.cos(angle), y2 - r + r * math.sin(angle)])

        # Bottom edge
        coords.extend([x2 - r, y2])
        coords.extend([x1 + r, y2])

        # Bottom-left corner
        for i in range(arc_points + 1):
            angle = math.pi / 2 + (math.pi / 2) * (i / arc_points)
            coords.extend([x1 + r + r * math.cos(angle), y2 - r + r * math.sin(angle)])

        # Left edge
        coords.extend([x1, y2 - r])
        coords.extend([x1, y1 + r])

        # Top-left corner
        for i in range(arc_points + 1):
            angle = math.pi + (math.pi / 2) * (i / arc_points)
            coords.extend([x1 + r + r * math.cos(angle), y1 + r + r * math.sin(angle)])

        return coords

    def add_widget(self, widget, **pack_kwargs):
        """Add a widget to the content frame."""
        widget.pack(in_=self.content_frame, **pack_kwargs)

    def get_content_frame(self) -> tk.Frame:
        """Get the content frame for direct widget adding."""
        return self.content_frame


class BlurPanel(tk.Frame):
    """
    Panel with simulated blur effect using semi-transparent overlay.

    This creates a "frosted glass" appearance by layering
    semi-transparent elements.
    """

    def __init__(self, parent,
                 background_tint: str = "#ffffff",
                 tint_opacity: float = 0.7,
                 saturation: float = 0.8,
                 corner_radius: int = 12,
                 **kwargs):
        self.tint_color = background_tint
        self.tint_opacity = tint_opacity
        self.saturation = saturation
        self.corner_radius = corner_radius

        # Calculate blended background
        self.bg_color = self._blend_color(background_tint, tint_opacity)

        super().__init__(parent, bg=self.bg_color, **kwargs)

        # Canvas for drawing
        self.canvas = tk.Canvas(
            self,
            highlightthickness=0,
            bg=self.bg_color
        )
        self.canvas.pack(fill='both', expand=True)

        # Noise overlay for texture
        self._add_noise_texture()

    def _blend_color(self, color: str, opacity: float) -> str:
        """Blend a color with white for transparency simulation."""
        # Parse hex color
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)

        # Blend with white
        r = int(r * opacity + 255 * (1 - opacity))
        g = int(g * opacity + 255 * (1 - opacity))
        b = int(b * opacity + 255 * (1 - opacity))

        return f'#{r:02x}{g:02x}{b:02x}'

    def _add_noise_texture(self):
        """Add subtle noise texture for realism."""
        w = self.winfo_width()
        h = self.winfo_height()

        if w > 1 and h > 1:
            # Create noise pattern
            noise_points = min(500, w * h // 100)
            for _ in range(noise_points):
                x = int(hash(str(_)) % w)
                y = int(hash(str(_ + 1)) % h)
                self.canvas.create_oval(
                    x, y, x + 1, y + 1,
                    fill='#ffffff',
                    outline='',
                    stipple='gray25'
                )


class AcrylicPanel(GlassPanel):
    """
    Windows-style acrylic panel with stronger blur and vibrancy.

    Simulates the Windows 11 acrylic material.
    """

    def __init__(self, parent,
                 blur_radius: int = 32,
                 opacity: float = 0.75,
                 luminosity: float = 1.0,
                 **kwargs):
        self.luminosity = luminosity

        super().__init__(
            parent,
            blur_radius=blur_radius,
            opacity=opacity,
            corner_radius=8,
            border_color="rgba(255, 255, 255, 0.1)",
            border_width=2,
            shadow_intensity=0.15,
            **kwargs
        )

        # Add luminosity overlay
        self._add_luminosity()

    def _add_luminosity(self):
        """Add luminosity effect for brightness."""
        if self.luminosity > 1.0:
            # Create bright highlight at top
            self.canvas.create_rectangle(
                0, 0,
                self.winfo_width(),
                int(self.winfo_height() * 0.3),
                fill=f'#{255:02x}{255:02x}{255:02x}',
                stipple='gray12',
                outline=''
            )


class VibrantPanel(GlassPanel):
    """
    Vibrant panel with subtle gradient effects.

    Creates a colorful, vibrant glass appearance.
    """

    def __init__(self, parent,
                 gradient_colors: List[str] = None,
                 **kwargs):
        self.gradient_colors = gradient_colors or [
            '#667eea', '#764ba2'
        ]

        # Default to slightly more transparent
        kwargs.setdefault('opacity', 0.8)
        kwargs.setdefault('border_color', 'rgba(255, 255, 255, 0.3)')

        super().__init__(parent, **kwargs)

        # Add gradient overlay
        self._add_gradient()

    def _add_gradient(self):
        """Add gradient effect."""
        w = self.winfo_width()
        h = self.winfo_height()

        if len(self.gradient_colors) >= 2:
            # Create gradient using stippled rectangles
            steps = 20
            for i in range(steps):
                y1 = int(h * i / steps)
                y2 = int(h * (i + 1) / steps)
                t = i / steps

                # Interpolate colors
                color1 = self.gradient_colors[0]
                color2 = self.gradient_colors[-1]
                color = self._interpolate_colors(color1, color2, t)

                self.canvas.create_rectangle(
                    0, y1, w, y2,
                    fill=color,
                    outline='',
                    stipple='gray10'
                )

    def _interpolate_colors(self, color1: str, color2: str, t: float) -> str:
        """Interpolate between two hex colors."""
        c1 = color1.lstrip('#')
        c2 = color2.lstrip('#')

        r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
        r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)

        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)

        return f'#{r:02x}{g:02x}{b:02x}'


class GlassDialog(tk.Toplevel):
    """
    A dialog window with glassmorphism styling.
    """

    def __init__(self, parent, title: str = "", **kwargs):
        super().__init__(parent, **kwargs)

        self.title(title)
        self.configure(bg='white')

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Create glass panel as main container
        self.glass_panel = GlassPanel(
            self,
            blur_radius=25,
            opacity=0.9,
            corner_radius=16
        )
        self.glass_panel.pack(fill='both', expand=True, padx=20, pady=20)

    def add_content(self, widget):
        """Add content widget to the dialog."""
        widget.pack(in_=self.glass_panel.get_content_frame(),
                   fill='both', expand=True, padx=20, pady=20)


# Preset glass styles

GLASS_STYLE_LIGHT = {
    'blur_radius': 20,
    'opacity': 0.85,
    'corner_radius': 16,
    'border_color': 'rgba(255, 255, 255, 0.3)',
    'border_width': 1,
    'shadow_intensity': 0.1
}

GLASS_STYLE_DARK = {
    'blur_radius': 20,
    'opacity': 0.75,
    'corner_radius': 16,
    'border_color': 'rgba(255, 255, 255, 0.1)',
    'border_width': 1,
    'shadow_intensity': 0.2
}

GLASS_STYLE_FROSTED = {
    'blur_radius': 30,
    'opacity': 0.7,
    'corner_radius': 20,
    'border_color': 'rgba(255, 255, 255, 0.2)',
    'border_width': 2,
    'shadow_intensity': 0.15
}


def create_glass_panel(parent, style: str = 'light', **kwargs) -> GlassPanel:
    """Create a glass panel with a preset style."""
    style_dict = {
        'light': GLASS_STYLE_LIGHT,
        'dark': GLASS_STYLE_DARK,
        'frosted': GLASS_STYLE_FROSTED
    }.get(style, GLASS_STYLE_LIGHT)

    style_dict.update(kwargs)
    return GlassPanel(parent, **style_dict)


if __name__ == "__main__":
    # Test glass panels
    root = tk.Tk()
    root.title("Glass Panel Test")
    root.geometry("600x400")
    root.configure(bg='#f0f0f0')

    # Test basic glass panel
    panel1 = create_glass_panel(root, style='light')
    panel1.place(x=50, y=50, width=200, height=150)

    # Test frosted panel
    panel2 = create_glass_panel(root, style='frosted')
    panel2.place(x=300, y=50, width=200, height=150)

    # Test vibrant panel
    panel3 = VibrantPanel(root, gradient_colors=['#667eea', '#764ba2'])
    panel3.place(x=175, y=250, width=200, height=100)

    root.mainloop()
