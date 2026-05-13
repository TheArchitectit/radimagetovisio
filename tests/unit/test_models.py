
from radimagetovisio.models.diagram import (
    Connector,
    ConnectorType,
    Diagram,
    Page,
    Shape,
    ShapeType,
    TextBox,
)
from radimagetovisio.models.geometry import Point, Rect


class TestShape:
    def test_default_values(self) -> None:
        s = Shape(bounds=Rect(0, 0, 10, 10))
        assert s.shape_type == ShapeType.RECTANGLE
        assert s.fill_color == "#ffffff"
        assert s.stroke_color == "#000000"
        assert s.stroke_width == 1.0
        assert s.z_order == 0
        assert s.opacity == 1.0
        assert s.label == ""

    def test_center(self) -> None:
        s = Shape(bounds=Rect(10, 20, 30, 40))
        assert s.center == Point(25, 40)

    def test_id_is_unique(self) -> None:
        a = Shape(bounds=Rect(0, 0, 1, 1))
        b = Shape(bounds=Rect(0, 0, 1, 1))
        assert a.id != b.id


class TestConnector:
    def test_default_values(self) -> None:
        c = Connector(from_shape_id="a", to_shape_id="b")
        assert c.connector_type == ConnectorType.STRAIGHT
        assert c.arrowhead_start is False
        assert c.arrowhead_end is True
        assert c.stroke_color == "#000000"
        assert c.stroke_width == 1.0

    def test_id_is_unique(self) -> None:
        a = Connector(from_shape_id="x", to_shape_id="y")
        b = Connector(from_shape_id="x", to_shape_id="y")
        assert a.id != b.id


class TestTextBox:
    def test_default_values(self) -> None:
        t = TextBox(text="hello", bounds=Rect(0, 0, 10, 10))
        assert t.font_family == "Arial"
        assert t.font_size_pt == 12.0
        assert t.color == "#000000"
        assert t.bold is False
        assert t.italic is False
        assert t.associated_shape_id is None

    def test_id_is_unique(self) -> None:
        a = TextBox(text="a", bounds=Rect(0, 0, 1, 1))
        b = TextBox(text="b", bounds=Rect(0, 0, 1, 1))
        assert a.id != b.id


class TestPage:
    def test_default_size(self) -> None:
        p = Page()
        assert p.width_mm == 210.0
        assert p.height_mm == 297.0
        assert p.name == "Page-1"

    def test_add_shape(self) -> None:
        p = Page()
        s = Shape(bounds=Rect(0, 0, 10, 10))
        p.add_shape(s)
        assert len(p.shapes) == 1
        assert p.shapes[0] == s

    def test_add_connector(self) -> None:
        p = Page()
        c = Connector(from_shape_id="a", to_shape_id="b")
        p.add_connector(c)
        assert len(p.connectors) == 1

    def test_add_text(self) -> None:
        p = Page()
        t = TextBox(text="hi", bounds=Rect(0, 0, 5, 5))
        p.add_text(t)
        assert len(p.texts) == 1

    def test_get_shape_by_id(self) -> None:
        p = Page()
        s = Shape(bounds=Rect(0, 0, 10, 10))
        p.add_shape(s)
        assert p.get_shape_by_id(s.id) == s
        assert p.get_shape_by_id("nonexistent") is None


class TestDiagram:
    def test_defaults(self) -> None:
        d = Diagram()
        assert d.title == "Untitled Diagram"
        assert d.author == ""
        assert d.page_count == 0

    def test_add_page(self) -> None:
        d = Diagram()
        p = Page(name="Test")
        d.add_page(p)
        assert d.page_count == 1
        assert d.pages[0].name == "Test"

    def test_get_page_by_id(self) -> None:
        d = Diagram()
        p = Page()
        d.add_page(p)
        assert d.get_page_by_id(p.id) == p
        assert d.get_page_by_id("missing") is None
