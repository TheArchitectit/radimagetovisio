import numpy as np
import pytest

from radimagetovisio.models.diagram import ConnectorType, Shape, ShapeType, TextBox
from radimagetovisio.models.geometry import Rect
from radimagetovisio.vision.diagram_inference import (
    assign_z_order,
    classify_flowchart_shapes,
    compute_page_bounds,
    deduplicate_shapes,
    detect_arrowheads,
    infer_connectors,
    snap_endpoints_to_shapes,
)


class TestDeduplicateShapes:
    def test_keeps_non_overlapping(self) -> None:
        s1 = Shape(bounds=Rect(0, 0, 10, 10))
        s2 = Shape(bounds=Rect(20, 20, 10, 10))
        result = deduplicate_shapes([s1, s2])
        assert len(result) == 2

    def test_removes_high_iou_duplicate(self) -> None:
        s1 = Shape(bounds=Rect(0, 0, 10, 10))
        s2 = Shape(bounds=Rect(1, 1, 9, 9))
        result = deduplicate_shapes([s1, s2], iou_threshold=0.5)
        assert len(result) == 1
        assert result[0].bounds.area == pytest.approx(100.0, abs=1.0)

    def test_keeps_low_iou(self) -> None:
        s1 = Shape(bounds=Rect(0, 0, 10, 10))
        s2 = Shape(bounds=Rect(8, 8, 10, 10))
        result = deduplicate_shapes([s1, s2], iou_threshold=0.9)
        assert len(result) == 2

    def test_empty_list(self) -> None:
        assert deduplicate_shapes([]) == []

    def test_progress_callback(self) -> None:
        calls = []

        def cb(step: str, pct: int) -> None:
            calls.append((step, pct))

        deduplicate_shapes([Shape(bounds=Rect(0, 0, 10, 10))], progress=cb)
        assert len(calls) >= 2


class TestClassifyFlowchartShapes:
    def test_ellipse_stays_ellipse(self) -> None:
        s = Shape(bounds=Rect(0, 0, 20, 20), shape_type=ShapeType.ELLIPSE)
        result = classify_flowchart_shapes([s])
        assert result[0].shape_type == ShapeType.ELLIPSE

    def test_freehand_becomes_rectangle(self) -> None:
        s = Shape(bounds=Rect(0, 0, 20, 20), shape_type=ShapeType.FREEHAND)
        result = classify_flowchart_shapes([s])
        assert result[0].shape_type == ShapeType.RECTANGLE

    def test_freehand_becomes_parallelogram_when_wide(self) -> None:
        s = Shape(bounds=Rect(0, 0, 60, 10), shape_type=ShapeType.FREEHAND)
        result = classify_flowchart_shapes([s])
        assert result[0].shape_type == ShapeType.PARALLELOGRAM

    def test_ellipse_becomes_rectangle_when_very_wide(self) -> None:
        s = Shape(bounds=Rect(0, 0, 60, 20), shape_type=ShapeType.ELLIPSE)
        result = classify_flowchart_shapes([s])
        assert result[0].shape_type == ShapeType.RECTANGLE

    def test_preserves_label_and_id(self) -> None:
        s = Shape(bounds=Rect(0, 0, 20, 20), shape_type=ShapeType.FREEHAND, label="test")
        result = classify_flowchart_shapes([s])
        assert result[0].label == "test"
        assert result[0].id == s.id

    def test_empty_list(self) -> None:
        assert classify_flowchart_shapes([]) == []


class TestSnapEndpointsToShapes:
    def test_snaps_inside_to_boundary(self) -> None:
        shape = Shape(bounds=Rect(0, 0, 100, 100))
        lines = [((50, 50), (150, 50))]
        result = snap_endpoints_to_shapes(lines, [shape], snap_distance_px=20.0)
        # First point was inside shape, should snap to nearest boundary (left at x=0)
        assert result[0][0][0] == pytest.approx(0.0, abs=1.0)

    def test_snaps_nearby_outside(self) -> None:
        shape = Shape(bounds=Rect(0, 0, 100, 100))
        lines = [((-5, 50), (150, 50))]
        result = snap_endpoints_to_shapes(lines, [shape], snap_distance_px=20.0)
        assert result[0][0][0] == pytest.approx(0.0, abs=1.0)

    def test_does_not_snap_far_away(self) -> None:
        shape = Shape(bounds=Rect(0, 0, 100, 100))
        lines = [((200, 200), (300, 300))]
        result = snap_endpoints_to_shapes(lines, [shape], snap_distance_px=20.0)
        assert result[0][0] == (200.0, 200.0)

    def test_empty_inputs(self) -> None:
        assert snap_endpoints_to_shapes([], []) == []

    def test_progress_callback(self) -> None:
        calls = []

        def cb(step: str, pct: int) -> None:
            calls.append((step, pct))

        shape = Shape(bounds=Rect(0, 0, 10, 10))
        snap_endpoints_to_shapes([((0, 5), (10, 5))], [shape], progress=cb)
        assert len(calls) >= 2


class TestInferConnectors:
    def test_creates_connector_between_shapes(self) -> None:
        s1 = Shape(bounds=Rect(0, 0, 50, 50))
        s2 = Shape(bounds=Rect(100, 0, 50, 50))
        lines = [((50, 25), (100, 25))]
        connectors = infer_connectors(lines, [s1, s2], snap_distance_px=20.0)
        assert len(connectors) == 1
        assert connectors[0].from_shape_id == s1.id
        assert connectors[0].to_shape_id == s2.id
        assert connectors[0].connector_type == ConnectorType.STRAIGHT

    def test_no_connector_for_same_shape(self) -> None:
        s1 = Shape(bounds=Rect(0, 0, 100, 100))
        lines = [((10, 10), (20, 20))]
        connectors = infer_connectors(lines, [s1], snap_distance_px=20.0)
        assert len(connectors) == 0

    def test_no_connector_when_far(self) -> None:
        s1 = Shape(bounds=Rect(0, 0, 10, 10))
        s2 = Shape(bounds=Rect(100, 100, 10, 10))
        lines = [((0, 0), (200, 200))]
        connectors = infer_connectors(lines, [s1, s2], snap_distance_px=5.0)
        assert len(connectors) == 0

    def test_empty_inputs(self) -> None:
        assert infer_connectors([], []) == []

    def test_progress_callback(self) -> None:
        calls = []

        def cb(step: str, pct: int) -> None:
            calls.append((step, pct))

        s1 = Shape(bounds=Rect(0, 0, 50, 50))
        s2 = Shape(bounds=Rect(100, 0, 50, 50))
        infer_connectors([((50, 25), (100, 25))], [s1, s2], progress=cb)
        assert len(calls) >= 2


class TestDetectArrowheads:
    def _make_triangle_roi(self) -> np.ndarray:
        img = np.full((50, 50, 3), 255, dtype=np.uint8)
        pts = np.array([[25, 10], [15, 40], [35, 40]], dtype=np.int32)
        cv2 = pytest.importorskip("cv2")
        cv2.fillPoly(img, [pts], (0, 0, 0))
        return img

    def test_no_arrowheads_in_blank(self) -> None:
        cv2 = pytest.importorskip("cv2")
        img = np.full((100, 100, 3), 255, dtype=np.uint8)
        cv2.line(img, (10, 50), (90, 50), (0, 0, 0), thickness=2)
        lines = [((10, 50), (90, 50))]
        start, end = detect_arrowheads(img, lines, [])
        assert all(not x for x in start)
        assert all(not x for x in end)

    def test_detects_triangle_near_endpoint(self) -> None:
        cv2 = pytest.importorskip("cv2")
        img = np.full((100, 100, 3), 255, dtype=np.uint8)
        cv2.line(img, (10, 50), (62, 50), (0, 0, 0), thickness=2)
        pts = np.array([[65, 50], [80, 40], [80, 60]], dtype=np.int32)
        cv2.fillPoly(img, [pts], (0, 0, 0))
        lines = [((10, 50), (62, 50))]
        start, end = detect_arrowheads(img, lines, [], arrowhead_size_px=20.0)
        assert end[0] is True
        assert start[0] is False

    def test_empty_lines(self) -> None:
        img = np.full((50, 50, 3), 255, dtype=np.uint8)
        start, end = detect_arrowheads(img, [], [])
        assert start == []
        assert end == []

    def test_shape_at_endpoint_suppresses(self) -> None:
        cv2 = pytest.importorskip("cv2")
        img = np.full((100, 100, 3), 255, dtype=np.uint8)
        s = Shape(bounds=Rect(65, 35, 30, 30))
        cv2.line(img, (10, 50), (70, 50), (0, 0, 0), thickness=2)
        pts = np.array([[70, 50], [80, 40], [80, 60]], dtype=np.int32)
        cv2.fillPoly(img, [pts], (0, 0, 0))
        lines = [((10, 50), (70, 50))]
        start, end = detect_arrowheads(img, lines, [s], arrowhead_size_px=20.0)
        assert end[0] is False


class TestComputePageBounds:
    def test_computes_from_shapes(self) -> None:
        shapes = [Shape(bounds=Rect(10, 10, 50, 50))]
        bounds = compute_page_bounds(shapes, [], margin_mm=5.0)
        assert bounds.left <= 10
        assert bounds.top <= 10
        assert bounds.width >= 60
        assert bounds.height >= 60

    def test_includes_texts(self) -> None:
        texts = [TextBox(text="x", bounds=Rect(100, 100, 20, 10))]
        bounds = compute_page_bounds([], texts, margin_mm=0.0)
        assert bounds.right >= 120
        assert bounds.bottom >= 110

    def test_minimum_size(self) -> None:
        bounds = compute_page_bounds([], [], min_width_mm=210.0, min_height_mm=297.0)
        assert bounds.width >= 210.0
        assert bounds.height >= 297.0

    def test_empty_with_defaults(self) -> None:
        bounds = compute_page_bounds([], [])
        assert bounds.width >= 210.0
        assert bounds.height >= 297.0


class TestAssignZOrder:
    def test_assigns_increasing_order(self) -> None:
        s1 = Shape(bounds=Rect(0, 0, 10, 10))
        s2 = Shape(bounds=Rect(0, 0, 20, 20))
        s3 = Shape(bounds=Rect(0, 0, 5, 5))
        result = assign_z_order([s1, s2, s3])
        z_values = [s.z_order for s in result]
        assert z_values == sorted(z_values)
        assert len(set(z_values)) == 3

    def test_smallest_is_topmost(self) -> None:
        small = Shape(bounds=Rect(0, 0, 5, 5))
        large = Shape(bounds=Rect(0, 0, 20, 20))
        result = assign_z_order([small, large])
        small_result = [s for s in result if s.bounds.area == pytest.approx(25.0)][0]
        large_result = [s for s in result if s.bounds.area == pytest.approx(400.0)][0]
        assert small_result.z_order > large_result.z_order

    def test_empty_list(self) -> None:
        assert assign_z_order([]) == []

    def test_preserves_shape_data(self) -> None:
        s = Shape(bounds=Rect(0, 0, 10, 10), label="test")
        result = assign_z_order([s])
        assert result[0].label == "test"
        assert result[0].id == s.id
