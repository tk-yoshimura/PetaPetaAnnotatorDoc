# Copyright (c) T.Yoshimura
# https://github.com/tk-yoshimura


import numpy as np

from bezier_interpolation import interpolate_closed_curve, interpolate_open_curve


SAMPLES_PER_SEGMENT = 16


def _normalize(v):
    n = np.linalg.norm(v)
    if n > 0.0:
        return v / n
    return np.array([0.0, 0.0], dtype=float)


def _compute_tangents(polyline):
    n = polyline.shape[0]
    tangents = np.zeros((n, 2), dtype=float)

    if n == 0:
        return tangents
    if n == 1:
        tangents[0] = np.array([1.0, 0.0], dtype=float)
        return tangents

    tangents[0] = _normalize(polyline[1] - polyline[0])
    tangents[-1] = _normalize(polyline[-1] - polyline[-2])

    for i in range(1, n - 1):
        tangents[i] = _normalize(polyline[i + 1] - polyline[i - 1])

    for i in range(n):
        if np.linalg.norm(tangents[i]) == 0.0:
            if i > 0 and np.linalg.norm(tangents[i - 1]) > 0.0:
                tangents[i] = tangents[i - 1]
            else:
                tangents[i] = np.array([1.0, 0.0], dtype=float)

    return tangents


def bezier_closed_region(points, tension=0.5, samples_per_segment=SAMPLES_PER_SEGMENT):
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2:
        raise ValueError("points must be shape (N, 2)")
    if points.shape[0] == 0:
        return np.empty((0, 2), dtype=float)

    curve = interpolate_closed_curve(points, tension=tension, samples_per_segment=samples_per_segment)

    if curve.shape[0] >= 2 and np.allclose(curve[0], curve[-1]):
        curve = curve[:-1]

    return curve


def bezier_open_stroke_region(
    points,
    stroke_width,
    tension=0.5,
    samples_per_segment=SAMPLES_PER_SEGMENT,
):
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2:
        raise ValueError("points must be shape (N, 2)")
    if points.shape[0] == 0:
        return np.empty((0, 2), dtype=float)
    if stroke_width < 0.0:
        raise ValueError("stroke_width must be >= 0")

    centerline = interpolate_open_curve(points, tension=tension, samples_per_segment=samples_per_segment)

    if centerline.shape[0] == 1 or stroke_width == 0.0:
        return centerline.copy()

    tangents = _compute_tangents(centerline)
    normals = np.column_stack((-tangents[:, 1], tangents[:, 0]))

    half = stroke_width * 0.5
    left = centerline + normals * half
    right = centerline - normals * half

    polygon = np.vstack((left, right[::-1]))

    return polygon
