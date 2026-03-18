"""Character canvas with per-cell color."""

from __future__ import annotations

from dataclasses import dataclass

from .color import apply_color


@dataclass
class Cell:
    char: str = " "
    color: str | None = None


class TextCanvas:
    def __init__(self, width: int, height: int):
        self.width = max(1, width)
        self.height = max(1, height)
        self.rows = [[Cell() for _ in range(self.width)] for _ in range(self.height)]

    def set(self, x: int, y: int, char: str, color: str | None = None):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.rows[y][x] = Cell(char=char, color=color)

    def write_text(self, x: int, y: int, text: str, color: str | None = None):
        for offset, char in enumerate(text):
            self.set(x + offset, y, char, color)

    def render(self) -> str:
        lines = []
        for row in self.rows:
            pieces = [apply_color(cell.char, cell.color) for cell in row]
            lines.append("".join(pieces).rstrip())
        return "\n".join(lines)
