"""Canvas layout helpers."""

from __future__ import annotations

from .canvas import TextCanvas


def framed_plot(plot_chars, plot_colors=None, title=None, xlabel=None, ylabel=None, legend=None, xlim=None, ylim=None):
    plot_height = len(plot_chars)
    plot_width = len(plot_chars[0]) if plot_chars else 1
    left_margin = 10
    bottom_area = 3
    top_area = 1 if title else 0
    legend_area = 1 if legend else 0
    canvas = TextCanvas(
        width=left_margin + plot_width + 1,
        height=top_area + plot_height + bottom_area + legend_area,
    )

    plot_top = top_area
    _draw_axes(canvas, left_margin, plot_top, plot_width, plot_height)
    if title is not None:
        canvas.write_text(0, 0, title[: canvas.width])
    if ylim is not None:
        canvas.write_text(0, plot_top, f"{ylim[1]:8.2g}")
        canvas.write_text(0, plot_top + plot_height - 1, f"{ylim[0]:8.2g}")
    if ylabel is not None:
        canvas.write_text(0, max(0, plot_top + plot_height // 2), str(ylabel)[:8])

    for row_idx, row in enumerate(plot_chars):
        for col_idx, char in enumerate(row):
            color = None if plot_colors is None else plot_colors[row_idx][col_idx]
            canvas.set(left_margin + col_idx + 1, plot_top + row_idx, char, color)

    x_axis_y = plot_top + plot_height
    if xlim is not None:
        left_x_text = f"{xlim[0]:.3g}"
        right_label = f"{xlim[1]:.3g}"
        left_pos = left_margin + 1
        right_pos = max(left_margin + 1, left_margin + plot_width - len(right_label) + 1)
        if left_pos + len(left_x_text) + 1 < right_pos:
            canvas.write_text(left_pos, x_axis_y + 1, left_x_text)
        canvas.write_text(right_pos, x_axis_y + 1, right_label)
    if xlabel is not None:
        label = str(xlabel)
        left_bound = left_margin + 1
        right_bound = left_margin + plot_width - len(label) + 1
        start = max(left_bound, min(right_bound, left_margin + 1 + (plot_width - len(label)) // 2))
        canvas.write_text(start, x_axis_y + 2, label[:plot_width])
    if legend is not None:
        canvas.write_text(0, canvas.height - 1, legend[: canvas.width])
    return canvas


def _draw_axes(canvas, left_margin, top, width, height):
    for row in range(height):
        canvas.set(left_margin, top + row, "│")
    for col in range(width + 1):
        canvas.set(left_margin + col, top + height, "─")
    canvas.set(left_margin, top + height, "└")
