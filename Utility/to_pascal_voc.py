# Copyright (c) T.Yoshimura
# https://github.com/tk-yoshimura


from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Sequence
import xml.etree.ElementTree as ET
from xml.dom import minidom

import numpy as np

from xml_to_polygon import xml_to_class_polygon_arrays


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SOI = b"\xff\xd8"
JPEG_EOI = b"\xff\xd9"


def _ensure_polygon_array(polygon: Sequence[Sequence[float]] | np.ndarray) -> np.ndarray:
    arr = np.asarray(polygon, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 2:
        raise ValueError("polygon must be shape (N, 2)")
    if arr.shape[0] < 1:
        raise ValueError("polygon must contain at least one point")
    return arr


def read_png_size(png_path: str | Path) -> tuple[int, int]:
    png_path = Path(png_path)

    with png_path.open("rb") as f:
        header = f.read(24)

    if len(header) < 24 or header[:8] != PNG_SIGNATURE:
        raise ValueError(f"Invalid PNG file: {png_path}")

    width = int.from_bytes(header[16:20], byteorder="big", signed=False)
    height = int.from_bytes(header[20:24], byteorder="big", signed=False)

    return width, height


def read_jpeg_size(jpeg_path: str | Path) -> tuple[int, int]:
    jpeg_path = Path(jpeg_path)

    with jpeg_path.open("rb") as f:
        if f.read(2) != JPEG_SOI:
            raise ValueError(f"Invalid JPEG file: {jpeg_path}")

        while True:
            marker_prefix = f.read(1)
            if not marker_prefix:
                break
            if marker_prefix != b"\xff":
                continue

            marker = f.read(1)
            while marker == b"\xff":
                marker = f.read(1)
            if not marker:
                break

            # Standalone markers without segment length.
            if marker in {b"\x01"} or b"\xd0" <= marker <= b"\xd9":
                if marker == JPEG_EOI[1:2]:
                    break
                continue

            segment_len_bytes = f.read(2)
            if len(segment_len_bytes) != 2:
                break

            segment_len = int.from_bytes(segment_len_bytes, byteorder="big", signed=False)
            if segment_len < 2:
                raise ValueError(f"Invalid JPEG segment length in: {jpeg_path}")

            # SOF markers that contain dimensions.
            if marker in {
                b"\xc0",
                b"\xc1",
                b"\xc2",
                b"\xc3",
                b"\xc5",
                b"\xc6",
                b"\xc7",
                b"\xc9",
                b"\xca",
                b"\xcb",
                b"\xcd",
                b"\xce",
                b"\xcf",
            }:
                sof = f.read(5)
                if len(sof) != 5:
                    break
                height = int.from_bytes(sof[1:3], byteorder="big", signed=False)
                width = int.from_bytes(sof[3:5], byteorder="big", signed=False)
                return width, height

            f.seek(segment_len - 2, 1)

    raise ValueError(f"Could not read JPEG size from: {jpeg_path}")


def read_image_size(image_path: str | Path) -> tuple[int, int]:
    image_path = Path(image_path)
    suffix = image_path.suffix.lower()

    if suffix == ".png":
        return read_png_size(image_path)
    if suffix in {".jpg", ".jpeg"}:
        return read_jpeg_size(image_path)

    raise ValueError(f"Unsupported image extension: {image_path.suffix}")


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
    class_polygons = xml_to_class_polygon_arrays(input_xml_path)
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
    image_path = Path(image_path)
    annotation_xml_path = Path(annotation_xml_path)

    width, height = read_image_size(image_path)

    xml_annotations_to_pascal_voc(
        annotation_xml_path,
        output_voc_path,
        filename=image_path.name,
        width=width,
        height=height,
        depth=depth,
        folder=image_path.parent.name,
        image_path=str(image_path.resolve()),
        database=database,
    )


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


def discover_png_annotation_pairs(input_dir: str | Path) -> tuple[list[tuple[Path, Path]], list[Path]]:
    # Backward-compatible alias. Discovery now includes PNG/JPEG.
    return discover_image_annotation_pairs(input_dir)


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


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert class/polygon annotations to Pascal VOC XML (segmentation format).",
    )

    parser.add_argument(
        "--input-dir",
        help="Root directory to scan for *.png/*.jpg/*.jpeg and *_annotations.xml pairs",
    )
    parser.add_argument("--output-dir", help="Output directory for Pascal VOC XML files (default: input-dir)")

    parser.add_argument("--input-xml", help="Input annotation XML path (single mode)")
    parser.add_argument("--output-xml", help="Output Pascal VOC XML path (single mode)")
    parser.add_argument("--filename", help="Image filename for VOC <filename> (single mode)")
    parser.add_argument("--width", type=int, help="Image width (single mode)")
    parser.add_argument("--height", type=int, help="Image height (single mode)")

    parser.add_argument("--depth", type=int, default=3, help="Image depth (default: 3)")
    parser.add_argument("--folder", default="", help="VOC <folder> (single mode)")
    parser.add_argument("--image-path", default="", help="VOC <path> (single mode)")
    parser.add_argument("--database", default="Unknown", help="VOC <source>/<database>")

    return parser


def main() -> None:
    args = _build_arg_parser().parse_args()

    if args.input_dir:
        written, missing = convert_directory_to_pascal_voc(
            args.input_dir,
            output_dir=args.output_dir,
            depth=args.depth,
            database=args.database,
        )

        print(f"converted: {len(written)}")
        for p in written:
            print(f"  {p}")

        if missing:
            print(f"missing annotation xml for {len(missing)} image files:")
            for p in missing:
                print(f"  {p}")

        return

    required = [args.input_xml, args.output_xml, args.filename, args.width, args.height]
    if any(v is None for v in required):
        raise SystemExit(
            "single mode requires --input-xml --output-xml --filename --width --height, "
            "or use --input-dir for batch mode"
        )

    xml_annotations_to_pascal_voc(
        args.input_xml,
        args.output_xml,
        filename=args.filename,
        width=args.width,
        height=args.height,
        depth=args.depth,
        folder=args.folder,
        image_path=args.image_path,
        database=args.database,
    )


if __name__ == "__main__":
    main()
