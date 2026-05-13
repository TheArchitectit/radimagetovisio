import pytest

from radimagetovisio.models.geometry import Point, Rect, mm_to_px, px_to_mm


class TestPoint:
    def test_add(self) -> None:
        a = Point(1, 2)
        b = Point(3, 4)
        assert a + b == Point(4, 6)

    def test_sub(self) -> None:
        a = Point(5, 5)
        b = Point(2, 1)
        assert a - b == Point(3, 4)

    def test_distance_to(self) -> None:
        a = Point(0, 0)
        b = Point(3, 4)
        assert a.distance_to(b) == pytest.approx(5.0)


class TestRect:
    def test_properties(self) -> None:
        r = Rect(10, 20, 30, 40)
        assert r.left == 10
        assert r.top == 20
        assert r.right == 40
        assert r.bottom == 60
        assert r.center == Point(25, 40)
        assert r.top_left == Point(10, 20)
        assert r.bottom_right == Point(40, 60)

    def test_contains(self) -> None:
        r = Rect(0, 0, 10, 10)
        assert r.contains(Point(5, 5))
        assert r.contains(Point(0, 0))
        assert not r.contains(Point(11, 5))

    def test_intersects(self) -> None:
        a = Rect(0, 0, 10, 10)
        b = Rect(5, 5, 10, 10)
        c = Rect(20, 20, 5, 5)
        assert a.intersects(b)
        assert not a.intersects(c)

    def test_intersection_area(self) -> None:
        a = Rect(0, 0, 10, 10)
        b = Rect(5, 5, 10, 10)
        assert a.intersection_area(b) == 25.0
        assert a.intersection_area(Rect(20, 20, 5, 5)) == 0.0

    def test_iou(self) -> None:
        a = Rect(0, 0, 10, 10)
        b = Rect(5, 5, 10, 10)
        expected = 25.0 / (100.0 + 100.0 - 25.0)
        assert a.iou(b) == pytest.approx(expected)

    def test_iou_no_overlap(self) -> None:
        a = Rect(0, 0, 10, 10)
        b = Rect(20, 20, 10, 10)
        assert a.iou(b) == 0.0

    def test_area(self) -> None:
        assert Rect(0, 0, 5, 7).area == 35.0

    def test_to_tuple(self) -> None:
        assert Rect(1, 2, 3, 4).to_tuple() == (1, 2, 3, 4)


class TestUnitConversion:
    def test_px_to_mm_default_dpi(self) -> None:
        assert px_to_mm(96) == pytest.approx(25.4)

    def test_mm_to_px_default_dpi(self) -> None:
        assert mm_to_px(25.4) == pytest.approx(96.0)

    def test_round_trip(self) -> None:
        original = 123.45
        assert mm_to_px(px_to_mm(original)) == pytest.approx(original)
