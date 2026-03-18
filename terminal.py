"""Terminal capability helpers."""

from __future__ import annotations

import os
import shutil
import sys

from .config import THEME


def terminal_size(default=(100, 28)):
    size = shutil.get_terminal_size(fallback=default)
    return size.columns, size.lines


def supports_color():
    if not sys.stdout.isatty():
        return False
    if os.environ.get("NO_COLOR"):
        return False
    term = os.environ.get("TERM", "")
    return term not in {"", "dumb"}


def supports_unicode():
    encoding = getattr(sys.stdout, "encoding", None) or ""
    return "utf" in encoding.lower()


def refresh_theme_from_terminal():
    if THEME.auto_color:
        THEME.color = supports_color()
    if THEME.auto_unicode:
        THEME.unicode = supports_unicode()
