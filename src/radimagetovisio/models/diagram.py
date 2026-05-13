from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

from radimagetovisio.models.geometry import Point, Rect


class ShapeType(Enum):
    RECTANGLE = auto()
    ELLIPSE = auto()
    DIAMOND = auto()
    PARALLELOGRAM = auto()
    TRIANGLE = auto()
    FREEHAND = auto()
    CONTAINER = auto()


class ConnectorType(Enum):
    STRAIGHT = auto()
    ELBOW = auto()
    CURVED = auto()


@dataclass
class Shape:
    bounds: Rect
    shape_type: ShapeType = ShapeType.RECTANGLE
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fill_color: str = "#ffffff"
    stroke_color: str = "#000000"
    stroke_width: float = 1.0
    z_order: int = 0
    opacity: float = 1.0
    label: str = ""

    @property
    def center(self) -> Point:
        return self.bounds.center


@dataclass
class Connector:
    from_shape_id: str
    to_shape_id: str
    connector_type: ConnectorType = ConnectorType.STRAIGHT
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_point: Point | None = None
    to_point: Point | None = None
    arrowhead_start: bool = False
    arrowhead_end: bool = True
    stroke_color: str = "#000000"
    stroke_width: float = 1.0
    label: str = ""


@dataclass
class TextBox:
    text: str
    bounds: Rect
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    font_family: str = "Arial"
    font_size_pt: float = 12.0
    color: str = "#000000"
    bold: bool = False
    italic: bool = False
    associated_shape_id: str | None = None


@dataclass
class Page:
    name: str = "Page-1"
    width_mm: float = 210.0
    height_mm: float = 297.0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    shapes: list[Shape] = field(default_factory=list)
    connectors: list[Connector] = field(default_factory=list)
    texts: list[TextBox] = field(default_factory=list)

    def add_shape(self, shape: Shape) -> None:
        self.shapes.append(shape)

    def add_connector(self, connector: Connector) -> None:
        self.connectors.append(connector)

    def add_text(self, text: TextBox) -> None:
        self.texts.append(text)

    def get_shape_by_id(self, shape_id: str) -> Shape | None:
        for shape in self.shapes:
            if shape.id == shape_id:
                return shape
        return None

    def get_text_by_id(self, text_id: str) -> TextBox | None:
        for text in self.texts:
            if text.id == text_id:
                return text
        return None


@dataclass
class Diagram:
    title: str = "Untitled Diagram"
    author: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pages: list[Page] = field(default_factory=list)

    def add_page(self, page: Page) -> None:
        self.pages.append(page)

    def get_page_by_id(self, page_id: str) -> Page | None:
        for page in self.pages:
            if page.id == page_id:
                return page
        return None

    @property
    def page_count(self) -> int:
        return len(self.pages)
