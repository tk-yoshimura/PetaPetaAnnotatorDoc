# Copyright (c) T.Yoshimura
# https://github.com/tk-yoshimura

from __future__ import annotations

from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SOI = b"\xff\xd8"
JPEG_EOI = b"\xff\xd9"


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

