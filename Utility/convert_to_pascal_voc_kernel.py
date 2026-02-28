# Copyright (c) T.Yoshimura
# https://github.com/tk-yoshimura

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence
import xml.etree.ElementTree as ET
from xml.dom import minidom

import numpy as np

from polygon_to_bbox_util import polygon_to_bbox, polygon_to_voc_polygon
from load_annotation import (
    discover_image_annotation_pairs,
    load_class_polygons_from_xml,
    load_image_annotation_context,
)


def class_polygons_to_pascal_voc_tree(
    class_polygons: Iterable[tuple[str, Sequence[Sequence[float]] | np.ndarray]],
    *,
    filename: str,
    width: int,
    height: int,
    depth: int = 3,
    folder: str = "",
    image_path: str = "",
    database: str = "Unknown",
) -> ET.ElementTree:
    root = ET.Element("annotation")

    ET.SubElement(root, "folder").text = folder
    ET.SubElement(root, "filename").text = filename
    ET.SubElement(root, "path").text = image_path

    source = ET.SubElement(root, "source")
    ET.SubElement(source, "database").text = database

    size = ET.SubElement(root, "size")
    ET.SubElement(size, "width").text = str(int(width))
    ET.SubElement(size, "height").text = str(int(height))
    ET.SubElement(size, "depth").text = str(int(depth))

    ET.SubElement(root, "segmented").text = "1"

    for class_name, polygon in class_polygons:
        voc_poly = polygon_to_voc_polygon(
            polygon,
            image_width=width,
            image_height=height,
        )
        xmin, ymin, xmax, ymax = polygon_to_bbox(
            polygon,
            image_width=width,
            image_height=height,
        )

        obj = ET.SubElement(root, "object")
        ET.SubElement(obj, "name").text = class_name
        ET.SubElement(obj, "pose").text = "Unspecified"
        ET.SubElement(obj, "truncated").text = "0"
        ET.SubElement(obj, "difficult").text = "0"

        # Keep bbox for broad VOC parser compatibility, and add polygon for segmentation.
        bndbox = ET.SubElement(obj, "bndbox")
        ET.SubElement(bndbox, "xmin").text = str(xmin)
        ET.SubElement(bndbox, "ymin").text = str(ymin)
        ET.SubElement(bndbox, "xmax").text = str(xmax)
        ET.SubElement(bndbox, "ymax").text = str(ymax)

        polygon_element = ET.SubElement(obj, "polygon")
        for i, (x, y) in enumerate(voc_poly, start=1):
            ET.SubElement(polygon_element, f"x{i}").text = str(int(x))
            ET.SubElement(polygon_element, f"y{i}").text = str(int(y))

    return ET.ElementTree(root)


def save_pascal_voc(tree: ET.ElementTree, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    xml_bytes = ET.tostring(tree.getroot(), encoding="utf-8")
    pretty = minidom.parseString(xml_bytes).toprettyxml(indent="  ", encoding="utf-8")
    output_path.write_bytes(pretty)


def xml_annotations_to_pascal_voc(
    input_xml_path: str | Path,
    output_voc_path: str | Path,
    *,
    filename: str,
    width: int,
    height: int,
    depth: int = 3,
    folder: str = "",
    image_path: str = "",
    database: str = "Unknown",
) -> None:
    class_polygons = load_class_polygons_from_xml(input_xml_path)
    tree = class_polygons_to_pascal_voc_tree(
        class_polygons,
        filename=filename,
        width=width,
        height=height,
        depth=depth,
        folder=folder,
        image_path=image_path,
        database=database,
    )
    save_pascal_voc(tree, output_voc_path)


def convert_image_xml_pair_to_pascal_voc(
    image_path: str | Path,
    annotation_xml_path: str | Path,
    output_voc_path: str | Path,
    *,
    depth: int = 3,
    database: str = "Unknown",
) -> None:
    context = load_image_annotation_context(image_path, annotation_xml_path)

    tree = class_polygons_to_pascal_voc_tree(
        context["class_polygons"],
        filename=str(context["filename"]),
        width=int(context["width"]),
        height=int(context["height"]),
        depth=depth,
        folder=str(context["folder"]),
        image_path=str(context["image_path"]),
        database=database,
    )
    save_pascal_voc(tree, output_voc_path)


def convert_png_xml_pair_to_pascal_voc(
    png_path: str | Path,
    annotation_xml_path: str | Path,
    output_voc_path: str | Path,
    *,
    depth: int = 3,
    database: str = "Unknown",
) -> None:
    # Backward-compatible alias. Input can now be PNG/JPEG as well.
    convert_image_xml_pair_to_pascal_voc(
        png_path,
        annotation_xml_path,
        output_voc_path,
        depth=depth,
        database=database,
    )


def convert_directory_to_pascal_voc(
    input_dir: str | Path,
    output_dir: str | Path | None = None,
    *,
    depth: int = 3,
    database: str = "Unknown",
) -> tuple[list[Path], list[Path]]:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir) if output_dir is not None else input_dir

    pairs, missing_annotations = discover_image_annotation_pairs(input_dir)

    written: list[Path] = []

    for image_path, annotation_xml in pairs:
        rel_parent = image_path.parent.relative_to(input_dir)
        output_xml = output_dir / rel_parent / f"{image_path.stem}.xml"

        convert_image_xml_pair_to_pascal_voc(
            image_path,
            annotation_xml,
            output_xml,
            depth=depth,
            database=database,
        )
        written.append(output_xml)

    return written, missing_annotations

