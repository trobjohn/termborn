"""Shared configuration state."""

from dataclasses import dataclass


@dataclass
class Theme:
    color: bool = True
    unicode: bool = True
    colorblind: bool = False
    auto_color: bool = True
    auto_unicode: bool = True


THEME = Theme()
