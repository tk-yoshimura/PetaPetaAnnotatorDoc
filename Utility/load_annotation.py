# Copyright (c) T.Yoshimura
# https://github.com/tk-yoshimura

from __future__ import annotations

from pathlib import Path

from get_image_size import read_image_size
from xml_to_polygon import xml_to_class_polygon_arrays


def load_class_polygons_from_xml(input_xml_path: str | Path):
    return xml_to_class_polygon_arrays(input_xml_path)


def load_image_annotation_context(
    image_path: str | Path,
    annotation_xml_path: str | Path,
) -> dict[str, object]:
    image_path = Path(image_path)
    annotation_xml_path = Path(annotation_xml_path)

    width, height = read_image_size(image_path)
    class_polygons = load_class_polygons_from_xml(annotation_xml_path)

    return {
        "class_polygons": class_polygons,
        "filename": image_path.name,
        "width": width,
        "height": height,
        "folder": image_path.parent.name,
        "image_path": str(image_path.resolve()),
    }


def discover_image_annotation_pairs(input_dir: str | Path) -> tuple[list[tuple[Path, Path]], list[Path]]:
    input_dir = Path(input_dir)

    pairs: list[tuple[Path, Path]] = []
    missing_annotations: list[Path] = []

    image_paths = sorted(
        p
        for p in input_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}
    )

    for image_path in image_paths:
        annotation_xml = image_path.with_name(f"{image_path.stem}_annotations.xml")
        if annotation_xml.exists():
            pairs.append((image_path, annotation_xml))
        else:
            missing_annotations.append(image_path)

    return pairs, missing_annotations


def discover_png_annotation_pairs(input_dir: str | Path) -> tuple[list[tuple[Path, Path]], list[Path]]:
    # Backward-compatible alias. Discovery now includes PNG/JPEG.
    return discover_image_annotation_pairs(input_dir)

