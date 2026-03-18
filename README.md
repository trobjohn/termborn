# termborn

Terminal-native plotting for lightweight EDA.

`termborn` is a small, seaborn-ish plotting library for people who live in a terminal, a REPL, Neovim, SSH, or a Kitty split and want fast visual feedback without spinning up a notebook or a full GUI plotting stack.

The joke is that you can write:

```python
import termborn as sns
```

and keep roughly the same calling style you would use with seaborn for a small, safe subset of plots.

This is not trying to be a full seaborn clone. It is trying to be fast, cute, useful, and honest about terminal constraints.

## What It Supports

- `scatterplot`
- `histplot`
- `kdeplot`
- `ecdfplot`
- `heatmap`
- `set_theme`
- `color_palette`

Current highlights:

- Braille scatter rendering for higher apparent resolution
- Density-aware scatter brightness as a terminal stand-in for alpha
- CMY-style hue collision logic for multi-series scatter and ECDF
- 1D histograms with block characters
- 2D `histplot(x=..., y=...)` density fill with shade characters
- KDE and ECDF plots with terminal-friendly line rendering
- Heatmaps with quantized yellow-to-green cell coloring
- Unicode and color fallbacks when the terminal is limited

## Intended Use

This is for lightweight exploratory work, especially in a split terminal workflow.

Good fit:

- checking distributions
- looking at overplotting
- quick feature sanity checks
- exploring relationships while staying inside Neovim or a REPL

Not the goal:

- publication plots
- exact seaborn compatibility
- a matplotlib-style figure/axes framework

## Example

```python
import numpy as np
import pandas as pd
import termborn as sns

rng = np.random.default_rng(7)
df = pd.DataFrame({
    "x": np.linspace(0, 10, 200),
    "y": np.sin(np.linspace(0, 10, 200)),
    "group": np.where(np.arange(200) < 100, "a", "b"),
    "value": np.r_[rng.normal(0, 1, 100), rng.normal(2.5, 0.6, 100)],
})

sns.scatterplot(data=df, x="x", y="y", hue="group", title="Scatter")
sns.histplot(data=df, x="value", title="Histogram")
sns.kdeplot(data=df, x="value", hue="group", title="KDE")
sns.ecdfplot(data=df, x="value", hue="group", title="ECDF")
sns.histplot(data=df, x="x", y="y", title="2D density")

matrix = np.corrcoef(rng.normal(size=(8, 100)))
sns.heatmap(matrix, title="Heatmap")
```

## API Notes

The API is seaborn-flavored, not seaborn-faithful.

- Common calls like `sns.histplot(x)` and `sns.scatterplot(x, y)` work
- `data=...`, `x=...`, `y=...`, and `hue=...` work for the supported plot types
- Many unsupported kwargs are quietly ignored on purpose
- Plot calls render immediately to stdout
- Each call uses a fresh canvas, so plots do not layer on top of one another

## Plot Notes

### `scatterplot`

- Uses braille characters for sub-cell precision
- Supports `hue`
- Density brightening acts as a rough alpha replacement

### `histplot`

- `histplot(x=...)` renders a 1D histogram
- `histplot(x=..., y=...)` renders a shaded 2D density plot
- Histogram hue support is intentionally not a focus right now

### `kdeplot`

- 1D KDE only
- Vertical axis scales to the actual sampled density peak

### `ecdfplot`

- Supports `hue`
- Uses the same collision logic as scatter-style plots

### `heatmap`

- Expects a 2D matrix or DataFrame
- Uses full-block cells with quantized color

## Theme Control

```python
sns.set_theme(color=False)
sns.set_theme(unicode=False)
sns.set_theme(colorblind=True)
```

By default, `termborn` auto-detects terminal color and Unicode support. Explicit `set_theme(...)` values override that detection.

## Dependencies

- `numpy`
- `pandas`
- `scipy`

## Workflow Notes

This project is especially nice in:

- Neovim with a REPL split
- Kitty or other modern terminals with good Unicode/color support
- remote shells where GUI plotting is annoying

The defaults are intentionally tuned for terminal panes rather than giant notebook cells.

## Status

This is a small, intentionally constrained v1-style project.

That is a feature, not a bug.

The library already covers a useful terminal EDA loop, and the goal is to keep it sharp rather than let it sprawl into a half-clone of seaborn.
