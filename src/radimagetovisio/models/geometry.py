from __future__ import annotations

from dataclasses import dataclass

DEFAULT_DPI = 96


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def __add__(self, other: Point) -> Point:
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Point) -> Point:
        return Point(self.x - other.x, self.y - other.y)

    def distance_to(self, other: Point) -> float:
        dx = self.x - other.x
        dy = self.y - other.y
        return (dx * dx + dy * dy) ** 0.5


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    width: float
    height: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def top(self) -> float:
        return self.y

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def center(self) -> Point:
        return Point(self.x + self.width / 2, self.y + self.height / 2)

    @property
    def top_left(self) -> Point:
        return Point(self.x, self.y)

    @property
    def bottom_right(self) -> Point:
        return Point(self.right, self.bottom)

    def contains(self, point: Point) -> bool:
        return self.left <= point.x <= self.right and self.top <= point.y <= self.bottom

    def intersects(self, other: Rect) -> bool:
        return not (
            self.right <= other.left
            or self.left >= other.right
            or self.bottom <= other.top
            or self.top >= other.bottom
        )

    def intersection_area(self, other: Rect) -> float:
        if not self.intersects(other):
            return 0.0
        x_left = max(self.left, other.left)
        y_top = max(self.top, other.top)
        x_right = min(self.right, other.right)
        y_bottom = min(self.bottom, other.bottom)
        return (x_right - x_left) * (y_bottom - y_top)

    def iou(self, other: Rect) -> float:
        intersection = self.intersection_area(other)
        if intersection == 0.0:
            return 0.0
        union = self.area + other.area - intersection
        return intersection / union

    @property
    def area(self) -> float:
        return self.width * self.height

    def to_tuple(self) -> tuple[float, float, float, float]:
        return (self.x, self.y, self.width, self.height)


def px_to_mm(px: float, dpi: int = DEFAULT_DPI) -> float:
    return px * 25.4 / dpi


def mm_to_px(mm: float, dpi: int = DEFAULT_DPI) -> float:
    return mm * dpi / 25.4
