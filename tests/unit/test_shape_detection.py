import cv2
import numpy as np

from radimagetovisio.models.diagram import ShapeType
from radimagetovisio.vision.shape_detection import detect_circles, detect_contours, detect_lines


class TestDetectContours:
    def test_detects_rectangle(self) -> None:
        img = np.full((100, 100, 3), 255, dtype=np.uint8)
        cv2.rectangle(img, (20, 20), (80, 60), (0, 0, 0), thickness=-1)
        shapes = detect_contours(img, min_area=100)
        assert any(s.shape_type == ShapeType.RECTANGLE for s in shapes)

    def test_detects_triangle(self) -> None:
        img = np.full((100, 100, 3), 255, dtype=np.uint8)
        pts = np.array([[50, 20], [20, 80], [80, 80]], dtype=np.int32)
        cv2.fillPoly(img, [pts], (0, 0, 0))
        shapes = detect_contours(img, min_area=100)
        assert any(s.shape_type == ShapeType.TRIANGLE for s in shapes)

    def test_detects_diamond(self) -> None:
        img = np.full((100, 100, 3), 255, dtype=np.uint8)
        pts = np.array([[50, 20], [80, 50], [50, 80], [20, 50]], dtype=np.int32)
        cv2.fillPoly(img, [pts], (0, 0, 0))
        shapes = detect_contours(img, min_area=100)
        assert any(s.shape_type == ShapeType.DIAMOND for s in shapes)

    def test_detects_ellipse(self) -> None:
        img = np.full((100, 100, 3), 255, dtype=np.uint8)
        cv2.ellipse(img, (50, 50), (30, 20), 0, 0, 360, (0, 0, 0), thickness=-1)
        shapes = detect_contours(img, min_area=100)
        assert any(s.shape_type == ShapeType.ELLIPSE for s in shapes)

    def test_empty_image(self) -> None:
        img = np.full((50, 50, 3), 255, dtype=np.uint8)
        shapes = detect_contours(img, min_area=5000)
        assert shapes == []

    def test_grayscale_input(self) -> None:
        img = np.full((100, 100), 255, dtype=np.uint8)
        cv2.rectangle(img, (20, 20), (80, 60), 0, thickness=-1)
        shapes = detect_contours(img, min_area=100)
        assert any(s.shape_type == ShapeType.RECTANGLE for s in shapes)

    def test_progress_callback(self) -> None:
        calls = []

        def cb(step: str, percent: int) -> None:
            calls.append((step, percent))

        img = np.full((100, 100, 3), 255, dtype=np.uint8)
        cv2.rectangle(img, (20, 20), (80, 60), (0, 0, 0), thickness=-1)
        detect_contours(img, min_area=100, progress=cb)
        assert len(calls) >= 2
        assert calls[0][1] <= calls[-1][1]

    def test_bounds_in_mm(self) -> None:
        img = np.full((100, 100, 3), 255, dtype=np.uint8)
        cv2.rectangle(img, (20, 20), (80, 60), (0, 0, 0), thickness=-1)
        shapes = detect_contours(img, min_area=100)
        rect_shapes = [s for s in shapes if s.shape_type == ShapeType.RECTANGLE]
        assert rect_shapes
        s = rect_shapes[0]
        assert s.bounds.width > 0
        assert s.bounds.height > 0
        assert s.bounds.x >= 0
        assert s.bounds.y >= 0


class TestDetectLines:
    def test_detects_straight_line(self) -> None:
        img = np.full((100, 100, 3), 255, dtype=np.uint8)
        cv2.line(img, (10, 50), (90, 50), (0, 0, 0), thickness=2)
        lines = detect_lines(img, min_line_length=20)
        assert len(lines) >= 1

    def test_no_lines_in_blank(self) -> None:
        img = np.full((50, 50, 3), 255, dtype=np.uint8)
        lines = detect_lines(img)
        assert lines == []


class TestDetectCircles:
    def test_detects_circle(self) -> None:
        img = np.full((100, 100, 3), 255, dtype=np.uint8)
        cv2.circle(img, (50, 50), 25, (0, 0, 0), thickness=2)
        circles = detect_circles(img, min_radius=10, max_radius=40)
        assert len(circles) >= 1
        x, y, r = circles[0]
        assert 20 <= r <= 35

    def test_no_circles_in_blank(self) -> None:
        img = np.full((50, 50, 3), 255, dtype=np.uint8)
        circles = detect_circles(img)
        assert circles == []
