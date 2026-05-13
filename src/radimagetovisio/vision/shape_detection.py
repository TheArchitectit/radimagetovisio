from __future__ import annotations

from collections.abc import Callable

import cv2
import numpy as np

from radimagetovisio.models.diagram import Shape, ShapeType
from radimagetovisio.models.geometry import Rect, px_to_mm

ProgressCallback = Callable[[str, int], None]


def _default_progress(step: str, percent: int) -> None:
    pass


def _classify_contour(approx: np.ndarray, aspect_ratio: float) -> ShapeType:
    vertices = len(approx)
    if vertices == 3:
        return ShapeType.TRIANGLE
    if vertices == 4:
        if 0.8 <= aspect_ratio <= 1.25:
            return ShapeType.DIAMOND
        return ShapeType.RECTANGLE
    if vertices == 5:
        return ShapeType.PARALLELOGRAM
    if vertices >= 6:
        area = cv2.contourArea(approx)
        if area > 0:
            perimeter = cv2.arcLength(approx, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity > 0.75:
                return ShapeType.ELLIPSE
        return ShapeType.FREEHAND
    return ShapeType.FREEHAND


def detect_contours(
    image: np.ndarray,
    min_area: int = 50,
    max_area: int | None = None,
    epsilon_factor: float = 0.02,
    progress: ProgressCallback = _default_progress,
) -> list[Shape]:
    progress("Finding contours", 10)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image.copy()

    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    progress("Classifying contours", 40)

    shapes: list[Shape] = []
    if not contours:
        progress("Done", 100)
        return shapes

    for idx, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        if max_area is not None and area > max_area:
            continue

        epsilon = epsilon_factor * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = float(w) / h if h > 0 else 1.0
        shape_type = _classify_contour(approx, aspect_ratio)

        bounds_px = Rect(x, y, w, h)
        bounds_mm = Rect(
            px_to_mm(bounds_px.x),
            px_to_mm(bounds_px.y),
            px_to_mm(bounds_px.width),
            px_to_mm(bounds_px.height),
        )

        shape = Shape(
            bounds=bounds_mm,
            shape_type=shape_type,
            fill_color="#ffffff",
            stroke_color="#000000",
            stroke_width=1.0,
            z_order=0,
        )
        shapes.append(shape)

        progress(
            f"Classifying contour {idx + 1}/{len(contours)}",
            40 + int(50 * (idx + 1) / len(contours)),
        )

    progress("Done", 100)
    return shapes


def detect_lines(
    image: np.ndarray,
    rho: float = 1.0,
    theta: float = np.pi / 180,
    threshold: int = 50,
    min_line_length: float = 30.0,
    max_line_gap: float = 10.0,
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image.copy()

    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(
        edges,
        rho,
        theta,
        threshold,
        minLineLength=min_line_length,
        maxLineGap=max_line_gap,
    )

    result: list[tuple[tuple[float, float], tuple[float, float]]] = []
    if lines is None:
        return result

    for line in lines:
        x1, y1, x2, y2 = line[0]
        result.append(((float(x1), float(y1)), (float(x2), float(y2))))

    return result


def detect_circles(
    image: np.ndarray,
    dp: float = 1.2,
    min_dist: float = 50.0,
    param1: int = 100,
    param2: int = 30,
    min_radius: int = 10,
    max_radius: int = 200,
) -> list[tuple[float, float, float]]:
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image.copy()

    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp,
        min_dist,
        param1=param1,
        param2=param2,
        minRadius=min_radius,
        maxRadius=max_radius,
    )

    result: list[tuple[float, float, float]] = []
    if circles is None:
        return result

    for circle in circles[0]:
        x, y, r = circle
        result.append((float(x), float(y), float(r)))

    return result
