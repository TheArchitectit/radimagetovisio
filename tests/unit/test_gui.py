import numpy as np
import pytest

from radimagetovisio.gui.image_view import ImageView
from radimagetovisio.gui.shape_palette import ShapePalette
from radimagetovisio.models.diagram import (
    Connector,
    Diagram,
    Page,
    Shape,
    ShapeType,
    TextBox,
)
from radimagetovisio.models.geometry import Rect


class TestImageView:
    def test_init(self, qtbot):
        view = ImageView()
        qtbot.addWidget(view)
        assert view._pixmap_item is None

    def test_load_numpy_rgb(self, qtbot):
        view = ImageView()
        qtbot.addWidget(view)
        img = np.full((100, 200, 3), 128, dtype=np.uint8)
        view.load_image(img)
        assert view._pixmap_item is not None

    def test_load_numpy_grayscale(self, qtbot):
        view = ImageView()
        qtbot.addWidget(view)
        img = np.full((50, 50), 200, dtype=np.uint8)
        view.load_image(img)
        assert view._pixmap_item is not None

    def test_load_numpy_rgba(self, qtbot):
        view = ImageView()
        qtbot.addWidget(view)
        img = np.full((50, 50, 4), 255, dtype=np.uint8)
        view.load_image(img)
        assert view._pixmap_item is not None

    def test_load_invalid_type_raises(self, qtbot):
        view = ImageView()
        qtbot.addWidget(view)
        with pytest.raises(TypeError):
            view.load_image(42)

    def test_clear(self, qtbot):
        view = ImageView()
        qtbot.addWidget(view)
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        view.load_image(img)
        view.clear()
        assert view._pixmap_item is None

    def test_overlay_toggle(self, qtbot):
        view = ImageView()
        qtbot.addWidget(view)
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        view.load_image(img)
        overlay = np.full((10, 10, 3), 255, dtype=np.uint8)
        view.set_overlay_image(overlay)
        assert view._overlay_item is not None
        view.set_overlay_visible(True)
        assert view._overlay_item.isVisible()
        view.set_overlay_visible(False)
        assert not view._overlay_item.isVisible()

    def test_zoom_in(self, qtbot):
        view = ImageView()
        qtbot.addWidget(view)
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        view.load_image(img)
        initial = view._zoom_factor
        view.zoom_in()
        assert view._zoom_factor > initial

    def test_zoom_out(self, qtbot):
        view = ImageView()
        qtbot.addWidget(view)
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        view.load_image(img)
        view.zoom_in()
        initial = view._zoom_factor
        view.zoom_out()
        assert view._zoom_factor < initial

    def test_zoom_reset(self, qtbot):
        view = ImageView()
        qtbot.addWidget(view)
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        view.load_image(img)
        view.zoom_in()
        view.zoom_reset()
        assert view._zoom_factor == 1.0


class TestShapePalette:
    def test_init(self, qtbot):
        palette = ShapePalette()
        qtbot.addWidget(palette)
        assert palette._diagram is None

    def test_set_empty_diagram(self, qtbot):
        palette = ShapePalette()
        qtbot.addWidget(palette)
        palette.set_diagram(Diagram())
        assert palette.topLevelItemCount() == 0

    def test_set_diagram_with_shapes(self, qtbot):
        palette = ShapePalette()
        qtbot.addWidget(palette)
        page = Page()
        page.add_shape(Shape(bounds=Rect(0, 0, 10, 10), shape_type=ShapeType.RECTANGLE))
        page.add_shape(Shape(bounds=Rect(20, 20, 30, 30), shape_type=ShapeType.ELLIPSE))
        diagram = Diagram()
        diagram.add_page(page)
        palette.set_diagram(diagram)
        assert palette.topLevelItemCount() == 3  # Shapes, Connectors, Texts roots

    def test_set_diagram_with_all_types(self, qtbot):
        palette = ShapePalette()
        qtbot.addWidget(palette)
        page = Page()
        page.add_shape(Shape(bounds=Rect(0, 0, 10, 10)))
        page.add_connector(Connector(from_shape_id="a", to_shape_id="b"))
        page.add_text(TextBox(text="Hello", bounds=Rect(0, 0, 50, 20)))
        diagram = Diagram()
        diagram.add_page(page)
        palette.set_diagram(diagram)
        assert palette.topLevelItemCount() == 3

    def test_select_shape(self, qtbot):
        palette = ShapePalette()
        qtbot.addWidget(palette)
        page = Page()
        shape = Shape(bounds=Rect(0, 0, 10, 10), shape_type=ShapeType.RECTANGLE)
        page.add_shape(shape)
        diagram = Diagram()
        diagram.add_page(page)
        palette.set_diagram(diagram)
        palette.select_shape(shape.id)
        assert palette.currentItem() is not None

    def test_set_none_clears(self, qtbot):
        palette = ShapePalette()
        qtbot.addWidget(palette)
        page = Page()
        page.add_shape(Shape(bounds=Rect(0, 0, 10, 10)))
        diagram = Diagram()
        diagram.add_page(page)
        palette.set_diagram(diagram)
        palette.set_diagram(None)
        assert palette.topLevelItemCount() == 0


class TestMainWindow:
    def test_view_menu_exists(self, qtbot):
        from radimagetovisio.gui.main_window import MainWindow

        window = MainWindow()
        qtbot.addWidget(window)
        menus = [window.menuBar().actions()[i].text() for i in range(len(window.menuBar().actions()))]
        assert "View" in menus

    def test_status_bar_shows_zoom(self, qtbot):
        from radimagetovisio.gui.main_window import MainWindow

        window = MainWindow()
        qtbot.addWidget(window)
        text = window._zoom_label.text()
        assert "Image:" in text
        assert "Diagram:" in text

    def test_zoom_fit_updates_label(self, qtbot):
        from radimagetovisio.gui.main_window import MainWindow

        window = MainWindow()
        qtbot.addWidget(window)
        window._on_zoom_fit()
        text = window._zoom_label.text()
        assert "%" in text
