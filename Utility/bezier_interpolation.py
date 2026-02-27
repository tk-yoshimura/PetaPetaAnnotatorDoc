import numpy as np

from bezier_control_point import bezier_closed_curve, bezier_open_curve


def _cubic_bezier(p0, c1, c2, p1, t):
    u = 1.0 - t
    return (u ** 3) * p0 + 3.0 * (u ** 2) * t * c1 + 3.0 * u * (t ** 2) * c2 + (t ** 3) * p1


def interpolate_from_control_points(control_points, samples_per_segment=20):
    control_points = np.asarray(control_points, dtype=float)

    if control_points.ndim != 2 or control_points.shape[1] != 2:
        raise ValueError("control_points must be shape (N, 2)")
    if control_points.shape[0] < 4:
        return control_points.copy()
    if (control_points.shape[0] - 1) % 3 != 0:
        raise ValueError("control_points length must satisfy (N - 1) % 3 == 0")
    if samples_per_segment < 1:
        raise ValueError("samples_per_segment must be >= 1")

    segment_count = (control_points.shape[0] - 1) // 3
    result = []

    for i in range(segment_count):
        p0 = control_points[i * 3]
        c1 = control_points[i * 3 + 1]
        c2 = control_points[i * 3 + 2]
        p1 = control_points[i * 3 + 3]

        t_values = np.linspace(0.0, 1.0, samples_per_segment + 1)
        if i > 0:
            t_values = t_values[1:]

        for t in t_values:
            result.append(_cubic_bezier(p0, c1, c2, p1, t))

    return np.asarray(result, dtype=float)


def interpolate_open_curve(points, tension=0.5, samples_per_segment=20):
    control_points = bezier_open_curve(points, tension)
    return interpolate_from_control_points(control_points, samples_per_segment=samples_per_segment)


def interpolate_closed_curve(points, tension=0.5, samples_per_segment=20):
    control_points = bezier_closed_curve(points, tension)
    return interpolate_from_control_points(control_points, samples_per_segment=samples_per_segment)
