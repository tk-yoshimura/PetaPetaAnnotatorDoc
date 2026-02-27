import numpy as np

def bezier_open_curve(points, tension):
    points = np.asarray(points, dtype=float)
    if len(points) == 0:
        return np.empty((0, 2), dtype=float)
    if len(points) == 1:
        return points.copy()

    n = len(points)
    weight = tension / 2.0

    pts = np.empty((n * 3 - 2, 2), dtype=float)
    pts[0::3] = points

    if n == 2:
        pts[1], pts[2] = control_point(0.0, 0.0, points[0], points[0], points[1], points[1])
    else:
        pts[1], pts[2] = control_point(0.0, weight, points[0], points[0], points[1], points[2])

        for i in range(1, n - 2):
            pts[i * 3 + 1], pts[i * 3 + 2] = control_point(
                weight, weight, points[i - 1], points[i], points[i + 1], points[i + 2]
            )

        pts[-3], pts[-2] = control_point(weight, 0.0, points[-3], points[-2], points[-1], points[-1])

    return pts


def bezier_closed_curve(points, tension):
    points = np.asarray(points, dtype=float)
    if len(points) == 0:
        return np.empty((0, 2), dtype=float)
    if len(points) == 1:
        return points.copy()

    n = len(points)
    weight = tension / 2.0

    pts = np.empty((n * 3 + 1, 2), dtype=float)
    pts[0 : n * 3 : 3] = points
    pts[n * 3] = points[0]

    if n == 2:
        pts[1], pts[2] = control_point(0.0, 0.0, points[0], points[0], points[1], points[1])
        pts[4], pts[5] = pts[2], pts[1]
    else:
        pts[1], pts[2] = control_point(weight, weight, points[-1], points[0], points[1], points[2])

        for i in range(1, n - 2):
            pts[i * 3 + 1], pts[i * 3 + 2] = control_point(
                weight, weight, points[i - 1], points[i], points[i + 1], points[i + 2]
            )

        pts[-6], pts[-5] = control_point(weight, weight, points[-3], points[-2], points[-1], points[0])
        pts[-3], pts[-2] = control_point(weight, weight, points[-2], points[-1], points[0], points[1])

    return pts


def control_point(weight1, weight2, pt0, pt1, pt2, pt3):
    v12 = pt2 - pt1
    n12 = np.linalg.norm(v12)

    if not (n12 > 0.0):
        return pt1.copy(), pt2.copy()

    v02 = pt2 - pt0
    v31 = pt1 - pt3

    c1 = limited_overshoot_control_point(weight1, pt1, n12, v02)
    c2 = limited_overshoot_control_point(weight2, pt2, n12, v31)

    return c1, c2


def limited_overshoot_control_point(weight, pt, interval_length, direction):
    direction_length = np.linalg.norm(direction)

    if direction_length > 0.0:
        direction_norm_limited = direction * min(1.0, interval_length / direction_length * 2.0)
        return pt + weight * direction_norm_limited

    return pt.copy()