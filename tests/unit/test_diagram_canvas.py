
import pytest
from PyQt6.QtWidgets import QGraphicsItem

from radimagetovisio.gui.diagram_canvas import DiagramCanvas, _mm_to_px_rect
from radimagetovisio.models.diagram import (
    Connector,
    Diagram,
    Page,
    Shape,
    ShapeType,
    TextBox,
)
from radimagetovisio.models.geometry import Point, Rect


def _make_diagram_with_shape(shape_type: ShapeType = ShapeType.RECTANGLE) -> Diagram:
    page = Page()
    page.add_shape(Shape(bounds=Rect(10, 20, 100, 50), shape_type=shape_type))
    diagram = Diagram()
    diagram.add_page(page)
    return diagram


class TestMmToPxRect:
    def test_conversion(self):
        r = Rect(10, 20, 100, 50)
        result = _mm_to_px_rect(r)
        assert result.width > 0
        assert result.height > 0


class TestDiagramCanvas:
    def test_init(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        assert canvas._diagram is None

    def test_set_none_clears(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        canvas.set_diagram(None)
        assert canvas._diagram is None

    def test_set_empty_diagram(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        diagram = Diagram()
        canvas.set_diagram(diagram)
        assert canvas._diagram is not None

    def test_render_rectangle(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        diagram = _make_diagram_with_shape(ShapeType.RECTANGLE)
        canvas.set_diagram(diagram)
        shape_id = diagram.pages[0].shapes[0].id
        assert shape_id in canvas._shape_items

    def test_render_ellipse(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        diagram = _make_diagram_with_shape(ShapeType.ELLIPSE)
        canvas.set_diagram(diagram)
        shape_id = diagram.pages[0].shapes[0].id
        assert shape_id in canvas._shape_items

    def test_render_diamond(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        diagram = _make_diagram_with_shape(ShapeType.DIAMOND)
        canvas.set_diagram(diagram)
        shape_id = diagram.pages[0].shapes[0].id
        assert shape_id in canvas._shape_items

    def test_render_triangle(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        diagram = _make_diagram_with_shape(ShapeType.TRIANGLE)
        canvas.set_diagram(diagram)
        shape_id = diagram.pages[0].shapes[0].id
        assert shape_id in canvas._shape_items

    def test_render_parallelogram(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        diagram = _make_diagram_with_shape(ShapeType.PARALLELOGRAM)
        canvas.set_diagram(diagram)
        shape_id = diagram.pages[0].shapes[0].id
        assert shape_id in canvas._shape_items

    def test_render_container(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        diagram = _make_diagram_with_shape(ShapeType.CONTAINER)
        canvas.set_diagram(diagram)
        shape_id = diagram.pages[0].shapes[0].id
        assert shape_id in canvas._shape_items

    def test_render_text(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        page = Page()
        text = TextBox(text="Hello World", bounds=Rect(10, 10, 100, 20))
        page.add_text(text)
        diagram = Diagram()
        diagram.add_page(page)
        canvas.set_diagram(diagram)
        assert text.id in canvas._text_items

    def test_render_connector_with_points(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        page = Page()
        conn = Connector(
            from_shape_id="a",
            to_shape_id="b",
            from_point=Point(0, 0),
            to_point=Point(100, 100),
        )
        page.add_connector(conn)
        diagram = Diagram()
        diagram.add_page(page)
        canvas.set_diagram(diagram)
        assert conn.id in canvas._connector_items

    def test_render_connector_between_shapes(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        page = Page()
        s1 = Shape(bounds=Rect(0, 0, 50, 50), shape_type=ShapeType.RECTANGLE)
        s2 = Shape(bounds=Rect(100, 0, 50, 50), shape_type=ShapeType.RECTANGLE)
        page.add_shape(s1)
        page.add_shape(s2)
        conn = Connector(from_shape_id=s1.id, to_shape_id=s2.id)
        page.add_connector(conn)
        diagram = Diagram()
        diagram.add_page(page)
        canvas.set_diagram(diagram)
        assert conn.id in canvas._connector_items

    def test_highlight_shape(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        diagram = _make_diagram_with_shape(ShapeType.RECTANGLE)
        canvas.set_diagram(diagram)
        shape_id = diagram.pages[0].shapes[0].id
        canvas.highlight_shape(shape_id)
        item = canvas._shape_items[shape_id]
        assert item.isSelected()

    def test_highlight_text(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        page = Page()
        text = TextBox(text="Hi", bounds=Rect(0, 0, 50, 20))
        page.add_text(text)
        diagram = Diagram()
        diagram.add_page(page)
        canvas.set_diagram(diagram)
        canvas.highlight_text(text.id)
        item = canvas._text_items[text.id]
        assert item.isSelected()

    def test_clear_highlight(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        diagram = _make_diagram_with_shape(ShapeType.RECTANGLE)
        canvas.set_diagram(diagram)
        shape_id = diagram.pages[0].shapes[0].id
        canvas.highlight_shape(shape_id)
        canvas.clear_highlight()
        item = canvas._shape_items[shape_id]
        assert not item.isSelected()

    def test_zoom_in_out(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        diagram = _make_diagram_with_shape(ShapeType.RECTANGLE)
        canvas.set_diagram(diagram)
        canvas.zoom_in()
        canvas.zoom_out()

    def test_zoom_reset(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        diagram = _make_diagram_with_shape(ShapeType.RECTANGLE)
        canvas.set_diagram(diagram)
        canvas.zoom_in()
        canvas.zoom_reset()

    def test_multiple_shapes(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        page = Page()
        page.add_shape(Shape(bounds=Rect(0, 0, 10, 10), shape_type=ShapeType.RECTANGLE))
        page.add_shape(Shape(bounds=Rect(50, 50, 20, 20), shape_type=ShapeType.ELLIPSE))
        page.add_shape(Shape(bounds=Rect(100, 100, 30, 30), shape_type=ShapeType.DIAMOND))
        diagram = Diagram()
        diagram.add_page(page)
        canvas.set_diagram(diagram)
        assert len(canvas._shape_items) == 3

    def test_freehand_fallback(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        diagram = _make_diagram_with_shape(ShapeType.FREEHAND)
        canvas.set_diagram(diagram)
        shape_id = diagram.pages[0].shapes[0].id
        assert shape_id in canvas._shape_items

    def test_highlight_nonexistent_does_not_crash(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        canvas.highlight_shape("nonexistent")
        canvas.highlight_connector("nonexistent")
        canvas.highlight_text("nonexistent")

    def test_shape_item_is_movable(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        diagram = _make_diagram_with_shape(ShapeType.RECTANGLE)
        canvas.set_diagram(diagram)
        shape_id = diagram.pages[0].shapes[0].id
        item = canvas._shape_items[shape_id]
        assert bool(item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

    def test_text_item_is_movable(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        page = Page()
        text = TextBox(text="Hi", bounds=Rect(0, 0, 50, 20))
        page.add_text(text)
        diagram = Diagram()
        diagram.add_page(page)
        canvas.set_diagram(diagram)
        item = canvas._text_items[text.id]
        assert bool(item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

    def test_drag_commit_syncs_shape_model(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        diagram = _make_diagram_with_shape(ShapeType.RECTANGLE)
        canvas.set_diagram(diagram)
        shape = diagram.pages[0].shapes[0]
        item = canvas._shape_items[shape.id]
        original_pos = item.pos()
        canvas._drag_original_positions = {shape.id: original_pos}
        # Simulate moving the item 100 px right and 50 px down
        item.setPos(original_pos.x() + 100, original_pos.y() + 50)
        canvas._commit_item_moves()
        assert shape.bounds.x > 10  # should have increased
        assert shape.bounds.y > 20  # should have increased

    def test_drag_commit_syncs_text_model(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        page = Page()
        text = TextBox(text="Hi", bounds=Rect(5, 5, 50, 20))
        page.add_text(text)
        diagram = Diagram()
        diagram.add_page(page)
        canvas.set_diagram(diagram)
        item = canvas._text_items[text.id]
        original_pos = item.pos()
        canvas._drag_original_positions = {text.id: original_pos}
        item.setPos(original_pos.x() + 50, original_pos.y() + 25)
        canvas._commit_item_moves()
        assert text.bounds.x > 5
        assert text.bounds.y > 5

    def test_drag_commit_updates_connector_explicit_point(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        page = Page()
        s1 = Shape(bounds=Rect(0, 0, 50, 50), shape_type=ShapeType.RECTANGLE)
        s2 = Shape(bounds=Rect(100, 0, 50, 50), shape_type=ShapeType.RECTANGLE)
        page.add_shape(s1)
        page.add_shape(s2)
        conn = Connector(
            from_shape_id=s1.id,
            to_shape_id=s2.id,
            from_point=Point(25, 25),
            to_point=Point(125, 25),
        )
        page.add_connector(conn)
        diagram = Diagram()
        diagram.add_page(page)
        canvas.set_diagram(diagram)

        item = canvas._shape_items[s1.id]
        original_pos = item.pos()
        canvas._drag_original_positions = {s1.id: original_pos}
        item.setPos(original_pos.x() + 30, original_pos.y() + 20)
        canvas._commit_item_moves()

        assert conn.from_point is not None
        assert conn.from_point.x > 25
        assert conn.from_point.y > 25
        # to_point should be unchanged since s2 was not moved
        assert conn.to_point is not None
        assert conn.to_point.x == pytest.approx(125.0, abs=0.1)

    def test_current_zoom_percent_tracked(self, qtbot):
        canvas = DiagramCanvas()
        qtbot.addWidget(canvas)
        diagram = _make_diagram_with_shape(ShapeType.RECTANGLE)
        canvas.set_diagram(diagram)
        initial = canvas.current_zoom_percent()
        canvas.zoom_in()
        assert canvas.current_zoom_percent() > initial
