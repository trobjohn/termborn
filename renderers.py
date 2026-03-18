"""Low-level plot renderers."""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import gaussian_kde

from .color import collision_color, color_palette, density_color, heatmap_color
from .config import THEME

BRAILLE_BASE = 0x2800
BRAILLE_MAP = {
    (0, 0): 0x01,
    (0, 1): 0x02,
    (0, 2): 0x04,
    (1, 0): 0x08,
    (1, 1): 0x10,
    (1, 2): 0x20,
    (0, 3): 0x40,
    (1, 3): 0x80,
}

ASCII_DOTS = [".", "o", "O", "@", "#"]
SHADE_CHARS = [" ", "░", "▒", "▓", "█"]
ASCII_SHADES = [" ", ".", ":", "*", "#"]


def scatter_grid(series, width, height, hue_enabled=False):
    width = max(1, width)
    height = max(1, height)
    dot_width = width * 2
    dot_height = height * 4

    x_all = np.concatenate([item.x for item in series])
    y_all = np.concatenate([item.y for item in series])
    xmin, xmax = _nice_limits(x_all)
    ymin, ymax = _nice_limits(y_all)

    grid = [[{"mask": 0, "series": set(), "count": 0} for _ in range(width)] for _ in range(height)]
    for series_id, item in enumerate(series):
        for x_val, y_val in zip(item.x, item.y):
            dot_x = _scale(x_val, xmin, xmax, dot_width)
            dot_y = _scale(y_val, ymin, ymax, dot_height)
            cell_x = min(width - 1, max(0, dot_x // 2))
            dot_in_x = dot_x % 2
            cell_y_from_bottom = min(height - 1, max(0, dot_y // 4))
            dot_in_y = 3 - (dot_y % 4)
            cell_y = height - 1 - cell_y_from_bottom
            cell = grid[cell_y][cell_x]
            cell["mask"] |= BRAILLE_MAP[(dot_in_x, dot_in_y)]
            cell["series"].add(series_id)
            cell["count"] += 1

    chars = [[" " for _ in range(width)] for _ in range(height)]
    colors = [[None for _ in range(width)] for _ in range(height)]
    max_count = max(cell["count"] for row in grid for cell in row) if grid else 1
    for y_idx, row in enumerate(grid):
        for x_idx, cell in enumerate(row):
            if not cell["series"]:
                continue
            chars[y_idx][x_idx] = _braille_char(cell["mask"])
            colors[y_idx][x_idx] = density_color(
                cell["series"],
                density=cell["count"],
                max_density=max_count,
                hue_enabled=hue_enabled,
            )
    return chars, colors, (xmin, xmax), (ymin, ymax)


def histogram_grid(values, width, height, bins="auto"):
    counts, edges = np.histogram(values, bins=bins)
    width = min(width, len(counts)) if len(counts) else width
    if width <= 0:
        width = 1
    if len(counts) != width:
        rebinned = np.array_split(counts, width)
        counts = np.array([chunk.sum() for chunk in rebinned], dtype=float)
        edges = np.linspace(float(edges[0]), float(edges[-1]), width + 1)

    max_count = float(np.max(counts)) if len(counts) else 1.0
    max_count = max(max_count, 1.0)
    grid = [[" " for _ in range(width)] for _ in range(height)]
    for x_idx, count in enumerate(counts):
        full = (count / max_count) * height
        whole = int(full)
        frac = full - whole
        for offset in range(whole):
            y_idx = height - 1 - offset
            if y_idx >= 0:
                grid[y_idx][x_idx] = "█" if THEME.unicode else "#"
        if whole < height and frac > 0:
            y_idx = height - 1 - whole
            grid[y_idx][x_idx] = _partial_block(frac)
    return grid, edges, counts


def hist2d_grid(x_values, y_values, width, height, bins="auto"):
    del bins
    width = max(1, width)
    height = max(1, height)
    xmin, xmax = _nice_limits(x_values)
    ymin, ymax = _nice_limits(y_values)

    counts, xedges, yedges = np.histogram2d(
        x_values,
        y_values,
        bins=(width, height),
        range=((xmin, xmax), (ymin, ymax)),
    )

    grid = [[" " for _ in range(width)] for _ in range(height)]
    positive = counts[counts > 0]
    if positive.size == 0:
        return grid, (float(xedges[0]), float(xedges[-1])), (float(yedges[0]), float(yedges[-1]))

    max_count = float(np.max(positive))
    ramp = SHADE_CHARS if THEME.unicode else ASCII_SHADES
    for x_idx in range(width):
        for y_idx in range(height):
            count = float(counts[x_idx, y_idx])
            if count <= 0:
                continue
            level = np.log1p(count) / np.log1p(max_count)
            shade_idx = min(len(ramp) - 1, max(1, int(np.ceil(level * (len(ramp) - 1)))))
            row = height - 1 - y_idx
            grid[row][x_idx] = ramp[shade_idx]
    return grid, (float(xedges[0]), float(xedges[-1])), (float(yedges[0]), float(yedges[-1]))


def kde_grid(series, width, height):
    x_all = np.concatenate([item.x for item in series])
    xmin, xmax = _nice_limits(x_all)
    xs = np.linspace(xmin, xmax, max(width * 2, 64))
    ys_by_series = []
    for item in series:
        if len(item.x) == 0:
            density = np.zeros_like(xs)
        elif len(item.x) < 2 or np.allclose(item.x.min(), item.x.max()):
            density = np.zeros_like(xs)
            density[np.argmin(np.abs(xs - item.x.mean()))] = 1.0
        else:
            density = gaussian_kde(item.x)(xs)
        ys_by_series.append(density)

    ymax = max(float(np.max(curve)) for curve in ys_by_series) if ys_by_series else 1.0
    ymax = max(ymax, 1e-12)

    grid = [[{"mask": 0, "series": set()} for _ in range(width)] for _ in range(height)]
    for series_id, density in enumerate(ys_by_series):
        for col in range(width):
            x_start = int((col / width) * len(xs))
            x_stop = max(x_start + 1, int(((col + 1) / width) * len(xs)))
            y_val = float(np.max(density[x_start:x_stop]))
            dot_y = _scale(y_val, 0.0, ymax, height * 4)
            cell_y_from_bottom = min(height - 1, max(0, dot_y // 4))
            dot_in_y = 3 - (dot_y % 4)
            cell_y = height - 1 - cell_y_from_bottom
            cell = grid[cell_y][col]
            cell["mask"] |= BRAILLE_MAP[(0, dot_in_y)] | BRAILLE_MAP[(1, dot_in_y)]
            cell["series"].add(series_id)

    chars = [[" " for _ in range(width)] for _ in range(height)]
    colors = [[None for _ in range(width)] for _ in range(height)]
    palette = color_palette(n_colors=max(1, len(series)))
    for y_idx, row in enumerate(grid):
        for x_idx, cell in enumerate(row):
            if not cell["series"]:
                continue
            chars[y_idx][x_idx] = _braille_char(cell["mask"])
            if len(cell["series"]) == 1:
                colors[y_idx][x_idx] = palette[next(iter(cell["series"]))]
            else:
                colors[y_idx][x_idx] = collision_color(cell["series"])
    return chars, colors, (xmin, xmax), (0.0, ymax)


def ecdf_grid(series, width, height):
    width = max(1, width)
    height = max(1, height)
    x_all = np.concatenate([item.x for item in series])
    xmin, xmax = _nice_limits(x_all)
    grid = [[{"mask": 0, "series": set(), "count": 0} for _ in range(width)] for _ in range(height)]

    for series_id, item in enumerate(series):
        if len(item.x) == 0:
            continue
        xs = np.sort(item.x)
        ys = np.arange(1, len(xs) + 1, dtype=float) / len(xs)
        prev_col = None
        prev_row = None
        for x_val, y_val in zip(xs, ys):
            col = _scale(x_val, xmin, xmax, width * 2)
            row = _scale(y_val, 0.0, 1.0, height * 4)
            cell_x = min(width - 1, max(0, col // 2))
            dot_in_x = col % 2
            cell_y_from_bottom = min(height - 1, max(0, row // 4))
            dot_in_y = 3 - (row % 4)
            cell_y = height - 1 - cell_y_from_bottom
            _mark_braille(grid, cell_x, cell_y, dot_in_x, dot_in_y, series_id)
            if prev_col is not None and prev_row is not None:
                for seg_col in range(min(prev_col, col), max(prev_col, col) + 1):
                    prev_level = prev_row
                    current_level = row
                    mix = 0.0 if col == prev_col else (seg_col - prev_col) / (col - prev_col)
                    interp_row = int(round(prev_level + (current_level - prev_level) * mix))
                    seg_x = min(width - 1, max(0, seg_col // 2))
                    seg_dot_x = seg_col % 2
                    seg_cell_y_from_bottom = min(height - 1, max(0, interp_row // 4))
                    seg_dot_y = 3 - (interp_row % 4)
                    seg_y = height - 1 - seg_cell_y_from_bottom
                    _mark_braille(grid, seg_x, seg_y, seg_dot_x, seg_dot_y, series_id)
            prev_col = col
            prev_row = row

    chars = [[" " for _ in range(width)] for _ in range(height)]
    colors = [[None for _ in range(width)] for _ in range(height)]
    max_count = max(cell["count"] for row in grid for cell in row) if grid else 1
    for y_idx, row in enumerate(grid):
        for x_idx, cell in enumerate(row):
            if not cell["series"]:
                continue
            chars[y_idx][x_idx] = _braille_char(cell["mask"])
            colors[y_idx][x_idx] = density_color(
                cell["series"],
                density=cell["count"],
                max_density=max_count,
                hue_enabled=len(series) > 1,
            )
    return chars, colors, (xmin, xmax), (0.0, 1.0)


def heatmap_grid(matrix, steps=20):
    array = np.asarray(matrix, dtype=float)
    if array.ndim != 2:
        raise ValueError("heatmap expects a 2D matrix")
    rows, cols = array.shape
    chars = [[" " for _ in range(cols)] for _ in range(rows)]
    colors = [[None for _ in range(cols)] for _ in range(rows)]
    mask = ~np.isnan(array)
    if not np.any(mask):
        return chars, colors
    vmin = float(np.min(array[mask]))
    vmax = float(np.max(array[mask]))
    ramp = SHADE_CHARS if THEME.unicode else ASCII_SHADES
    for row_idx in range(rows):
        for col_idx in range(cols):
            value = array[row_idx, col_idx]
            if np.isnan(value):
                continue
            if math.isclose(vmin, vmax):
                level = 1.0
            else:
                level = (float(value) - vmin) / (vmax - vmin)
            draw_row = rows - 1 - row_idx
            if THEME.color:
                chars[draw_row][col_idx] = "█" if THEME.unicode else "#"
                colors[draw_row][col_idx] = heatmap_color(level, steps=steps)
            else:
                idx = min(len(ramp) - 1, max(1, int(round(level * (len(ramp) - 1)))))
                chars[draw_row][col_idx] = ramp[idx]
    return chars, colors


def _nice_limits(values):
    vmin = float(np.min(values))
    vmax = float(np.max(values))
    if math.isclose(vmin, vmax):
        pad = 1.0 if vmin == 0.0 else abs(vmin) * 0.1
        return vmin - pad, vmax + pad
    pad = (vmax - vmin) * 0.05
    return vmin - pad, vmax + pad


def _scale(value, low, high, size):
    if high <= low:
        return 0
    position = (float(value) - low) / (high - low)
    position = min(1.0, max(0.0, position))
    return min(size - 1, int(position * (size - 1)))


def _braille_char(mask):
    if THEME.unicode:
        return chr(BRAILLE_BASE + mask)
    bits = bin(mask).count("1")
    return ASCII_DOTS[min(bits, len(ASCII_DOTS) - 1)]


def _partial_block(frac):
    if not THEME.unicode:
        return "#"
    blocks = ["▁", "▂", "▃", "▄", "▅", "▆", "▇"]
    idx = min(len(blocks) - 1, max(0, int(frac * len(blocks))))
    return blocks[idx]


def _mark_braille(grid, cell_x, cell_y, dot_in_x, dot_in_y, series_id):
    cell = grid[cell_y][cell_x]
    cell["mask"] |= BRAILLE_MAP[(dot_in_x, dot_in_y)]
    cell["series"].add(series_id)
    cell["count"] += 1
