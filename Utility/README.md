# Utility

Utilities for converting annotation XML into Pascal VOC XML and visualizing results.

## Language

[English](README.md)
[日本語](README_JP.md)

## Overview

This folder contains helper scripts and notebooks for:

- Converting annotation XML (`*_annotations.xml`) to Pascal VOC XML
- Converting various geometry annotations into polygon arrays
- Visualizing Pascal VOC XML on top of images

## Files

- `convert_to_pascal_voc.py`
  - CLI entry point and compatibility import surface.
- `get_image_size.py`
  - Image-size readers for `.png` / `.jpg` / `.jpeg`.
- `polygon_to_bbox_util.py`
  - `polygon_to_bbox` and polygon coordinate normalization for VOC.
- `load_annotation.py`
  - XML/image loading and image-annotation pair discovery.
- `convert_to_pascal_voc_kernel.py`
  - Pascal VOC conversion and XML save orchestration.
- `xml_to_polygon.py`
  - Parses annotation XML and converts geometry (`Polygon`, `Rect`, `RotatedRect`, `Circle`, `Ellipse`, `Curve`, `ClosedCurve`) into polygon points.
- `pascal_voc_visualization.ipynb`
  - Visualizes one Pascal VOC XML file with `bndbox` and `polygon` overlays.
- `bezier_control_point.py`, `bezier_interpolation.py`, `bezier_region.py`
  - Bezier-related utilities used by polygon generation.
- `test_*.ipynb`
  - Experiment and validation notebooks.

## Requirements

Python 3.10+ recommended.

Install dependencies:

```bash
pip install numpy matplotlib pillow
```

## Usage

### 1) Batch conversion (recommended)

Scan a directory recursively for image + annotation pairs:

- image: `*.png` / `*.jpg` / `*.jpeg`
- annotation: `<image_stem>_annotations.xml`

```bash
python convert_to_pascal_voc.py --input-dir . --output-dir .
```

Example output:

- `0001.jpg` + `0001_annotations.xml` -> `0001.xml`
- `0002.png` + `0002_annotations.xml` -> `0002.xml`

### 2) Single conversion mode

Use when width/height are already known:

```bash
python convert_to_pascal_voc.py \
  --input-xml 0001_annotations.xml \
  --output-xml 0001.xml \
  --filename 0001.jpg \
  --width 1920 \
  --height 1080
```

Optional args:

- `--depth` (default: `3`)
- `--folder`
- `--image-path`
- `--database`

### 3) Visualization notebook

Open and run:

- `pascal_voc_visualization.ipynb`

In the last cell, set:

```python
VOC_XML_PATH = Path("0001.xml")
```

Then execute to display the image with bounding boxes and polygons.

## Notes

- Pascal VOC output includes both:
  - `object/bndbox` (compatibility)
  - `object/polygon` (segmentation points)
- If an image has no matching `*_annotations.xml`, it is reported as missing in batch mode.

## Utilities License

[MIT](LICENSE)

