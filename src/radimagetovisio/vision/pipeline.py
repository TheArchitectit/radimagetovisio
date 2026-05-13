from __future__ import annotations

from collections.abc import Callable

from radimagetovisio.models.diagram import Diagram, Page, Shape, TextBox
from radimagetovisio.utils.image_io import ImageLoadResult
from radimagetovisio.vision import (
    diagram_inference,
    ocr_postprocess,
    preprocess,
    shape_detection,
    text_detection,
)

ProgressCallback = Callable[[str, int], None]


def _default_progress(step: str, percent: int) -> None:
    pass


def run_pipeline(
    image_result: ImageLoadResult,
    progress: ProgressCallback = _default_progress,
    detect_shapes: bool = True,
    detect_text: bool = True,
    deduplicate: bool = True,
    infer_connectors: bool = True,
    iou_threshold: float = 0.5,
    snap_distance_px: float = 20.0,
    page_margin_mm: float = 10.0,
) -> Diagram:
    progress("Pipeline started", 0)
    image = image_result.array

    # 1. Preprocess
    progress("Preprocessing", 5)
    denoised = preprocess.denoise(image, strength=10)
    deskewed = preprocess.deskew(denoised, max_angle=5.0)

    # 2. Shape detection
    shapes: list[Shape] = []
    if detect_shapes:
        progress("Detecting shapes", 20)
        h, w = deskewed.shape[:2]
        image_area = h * w
        min_area = max(50, image_area // 8000)
        max_area = int(image_area * 0.85)
        shapes = shape_detection.detect_contours(
            deskewed,
            min_area=min_area,
            max_area=max_area,
            progress=lambda step, pct: progress(step, int(20 + pct * 0.25)),
        )

    # 3. Text detection
    texts: list[TextBox] = []
    if detect_text:
        progress("Detecting text", 50)
        texts = text_detection.detect_text(
            deskewed,
            merge_into_lines=True,
            progress=lambda step, pct: progress(step, int(50 + pct * 0.15)),
        )
        progress("Post-processing OCR", 70)
        texts = ocr_postprocess.estimate_font_sizes(texts)
        texts = ocr_postprocess.filter_noise(texts)
        texts, shapes = ocr_postprocess.associate_text_with_shapes(texts, shapes)

    # 4. Diagram inference
    progress("Inferring diagram", 75)
    if deduplicate:
        shapes = diagram_inference.deduplicate_shapes(shapes, iou_threshold=iou_threshold)
    shapes = diagram_inference.classify_flowchart_shapes(shapes)

    lines = shape_detection.detect_lines(deskewed) if infer_connectors else []
    connectors = []
    if infer_connectors and lines:
        connectors = diagram_inference.infer_connectors(
            lines, shapes, snap_distance_px=snap_distance_px
        )
        if image is not None and lines:
            start_arrows, end_arrows = diagram_inference.detect_arrowheads(image, lines, shapes)
            for i, conn in enumerate(connectors):
                if i < len(start_arrows):
                    conn.arrowhead_start = start_arrows[i]
                if i < len(end_arrows):
                    conn.arrowhead_end = end_arrows[i]

    shapes = diagram_inference.assign_z_order(shapes)
    page_bounds = diagram_inference.compute_page_bounds(shapes, texts, margin_mm=page_margin_mm)

    # 5. Build output
    progress("Building diagram", 95)
    page = Page(
        name="Page-1",
        width_mm=page_bounds.width,
        height_mm=page_bounds.height,
    )
    for s in shapes:
        page.add_shape(s)
    for c in connectors:
        page.add_connector(c)
    for t in texts:
        page.add_text(t)

    diagram = Diagram(title="Converted Diagram")
    diagram.add_page(page)

    progress("Done", 100)
    return diagram
