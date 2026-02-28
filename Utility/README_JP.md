# Utility

アノテーション XML を Pascal VOC XML に変換し、可視化するためのユーティリティ群です。

## 言語

[English](README.md)
[日本語](README_JP.md)

## 概要

このフォルダには、以下を行うためのスクリプトとノートブックが含まれます。

- アノテーション XML（`*_annotations.xml`）を Pascal VOC XML に変換
- 各種ジオメトリアノテーションをポリゴン配列へ変換
- Pascal VOC XML を画像上に重ねて可視化

## ファイル構成

- `convert_to_pascal_voc.py`
  - CLIエントリーポイント兼、互換インポート窓口です。
- `get_image_size.py`
  - `.png` / `.jpg` / `.jpeg` の画像サイズ読み取り処理です。
- `polygon_to_bbox_util.py`
  - `polygon_to_bbox` と VOC向けポリゴン座標正規化処理です。
- `load_annotation.py`
  - XML/画像の読み込みと、画像-アノテーションペア検出処理です。
- `convert_to_pascal_voc_kernel.py`
  - Pascal VOC 変換と XML 保存のオーケストレーション処理です。
- `xml_to_polygon.py`
  - アノテーション XML を解析し、`Polygon`, `Rect`, `RotatedRect`, `Circle`, `Ellipse`, `Curve`, `ClosedCurve` をポリゴン点列に変換します。
- `pascal_voc_visualization.ipynb`
  - 1件の Pascal VOC XML を `bndbox` と `polygon` オーバーレイ付きで可視化します。
- `bezier_control_point.py`, `bezier_interpolation.py`, `bezier_region.py`
  - ポリゴン生成で利用する Bezier 関連ユーティリティです。
- `test_*.ipynb`
  - 実験・検証用ノートブックです。

## 動作環境

Python 3.10 以上を推奨します。

依存ライブラリのインストール:

```bash
pip install numpy matplotlib pillow
```

## 使い方

### 1) バッチ変換（推奨）

ディレクトリを再帰的に走査し、次のペアを検出して変換します。

- 画像: `*.png` / `*.jpg` / `*.jpeg`
- アノテーション: `<image_stem>_annotations.xml`

```bash
python convert_to_pascal_voc.py --input-dir . --output-dir .
```

出力例:

- `0001.jpg` + `0001_annotations.xml` -> `0001.xml`
- `0002.png` + `0002_annotations.xml` -> `0002.xml`

### 2) 単体変換モード

画像サイズ（width/height）が既知の場合に使用します。

```bash
python convert_to_pascal_voc.py \
  --input-xml 0001_annotations.xml \
  --output-xml 0001.xml \
  --filename 0001.jpg \
  --width 1920 \
  --height 1080
```

任意引数:

- `--depth`（デフォルト: `3`）
- `--folder`
- `--image-path`
- `--database`

### 3) 可視化ノートブック

以下を開いて実行します。

- `pascal_voc_visualization.ipynb`

最後のセルで次を指定:

```python
VOC_XML_PATH = Path("0001.xml")
```

実行すると、画像上にバウンディングボックスとポリゴンが表示されます。

## 補足

- Pascal VOC 出力には次の両方を含みます。
  - `object/bndbox`（互換性のため）
  - `object/polygon`（セグメンテーション点列）
- バッチモードで対応する `*_annotations.xml` が見つからない画像は、missing として報告されます。

## ユーティリティ群のライセンス

[MIT](LICENSE)

