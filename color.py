"""ANSI colors and simple palettes."""

from __future__ import annotations

import numpy as np

from .config import THEME

RESET = "\033[0m"

ANSI = {
    "blue": "\033[34m",
    "green": "\033[32m",
    "cyan": "\033[36m",
    "red": "\033[31m",
    "magenta": "\033[35m",
    "yellow": "\033[33m",
    "white": "\033[97m",
}

DEFAULT_PALETTE = ["cyan", "magenta", "yellow"]
COLORBLIND_PALETTE = ["blue", "yellow", "green"]
RGB = {
    "blue": (70, 130, 255),
    "green": (70, 210, 120),
    "cyan": (70, 220, 255),
    "red": (255, 90, 90),
    "magenta": (255, 90, 220),
    "yellow": (255, 220, 90),
    "white": (245, 245, 245),
}


def color_palette(palette=None, n_colors=None):
    names = _normalize_palette(palette)
    if n_colors is None:
        return names
    if n_colors <= len(names):
        return names[:n_colors]
    out = []
    for idx in range(n_colors):
        out.append(names[idx % len(names)])
    return out


def apply_color(text: str, color_name: str | None) -> str:
    if not THEME.color or not color_name:
        return text
    if color_name.startswith("\033["):
        return f"{color_name}{text}{RESET}"
    prefix = ANSI.get(color_name)
    if not prefix:
        return text
    return f"{prefix}{text}{RESET}"


def collision_color(series_ids) -> str | None:
    unique = sorted(set(series_ids))
    if not unique:
        return None
    if THEME.colorblind:
        return "white"
    mapping = {
        (0, 1): "blue",
        (0, 2): "green",
        (1, 2): "red",
    }
    if len(unique) == 1:
        return color_palette(n_colors=max(unique) + 1)[unique[0]]
    if len(unique) >= 3:
        return "white"
    return mapping.get(tuple(unique), "white")


def density_color(series_ids, density, max_density, hue_enabled):
    level = _density_level(density, max_density)
    if not hue_enabled:
        return _grayscale(level)
    base = collision_color(series_ids)
    if base is None:
        return None
    return _scaled_rgb(base, level)


def heatmap_color(level, steps=20):
    level = max(0.0, min(1.0, float(level)))
    if not THEME.color:
        return None
    if steps > 1:
        level = round(level * (steps - 1)) / (steps - 1)
    start = np.array((255, 230, 90), dtype=float)
    end = np.array((30, 155, 70), dtype=float)
    rgb = (start + (end - start) * level).astype(int)
    return f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"


def _normalize_palette(palette):
    if isinstance(palette, (list, tuple)) and palette:
        return list(palette)
    if palette == "colorblind" or THEME.colorblind:
        return list(COLORBLIND_PALETTE)
    return list(DEFAULT_PALETTE)


def _density_level(density, max_density):
    if max_density <= 1:
        return 1.0
    return max(0.18, min(1.0, np.log1p(density) / np.log1p(max_density)))


def _scaled_rgb(base_name, level):
    rgb = RGB.get(base_name)
    if rgb is None:
        return base_name
    floor = 28
    red, green, blue = rgb
    scaled = (
        int(floor + (red - floor) * level),
        int(floor + (green - floor) * level),
        int(floor + (blue - floor) * level),
    )
    return f"\033[38;2;{scaled[0]};{scaled[1]};{scaled[2]}m"


def _grayscale(level):
    shade = int(60 + 195 * level)
    return f"\033[38;2;{shade};{shade};{shade}m"
