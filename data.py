"""Input normalization helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SeriesData:
    label: str
    x: np.ndarray
    y: np.ndarray | None = None


def resolve_xy(data=None, x=None, y=None, hue=None):
    x_values = _resolve_vector(data, x, axis_name="x")
    y_values = None if y is None else _resolve_vector(data, y, axis_name="y")
    hue_values = None if hue is None else _resolve_vector(data, hue, axis_name="hue")

    length = len(x_values)
    if y_values is not None and len(y_values) != length:
        raise ValueError("x and y must have the same length")
    if hue_values is not None and len(hue_values) != length:
        raise ValueError("hue must have the same length as x")

    if y_values is None:
        mask = ~_is_missing(x_values)
    else:
        mask = ~( _is_missing(x_values) | _is_missing(y_values))
    if hue_values is not None:
        mask = mask & ~_is_missing(hue_values)

    x_values = x_values[mask]
    if y_values is not None:
        y_values = y_values[mask]
    if hue_values is not None:
        hue_values = hue_values[mask]

    return x_values, y_values, hue_values


def split_by_hue(x_values, y_values=None, hue_values=None):
    if hue_values is None:
        return [SeriesData(label="series", x=_as_float_array(x_values), y=None if y_values is None else _as_float_array(y_values))]

    labels = []
    order = {}
    for value in hue_values.tolist():
        key = str(value)
        if key not in order:
            order[key] = len(labels)
            labels.append(key)

    series = []
    for label in labels:
        mask = np.array([str(v) == label for v in hue_values], dtype=bool)
        xs = _as_float_array(x_values[mask])
        ys = None if y_values is None else _as_float_array(y_values[mask])
        series.append(SeriesData(label=label, x=xs, y=ys))
    return series


def _resolve_vector(data, value, axis_name):
    if value is None:
        raise ValueError(f"{axis_name} is required")
    if isinstance(value, str) and data is not None:
        if hasattr(data, "__getitem__"):
            return _to_array(data[value])
        raise ValueError(f"data does not support column lookup for {value!r}")
    return _to_array(value)


def _to_array(value):
    if hasattr(value, "to_numpy"):
        value = value.to_numpy()
    array = np.asarray(value)
    if array.ndim == 0:
        return array.reshape(1)
    if array.ndim == 1:
        return array
    if array.ndim == 2 and 1 in array.shape:
        return array.reshape(-1)
    raise ValueError("termborn expects 1D data vectors")


def _as_float_array(value):
    return np.asarray(value, dtype=float).reshape(-1)


def _is_missing(values):
    if np.issubdtype(values.dtype, np.number):
        return np.isnan(values)
    return np.array([v is None or v != v for v in values], dtype=bool)
