from __future__ import annotations

import argparse
import sys
from pathlib import Path

from radimagetovisio.exporters.svg_exporter import export_svg
from radimagetovisio.exporters.vsdx.package import export_vsdx
from radimagetovisio.utils.image_io import load_image
from radimagetovisio.vision.pipeline import run_pipeline


def _progress_cb(step: str, percent: int) -> None:
    print(f"  {step} ... {percent}%")


def convert(
    input_path: str,
    output_path: str,
    detect_shapes: bool = True,
    detect_text: bool = True,
    infer_connectors: bool = True,
) -> None:
    src = Path(input_path)
    dst = Path(output_path)
    if not src.exists():
        raise FileNotFoundError(f"Image not found: {src}")

    print(f"Loading {src} ...")
    image_result = load_image(src)
    print(f"  {image_result.width}x{image_result.height} {image_result.mode}")

    print("Running detection pipeline ...")
    diagram = run_pipeline(
        image_result,
        progress=_progress_cb,
        detect_shapes=detect_shapes,
        detect_text=detect_text,
        infer_connectors=infer_connectors,
    )
    page = diagram.pages[0] if diagram.pages else None
    if page is not None:
        print(
            f"Detected {len(page.shapes)} shapes, "
            f"{len(page.connectors)} connectors, "
            f"{len(page.texts)} texts"
        )

    print(f"Exporting to {dst} ...")
    suffix = dst.suffix.lower()
    if suffix == ".vsdx":
        export_vsdx(diagram, str(dst))
    elif suffix == ".svg":
        export_svg(diagram, str(dst))
    else:
        raise ValueError(f"Unsupported export format: {suffix}. Use .vsdx or .svg")

    print(f"Done. Output: {dst}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="radimagetovisio",
        description="Convert an image into a Visio-compatible diagram.",
    )
    parser.add_argument("input", help="Input image path (png, jpg, bmp, tiff)")
    parser.add_argument("output", help="Output path (.vsdx or .svg)")
    parser.add_argument(
        "--no-shapes",
        action="store_true",
        help="Skip shape detection",
    )
    parser.add_argument(
        "--no-text",
        action="store_true",
        help="Skip text/OCR detection",
    )
    parser.add_argument(
        "--no-connectors",
        action="store_true",
        help="Skip connector inference",
    )
    args = parser.parse_args(argv)

    try:
        convert(
            args.input,
            args.output,
            detect_shapes=not args.no_shapes,
            detect_text=not args.no_text,
            infer_connectors=not args.no_connectors,
        )
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
