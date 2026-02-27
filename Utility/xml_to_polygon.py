# Copyright (c) T.Yoshimura
# https://github.com/tk-yoshimura


from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

from bezier_region import (
    SAMPLES_PER_SEGMENT,
    bezier_closed_region,
    bezier_open_stroke_region,
)


@dataclass
class AnnotationPolygonItem:
    class_name: str
    shape: str
    polygon: np.ndarray


def _parse_point_element(point_element: ET.Element) -> tuple[float, float]:
    x = float(point_element.attrib["X"])
    y = float(point_element.attrib["Y"])
    return x, y


def _parse_points(parent: ET.Element) -> np.ndarray:
    points_container = parent.find("Points")
    if points_container is None:
        raise ValueError("Points element is missing")

    points = [_parse_point_element(pt) for pt in points_container.findall("Point")]
    return np.asarray(points, dtype=float)


def _polygon_from_rect(shape_element: ET.Element) -> np.ndarray:
    x = float(shape_element.attrib["X"])
    y = float(shape_element.attrib["Y"])
    width = float(shape_element.attrib["Width"])
    height = float(shape_element.attrib["Height"])

    return np.asarray(
        [
            [x, y],
            [x + width, y],
            [x + width, y + height],
            [x, y + height],
        ],
        dtype=float,
    )


def _polygon_from_rotated_rect(shape_element: ET.Element) -> np.ndarray:
    v0 = np.asarray([float(shape_element.attrib["V0X"]), float(shape_element.attrib["V0Y"])], dtype=float)
    v1 = np.asarray([float(shape_element.attrib["V1X"]), float(shape_element.attrib["V1Y"])], dtype=float)
    width = float(shape_element.attrib["Width"])

    direction = v0 - v1
    length = np.linalg.norm(direction)
    if length > 0.0:
        norm = direction / length * (width / 2.0)
    else:
        norm = np.asarray([0.0, 0.0], dtype=float)

    p0 = np.asarray([v0[0] - norm[1], v0[1] + norm[0]], dtype=float)
    p1 = np.asarray([v1[0] - norm[1], v1[1] + norm[0]], dtype=float)
    p2 = np.asarray([v1[0] + norm[1], v1[1] - norm[0]], dtype=float)
    p3 = np.asarray([v0[0] + norm[1], v0[1] - norm[0]], dtype=float)

    return np.asarray([p0, p1, p2, p3], dtype=float)


def _polygon_from_circle(shape_element: ET.Element, segments: int) -> np.ndarray:
    x = float(shape_element.attrib["X"])
    y = float(shape_element.attrib["Y"])
    radius = float(shape_element.attrib["Radius"])

    t = np.linspace(0.0, 2.0 * np.pi, segments, endpoint=False)
    pts = np.column_stack((x + radius * np.cos(t), y + radius * np.sin(t)))

    return pts.astype(float)


def _polygon_from_ellipse(shape_element: ET.Element, segments: int) -> np.ndarray:
    v0 = np.asarray([float(shape_element.attrib["V0X"]), float(shape_element.attrib["V0Y"])], dtype=float)
    v1 = np.asarray([float(shape_element.attrib["V1X"]), float(shape_element.attrib["V1Y"])], dtype=float)
    width = float(shape_element.attrib["Width"])

    center = (v0 + v1) / 2.0
    axis_x = np.linalg.norm(v1 - v0) / 2.0
    axis_y = width / 2.0
    angle = np.arctan2(v1[1] - v0[1], v1[0] - v0[0])

    t = np.linspace(0.0, 2.0 * np.pi, segments, endpoint=False)
    local = np.column_stack((axis_x * np.cos(t), axis_y * np.sin(t)))

    c = np.cos(angle)
    s = np.sin(angle)
    rot = np.asarray([[c, -s], [s, c]], dtype=float)

    return (local @ rot.T + center).astype(float)


def _polygon_from_curve(shape_element: ET.Element, bezier_samples_per_segment: int) -> np.ndarray:
    stroke_width = float(shape_element.attrib["StrokeWidth"])
    points = _parse_points(shape_element)

    return bezier_open_stroke_region(
        points,
        stroke_width=stroke_width,
        tension=0.5,
        samples_per_segment=bezier_samples_per_segment,
    )


def _polygon_from_closed_curve(shape_element: ET.Element, bezier_samples_per_segment: int) -> np.ndarray:
    points = _parse_points(shape_element)

    return bezier_closed_region(
        points,
        tension=0.5,
        samples_per_segment=bezier_samples_per_segment,
    )


def _polygon_from_geometry(
    shape_element: ET.Element,
    circle_segments: int,
    ellipse_segments: int,
    bezier_samples_per_segment: int,
) -> np.ndarray:
    shape = shape_element.tag

    if shape == "Point":
        x = float(shape_element.attrib["X"])
        y = float(shape_element.attrib["Y"])
        return np.asarray([[x, y]], dtype=float)
    if shape == "Polygon":
        return _parse_points(shape_element)
    if shape == "Rect":
        return _polygon_from_rect(shape_element)
    if shape == "RotatedRect":
        return _polygon_from_rotated_rect(shape_element)
    if shape == "Circle":
        return _polygon_from_circle(shape_element, segments=circle_segments)
    if shape == "Ellipse":
        return _polygon_from_ellipse(shape_element, segments=ellipse_segments)
    if shape == "Curve":
        return _polygon_from_curve(shape_element, bezier_samples_per_segment=bezier_samples_per_segment)
    if shape == "ClosedCurve":
        return _polygon_from_closed_curve(shape_element, bezier_samples_per_segment=bezier_samples_per_segment)

    raise ValueError(f"Unsupported geometry shape: {shape}")


def xml_to_polygon_items(
    xml_path: str | Path,
    *,
    circle_segments: int = 64,
    ellipse_segments: int = 64,
    bezier_samples_per_segment: int = SAMPLES_PER_SEGMENT,
) -> list[AnnotationPolygonItem]:
    tree = ET.parse(Path(xml_path))
    root = tree.getroot()

    items: list[AnnotationPolygonItem] = []

    for entry in root.findall("AnnotationEntry"):
        class_name = ""
        class_detail = entry.find("ClassDetail")
        if class_detail is not None:
            class_name = class_detail.attrib.get("Name", "")

        geometry = entry.find("Geometry")
        if geometry is None:
            continue

        shape_element = next(iter(geometry), None)
        if shape_element is None:
            continue

        polygon = _polygon_from_geometry(
            shape_element,
            circle_segments=circle_segments,
            ellipse_segments=ellipse_segments,
            bezier_samples_per_segment=bezier_samples_per_segment,
        )

        items.append(
            AnnotationPolygonItem(
                class_name=class_name,
                shape=shape_element.tag,
                polygon=np.asarray(polygon, dtype=float),
            )
        )

    return items


def xml_to_class_polygon_arrays(
    xml_path: str | Path,
    *,
    circle_segments: int = 64,
    ellipse_segments: int = 64,
    bezier_samples_per_segment: int = SAMPLES_PER_SEGMENT,
) -> list[tuple[str, np.ndarray]]:
    items = xml_to_polygon_items(
        xml_path,
        circle_segments=circle_segments,
        ellipse_segments=ellipse_segments,
        bezier_samples_per_segment=bezier_samples_per_segment,
    )
    return [(item.class_name, item.polygon) for item in items]


def xml_to_class_polygon_lists(
    xml_path: str | Path,
    *,
    circle_segments: int = 64,
    ellipse_segments: int = 64,
    bezier_samples_per_segment: int = SAMPLES_PER_SEGMENT,
) -> list[tuple[str, list[list[float]]]]:
    result: list[tuple[str, list[list[float]]]] = []

    for class_name, polygon in xml_to_class_polygon_arrays(
        xml_path,
        circle_segments=circle_segments,
        ellipse_segments=ellipse_segments,
        bezier_samples_per_segment=bezier_samples_per_segment,
    ):
        result.append((class_name, polygon.tolist()))

    return result
