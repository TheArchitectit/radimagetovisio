from __future__ import annotations

from collections.abc import Callable

import cv2
import numpy as np

from radimagetovisio.models.diagram import Connector, ConnectorType, Shape, ShapeType, TextBox
from radimagetovisio.models.geometry import Point, Rect

ProgressCallback = Callable[[str, int], None]


def _default_progress(step: str, percent: int) -> None:
    pass


def _snap_point_to_rect_boundary(point: Point, rect: Rect) -> Point:
    if rect.contains(point):
        dx_left = point.x - rect.left
        dx_right = rect.right - point.x
        dy_top = point.y - rect.top
        dy_bottom = rect.bottom - point.y
        min_dist = min(dx_left, dx_right, dy_top, dy_bottom)
        if min_dist == dx_left:
            return Point(rect.left, point.y)
        if min_dist == dx_right:
            return Point(rect.right, point.y)
        if min_dist == dy_top:
            return Point(point.x, rect.top)
        return Point(point.x, rect.bottom)

    x = max(rect.left, min(point.x, rect.right))
    y = max(rect.top, min(point.y, rect.bottom))
    return Point(x, y)


def deduplicate_shapes(
    shapes: list[Shape],
    iou_threshold: float = 0.5,
    progress: ProgressCallback = _default_progress,
) -> list[Shape]:
    progress("Deduplicating shapes", 0)
    if not shapes:
        progress("Done", 100)
        return []

    sorted_shapes = sorted(shapes, key=lambda s: s.bounds.area, reverse=True)
    kept: list[Shape] = []

    for s in sorted_shapes:
        duplicate = False
        for k in kept:
            iou = s.bounds.iou(k.bounds)
            if iou >= iou_threshold:
                duplicate = True
                break
        if not duplicate:
            kept.append(s)

    progress("Done", 100)
    return kept


def classify_flowchart_shapes(
    shapes: list[Shape],
    progress: ProgressCallback = _default_progress,
) -> list[Shape]:
    progress("Classifying flowchart shapes", 0)
    result = []
    for idx, s in enumerate(shapes):
        new_type = s.shape_type
        if s.shape_type == ShapeType.FREEHAND:
            aspect = s.bounds.width / s.bounds.height if s.bounds.height > 0 else 1.0
            if 0.5 <= aspect <= 2.0:
                new_type = ShapeType.RECTANGLE
            elif aspect > 2.0:
                new_type = ShapeType.PARALLELOGRAM
            elif aspect < 0.5:
                new_type = ShapeType.ELLIPSE

        if new_type == ShapeType.ELLIPSE and s.bounds.width > s.bounds.height * 1.5:
            new_type = ShapeType.RECTANGLE

        result.append(
            Shape(
                bounds=s.bounds,
                shape_type=new_type,
                id=s.id,
                fill_color=s.fill_color,
                stroke_color=s.stroke_color,
                stroke_width=s.stroke_width,
                z_order=s.z_order,
                opacity=s.opacity,
                label=s.label,
            )
        )
        progress(
            f"Classifying shape {idx + 1}/{len(shapes)}",
            int(100 * (idx + 1) / len(shapes)),
        )

    progress("Done", 100)
    return result


def snap_endpoints_to_shapes(
    lines: list[tuple[tuple[float, float], tuple[float, float]]],
    shapes: list[Shape],
    snap_distance_px: float = 20.0,
    progress: ProgressCallback = _default_progress,
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    progress("Snapping endpoints", 0)
    result = []
    for idx, (p1, p2) in enumerate(lines):
        pt1 = Point(p1[0], p1[1])
        pt2 = Point(p2[0], p2[1])

        nearest1: tuple[Shape, float] | None = None
        nearest2: tuple[Shape, float] | None = None

        for s in shapes:
            snap1 = _snap_point_to_rect_boundary(pt1, s.bounds)
            snap2 = _snap_point_to_rect_boundary(pt2, s.bounds)
            d1 = pt1.distance_to(snap1)
            d2 = pt2.distance_to(snap2)
            inside1 = s.bounds.contains(pt1)
            inside2 = s.bounds.contains(pt2)
            if (inside1 or d1 <= snap_distance_px) and (nearest1 is None or d1 < nearest1[1]):
                nearest1 = (s, d1)
            if (inside2 or d2 <= snap_distance_px) and (nearest2 is None or d2 < nearest2[1]):
                nearest2 = (s, d2)

        if nearest1 is not None:
            snapped = _snap_point_to_rect_boundary(pt1, nearest1[0].bounds)
            pt1 = snapped
        if nearest2 is not None:
            snapped = _snap_point_to_rect_boundary(pt2, nearest2[0].bounds)
            pt2 = snapped

        result.append(((pt1.x, pt1.y), (pt2.x, pt2.y)))
        progress(
            f"Snapping line {idx + 1}/{len(lines)}",
            int(100 * (idx + 1) / max(len(lines), 1)),
        )

    progress("Done", 100)
    return result


def infer_connectors(
    lines: list[tuple[tuple[float, float], tuple[float, float]]],
    shapes: list[Shape],
    snap_distance_px: float = 20.0,
    progress: ProgressCallback = _default_progress,
) -> list[Connector]:
    progress("Inferring connectors", 0)
    connectors = []
    for idx, (p1, p2) in enumerate(lines):
        pt1 = Point(p1[0], p1[1])
        pt2 = Point(p2[0], p2[1])

        from_shape: Shape | None = None
        to_shape: Shape | None = None
        best_d1 = float("inf")
        best_d2 = float("inf")

        for s in shapes:
            snap1 = _snap_point_to_rect_boundary(pt1, s.bounds)
            snap2 = _snap_point_to_rect_boundary(pt2, s.bounds)
            d1 = pt1.distance_to(snap1)
            d2 = pt2.distance_to(snap2)
            if d1 <= snap_distance_px and d1 < best_d1:
                best_d1 = d1
                from_shape = s
            if d2 <= snap_distance_px and d2 < best_d2:
                best_d2 = d2
                to_shape = s

        if from_shape is not None and to_shape is not None and from_shape.id != to_shape.id:
            connectors.append(
                Connector(
                    from_shape_id=from_shape.id,
                    to_shape_id=to_shape.id,
                    connector_type=ConnectorType.STRAIGHT,
                    from_point=pt1,
                    to_point=pt2,
                )
            )

        progress(
            f"Inferring connector {idx + 1}/{len(lines)}",
            int(100 * (idx + 1) / max(len(lines), 1)),
        )

    progress("Done", 100)
    return connectors


def detect_arrowheads(
    image: np.ndarray,
    lines: list[tuple[tuple[float, float], tuple[float, float]]],
    shapes: list[Shape],
    arrowhead_size_px: float = 15.0,
    progress: ProgressCallback = _default_progress,
) -> tuple[list[bool], list[bool]]:
    progress("Detecting arrowheads", 0)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image.copy()

    start_flags: list[bool] = []
    end_flags: list[bool] = []

    for idx, (p1, p2) in enumerate(lines):
        pt1 = Point(p1[0], p1[1])
        pt2 = Point(p2[0], p2[1])

        has_start = False
        has_end = False

        size = int(arrowhead_size_px)
        if size < 3:
            size = 3

        for endpoint, flag_ref in [(pt1, "start"), (pt2, "end")]:
            x1 = max(0, int(endpoint.x - size))
            y1 = max(0, int(endpoint.y - size))
            x2 = min(gray.shape[1], int(endpoint.x + size))
            y2 = min(gray.shape[0], int(endpoint.y + size))

            if x2 <= x1 or y2 <= y1:
                continue

            roi = gray[y1:y2, x1:x2]
            if roi.size == 0:
                continue

            _, binary = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                perimeter = cv2.arcLength(cnt, True)
                if area < 30 or area > size * size or perimeter < 15:
                    continue
                hull = cv2.convexHull(cnt)
                hull_area = cv2.contourArea(hull)
                solidity = area / hull_area if hull_area > 0 else 0.0
                if solidity < 0.7:
                    continue
                approx = cv2.approxPolyDP(cnt, 0.1 * perimeter, True)
                if len(approx) == 3:
                    if flag_ref == "start":
                        has_start = True
                    else:
                        has_end = True
                    break

            for s in shapes:
                if s.bounds.contains(endpoint):
                    if flag_ref == "start":
                        has_start = False
                    else:
                        has_end = False
                    break

        start_flags.append(has_start)
        end_flags.append(has_end)
        progress(
            f"Arrowhead {idx + 1}/{len(lines)}",
            int(100 * (idx + 1) / max(len(lines), 1)),
        )

    progress("Done", 100)
    return start_flags, end_flags


def compute_page_bounds(
    shapes: list[Shape],
    texts: list[TextBox],
    margin_mm: float = 10.0,
    min_width_mm: float = 210.0,
    min_height_mm: float = 297.0,
    progress: ProgressCallback = _default_progress,
) -> Rect:
    progress("Computing page bounds", 0)
    all_rects = [s.bounds for s in shapes] + [t.bounds for t in texts]
    if not all_rects:
        progress("Done", 100)
        return Rect(0, 0, min_width_mm, min_height_mm)

    left = min(r.left for r in all_rects)
    top = min(r.top for r in all_rects)
    right = max(r.right for r in all_rects)
    bottom = max(r.bottom for r in all_rects)

    width = max(right - left + 2 * margin_mm, min_width_mm)
    height = max(bottom - top + 2 * margin_mm, min_height_mm)

    result = Rect(
        left - margin_mm,
        top - margin_mm,
        width,
        height,
    )
    progress("Done", 100)
    return result


def assign_z_order(
    shapes: list[Shape],
    progress: ProgressCallback = _default_progress,
) -> list[Shape]:
    progress("Assigning Z-order", 0)
    if not shapes:
        progress("Done", 100)
        return []

    sorted_by_area = sorted(enumerate(shapes), key=lambda x: x[1].bounds.area, reverse=True)
    result = []
    for z, (_original_idx, s) in enumerate(sorted_by_area):
        result.append(
            Shape(
                bounds=s.bounds,
                shape_type=s.shape_type,
                id=s.id,
                fill_color=s.fill_color,
                stroke_color=s.stroke_color,
                stroke_width=s.stroke_width,
                z_order=z,
                opacity=s.opacity,
                label=s.label,
            )
        )
        progress(
            f"Z-order {z + 1}/{len(shapes)}",
            int(100 * (z + 1) / len(shapes)),
        )

    result.sort(key=lambda s: s.z_order)
    progress("Done", 100)
    return result
