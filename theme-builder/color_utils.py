"""
Color utility functions for theme generation
"""

import re
from typing import Tuple, Optional

def validate_hex_color(color: str) -> bool:
    """Validate hex color format"""
    pattern = r'^#[0-9A-Fa-f]{6}$|^#[0-9A-Fa-f]{8}$'
    return bool(re.match(pattern, color))

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 8:
        hex_color = hex_color[:6]  # Remove alpha
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB to hex color"""
    return f"#{r:02x}{g:02x}{b:02x}"

def get_brightness(hex_color: str) -> float:
    """Get perceived brightness of color (0-1)"""
    r, g, b = hex_to_rgb(hex_color)
    # Using perceived brightness formula
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255

def get_luminance(hex_color: str) -> float:
    """Get relative luminance for WCAG contrast calculations"""
    r, g, b = hex_to_rgb(hex_color)
    
    def adjust_channel(channel: int) -> float:
        c = channel / 255
        if c <= 0.03928:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4
    
    r_adj = adjust_channel(r)
    g_adj = adjust_channel(g)
    b_adj = adjust_channel(b)
    
    return 0.2126 * r_adj + 0.7152 * g_adj + 0.0722 * b_adj

def calculate_contrast_ratio(bg_color: str, fg_color: str) -> float:
    """Calculate WCAG contrast ratio between two colors"""
    l1 = get_luminance(bg_color)
    l2 = get_luminance(fg_color)
    
    lighter = max(l1, l2)
    darker = min(l1, l2)
    
    return (lighter + 0.05) / (darker + 0.05)

def adjust_brightness(hex_color: str, percent: int) -> str:
    """Adjust brightness by percentage (-100 to 100)"""
    r, g, b = hex_to_rgb(hex_color)
    
    # Calculate adjustment
    factor = 1 + (percent / 100)
    
    # Apply adjustment
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    
    return rgb_to_hex(r, g, b)

def get_complementary_color(hex_color: str) -> str:
    """Get complementary color"""
    r, g, b = hex_to_rgb(hex_color)
    
    # Calculate complementary
    r_comp = 255 - r
    g_comp = 255 - g
    b_comp = 255 - b
    
    return rgb_to_hex(r_comp, g_comp, b_comp)

def blend_colors(color1: str, color2: str, ratio: float = 0.5) -> str:
    """Blend two colors together"""
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    
    r = int(r1 * (1 - ratio) + r2 * ratio)
    g = int(g1 * (1 - ratio) + g2 * ratio)
    b = int(b1 * (1 - ratio) + b2 * ratio)
    
    return rgb_to_hex(r, g, b)

def saturate_color(hex_color: str, amount: float) -> str:
    """Increase color saturation"""
    r, g, b = hex_to_rgb(hex_color)
    
    # Convert to HSL
    r_norm = r / 255
    g_norm = g / 255
    b_norm = b / 255
    
    max_val = max(r_norm, g_norm, b_norm)
    min_val = min(r_norm, g_norm, b_norm)
    l = (max_val + min_val) / 2
    
    if max_val == min_val:
        h = s = 0
    else:
        d = max_val - min_val
        s = d / (2 - max_val - min_val) if l > 0.5 else d / (max_val + min_val)
        
        if max_val == r_norm:
            h = (g_norm - b_norm) / d + (6 if g_norm < b_norm else 0)
        elif max_val == g_norm:
            h = (b_norm - r_norm) / d + 2
        else:
            h = (r_norm - g_norm) / d + 4
        h /= 6
    
    # Adjust saturation
    s = min(1, s * (1 + amount))
    
    # Convert back to RGB
    if s == 0:
        r = g = b = int(l * 255)
    else:
        def hue_to_rgb(p: float, q: float, t: float) -> float:
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p
        
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        
        r = int(hue_to_rgb(p, q, h + 1/3) * 255)
        g = int(hue_to_rgb(p, q, h) * 255)
        b = int(hue_to_rgb(p, q, h - 1/3) * 255)
    
    return rgb_to_hex(r, g, b)