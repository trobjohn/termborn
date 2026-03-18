"""Public seaborn-ish plotting API."""

from __future__ import annotations

from typing import Any

from .color import apply_color, color_palette as palette_fn
from .config import THEME
from .data import resolve_xy, split_by_hue
from .layout import framed_plot
import numpy as np

from .renderers import ecdf_grid, heatmap_grid, hist2d_grid, histogram_grid, kde_grid, scatter_grid
from .terminal import refresh_theme_from_terminal, terminal_size


def scatterplot(*args, data=None, x=None, y=None, hue=None, palette=None, width=None, height=None, title=None, **kwargs):
    del palette, kwargs
    x, y = _coerce_xy_args(args, x=x, y=y)
    refresh_theme_from_terminal()
    plot_width, plot_height = _plot_size(width, height)
    x_values, y_values, hue_values = resolve_xy(data=data, x=x, y=y, hue=hue)
    series = split_by_hue(x_values, y_values=y_values, hue_values=hue_values)
    chars, colors, xlim, ylim = scatter_grid(series, plot_width, plot_height, hue_enabled=hue_values is not None)
    legend = _legend(series) if hue_values is not None else None
    canvas = framed_plot(chars, colors, title=title, xlabel=_axis_label(x), ylabel=_axis_label(y), legend=legend, xlim=xlim, ylim=ylim)
    return _render(canvas)


def histplot(*args, data=None, x=None, y=None, bins="auto", width=None, height=None, title=None, **kwargs):
    del kwargs
    x, y = _coerce_xy_args(args, x=x, y=y, allow_y=True)
    refresh_theme_from_terminal()
    plot_width, plot_height = _plot_size(width, height)
    x_values, y_values, _ = resolve_xy(data=data, x=x, y=y, hue=None)
    if y is not None:
        chars, xlim, ylim = hist2d_grid(x_values, y_values, plot_width, plot_height, bins=bins)
        canvas = framed_plot(chars, title=title, xlabel=_axis_label(x), ylabel=_axis_label(y), xlim=xlim, ylim=ylim)
        return _render(canvas)
    chars, edges, _counts = histogram_grid(x_values, plot_width, plot_height, bins=bins)
    ylim = (0.0, float(max(_counts)) if len(_counts) else 1.0)
    canvas = framed_plot(chars, title=title, xlabel=_axis_label(x), ylabel="count", xlim=(edges[0], edges[-1]), ylim=ylim)
    return _render(canvas)


def kdeplot(*args, data=None, x=None, hue=None, fill=False, common_norm=True, width=None, height=None, title=None, **kwargs):
    del fill, common_norm, kwargs
    x = _coerce_x_arg(args, x=x)
    refresh_theme_from_terminal()
    plot_width, plot_height = _plot_size(width, height)
    x_values, _, hue_values = resolve_xy(data=data, x=x, y=None, hue=hue)
    series = split_by_hue(x_values, y_values=None, hue_values=hue_values)
    chars, colors, xlim, ylim = kde_grid(series, plot_width, plot_height)
    legend = _legend(series) if hue_values is not None else None
    canvas = framed_plot(chars, colors, title=title, xlabel=_axis_label(x), ylabel="density", legend=legend, xlim=xlim, ylim=ylim)
    return _render(canvas)


def ecdfplot(*args, data=None, x=None, hue=None, width=None, height=None, title=None, **kwargs):
    del kwargs
    x = _coerce_x_arg(args, x=x)
    refresh_theme_from_terminal()
    plot_width, plot_height = _plot_size(width, height)
    x_values, _, hue_values = resolve_xy(data=data, x=x, y=None, hue=hue)
    series = split_by_hue(x_values, y_values=None, hue_values=hue_values)
    chars, colors, xlim, ylim = ecdf_grid(series, plot_width, plot_height)
    legend = _legend(series) if hue_values is not None else None
    canvas = framed_plot(chars, colors, title=title, xlabel=_axis_label(x), ylabel="ecdf", legend=legend, xlim=xlim, ylim=ylim)
    return _render(canvas)


def heatmap(data, *, width=None, height=None, title=None, vmin=None, vmax=None, **kwargs):
    del kwargs
    refresh_theme_from_terminal()
    matrix = _coerce_matrix(data)
    if vmin is not None or vmax is not None:
        matrix = matrix.astype(float, copy=True)
        lo = np.nanmin(matrix) if vmin is None else vmin
        hi = np.nanmax(matrix) if vmax is None else vmax
        matrix = np.clip(matrix, lo, hi)
    chars, colors = heatmap_grid(matrix)
    canvas = framed_plot(
        chars,
        colors,
        title=title,
        xlabel=None,
        ylabel=None,
        legend=None,
        xlim=(0.0, float(matrix.shape[1])),
        ylim=(0.0, float(matrix.shape[0])),
    )
    return _render(canvas)


def set_theme(*args: Any, color=None, unicode=None, colorblind=None, **kwargs: Any):
    del args, kwargs
    if color is not None:
        THEME.color = bool(color)
        THEME.auto_color = False
    if unicode is not None:
        THEME.unicode = bool(unicode)
        THEME.auto_unicode = False
    if colorblind is not None:
        THEME.colorblind = bool(colorblind)


def color_palette(palette=None, n_colors=None):
    return palette_fn(palette=palette, n_colors=n_colors)


def _plot_size(width, height):
    term_width, term_height = terminal_size()
    plot_height = height or max(8, min(24, term_height - 8))
    if width is None:
        width_cap = max(20, int(plot_height * 1.75))
        plot_width = max(20, min(80, term_width - 14, width_cap))
    else:
        plot_width = width
    return plot_width, plot_height


def _legend(series):
    palette = palette_fn(n_colors=max(1, len(series)))
    items = []
    for idx, item in enumerate(series):
        swatch = apply_color("■", palette[idx]) if THEME.unicode else apply_color("#", palette[idx])
        items.append(f"{swatch} {item.label}")
    return "  ".join(items)


def _render(canvas):
    output = canvas.render()
    print(output)
    return canvas


def _coerce_x_arg(args, x=None):
    if not args:
        return x
    if len(args) > 1:
        raise TypeError("termborn only supports a single positional argument here")
    if x is not None:
        raise TypeError("x was provided both positionally and by keyword")
    return args[0]


def _coerce_xy_args(args, x=None, y=None, allow_y=True):
    if not args:
        return x, y
    if len(args) > 2 or (not allow_y and len(args) > 1):
        raise TypeError("too many positional arguments for termborn plot")
    if len(args) >= 1:
        if x is not None:
            raise TypeError("x was provided both positionally and by keyword")
        x = args[0]
    if len(args) == 2:
        if y is not None:
            raise TypeError("y was provided both positionally and by keyword")
        y = args[1]
    return x, y


def _axis_label(value):
    return value if isinstance(value, str) else None


def _coerce_matrix(data):
    if hasattr(data, "to_numpy"):
        data = data.to_numpy()
    matrix = np.asarray(data)
    if matrix.ndim != 2:
        raise ValueError("heatmap expects a 2D matrix or DataFrame")
    return matrix
