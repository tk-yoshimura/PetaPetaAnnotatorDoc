# Copyright (c) T.Yoshimura
# https://github.com/tk-yoshimura

from __future__ import annotations

from typing import Sequence

import numpy as np


def _ensure_polygon_array(polygon: Sequence[Sequence[float]] | np.ndarray) -> np.ndarray:
    arr = np.asarray(polygon, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 2:
        raise ValueError("polygon must be shape (N, 2)")
    if arr.shape[0] < 1:
        raise ValueError("polygon must contain at least one point")
    return arr


def polygon_to_bbox(
    polygon: Sequence[Sequence[float]] | np.ndarray,
    *,
    image_width: int | None = None,
    image_height: int | None = None,
    min_size: int = 1,
) -> tuple[int, int, int, int]:
    pts = _ensure_polygon_array(polygon)

    xmin = float(np.min(pts[:, 0]))
    ymin = float(np.min(pts[:, 1]))
    xmax = float(np.max(pts[:, 0]))
    ymax = float(np.max(pts[:, 1]))

    if image_width is not None:
        xmin = max(0.0, min(xmin, float(image_width - 1)))
        xmax = max(0.0, min(xmax, float(image_width - 1)))
    if image_height is not None:
        ymin = max(0.0, min(ymin, float(image_height - 1)))
        ymax = max(0.0, min(ymax, float(image_height - 1)))

    ixmin = int(np.floor(xmin))
    iymin = int(np.floor(ymin))
    ixmax = int(np.ceil(xmax))
    iymax = int(np.ceil(ymax))

    if ixmax <= ixmin:
        ixmax = ixmin + max(1, min_size)
    if iymax <= iymin:
        iymax = iymin + max(1, min_size)

    if image_width is not None:
        ixmin = max(0, min(ixmin, image_width - 1))
        ixmax = max(1, min(ixmax, image_width))
        if ixmax <= ixmin:
            ixmin = max(0, min(ixmin - 1, image_width - 1))
            ixmax = min(image_width, ixmin + 1)

    if image_height is not None:
        iymin = max(0, min(iymin, image_height - 1))
        iymax = max(1, min(iymax, image_height))
        if iymax <= iymin:
            iymin = max(0, min(iymin - 1, image_height - 1))
            iymax = min(image_height, iymin + 1)

    return ixmin, iymin, ixmax, iymax


def polygon_to_voc_polygon(
    polygon: Sequence[Sequence[float]] | np.ndarray,
    *,
    image_width: int | None = None,
    image_height: int | None = None,
) -> np.ndarray:
    pts = _ensure_polygon_array(polygon).copy()

    if image_width is not None:
        pts[:, 0] = np.clip(pts[:, 0], 0.0, float(image_width - 1))
    if image_height is not None:
        pts[:, 1] = np.clip(pts[:, 1], 0.0, float(image_height - 1))

    return np.rint(pts).astype(int)
