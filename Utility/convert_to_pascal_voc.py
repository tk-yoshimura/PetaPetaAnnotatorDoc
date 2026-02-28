# Copyright (c) T.Yoshimura
# https://github.com/tk-yoshimura


from __future__ import annotations

import argparse

from polygon_to_bbox_util import polygon_to_bbox, polygon_to_voc_polygon
from convert_to_pascal_voc_kernel import (
    class_polygons_to_pascal_voc_tree,
    convert_directory_to_pascal_voc,
    convert_image_xml_pair_to_pascal_voc,
    convert_png_xml_pair_to_pascal_voc,
    save_pascal_voc,
    xml_annotations_to_pascal_voc,
)
from get_image_size import read_image_size, read_jpeg_size, read_png_size
from load_annotation import discover_image_annotation_pairs, discover_png_annotation_pairs


__all__ = [
    "read_png_size",
    "read_jpeg_size",
    "read_image_size",
    "polygon_to_bbox",
    "polygon_to_voc_polygon",
    "class_polygons_to_pascal_voc_tree",
    "save_pascal_voc",
    "xml_annotations_to_pascal_voc",
    "convert_image_xml_pair_to_pascal_voc",
    "discover_image_annotation_pairs",
    "convert_png_xml_pair_to_pascal_voc",
    "discover_png_annotation_pairs",
    "convert_directory_to_pascal_voc",
    "main",
]


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

