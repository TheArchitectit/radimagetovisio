from PyQt6.QtCore import QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPolygonItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QWidget,
)

from radimagetovisio.models.diagram import (
    Connector,
    Diagram,
    Page,
    Shape,
    ShapeType,
    TextBox,
)
from radimagetovisio.models.geometry import Point, Rect, mm_to_px, px_to_mm

MM_SCALE = 3.78


def _mm_to_px_rect(r: Rect) -> Rect:
    return Rect(
        mm_to_px(r.x) * MM_SCALE,
        mm_to_px(r.y) * MM_SCALE,
        mm_to_px(r.width) * MM_SCALE,
        mm_to_px(r.height) * MM_SCALE,
    )


def _point_to_qpointf(p: Point):
    return QPointF(p.x, p.y)


class DiagramCanvas(QGraphicsView):
    zoom_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._diagram: Diagram | None = None
        self._current_page: Page | None = None
        self._shape_items: dict[str, QGraphicsItem] = {}
        self._connector_items: dict[str, QGraphicsLineItem] = {}
        self._text_items: dict[str, QGraphicsTextItem] = {}
        self._model_positions: dict[str, QPointF] = {}
        self._drag_original_positions: dict[str, QPointF] = {}
        self._old_drag_mode = QGraphicsView.DragMode.ScrollHandDrag

        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setRenderHints(self.renderHints())

    def set_diagram(self, diagram: Diagram | None) -> None:
        self._diagram = diagram
        self._shape_items.clear()
        self._connector_items.clear()
        self._text_items.clear()
        self._model_positions.clear()
        self._scene.clear()

        if diagram is None or not diagram.pages:
            return

        self._current_page = diagram.pages[0]
        self._render_page(self._current_page)
        self._scene.setSceneRect(self._scene.itemsBoundingRect())
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.zoom_changed.emit()

    def _render_page(self, page: Page) -> None:
        for shape in page.shapes:
            item = self._create_shape_item(shape)
            if item is not None:
                self._shape_items[shape.id] = item
                self._scene.addItem(item)
                self._model_positions[shape.id] = item.pos()

        for text in page.texts:
            item = self._create_text_item(text)
            if item is not None:
                self._text_items[text.id] = item
                self._scene.addItem(item)
                self._model_positions[text.id] = item.pos()

        for connector in page.connectors:
            item = self._create_connector_item(connector)
            if item is not None:
                self._connector_items[connector.id] = item
                self._scene.addItem(item)

    def _create_shape_item(self, shape: Shape) -> QGraphicsItem | None:
        r = _mm_to_px_rect(shape.bounds)
        pen = QPen(QColor(shape.stroke_color), shape.stroke_width)
        brush = QBrush(QColor(shape.fill_color))

        if shape.shape_type == ShapeType.ELLIPSE:
            item = QGraphicsEllipseItem(0, 0, r.width, r.height)
        elif shape.shape_type in (ShapeType.RECTANGLE, ShapeType.CONTAINER):
            item = QGraphicsRectItem(0, 0, r.width, r.height)
        elif shape.shape_type == ShapeType.DIAMOND:
            cx = r.width / 2
            cy = r.height / 2
            polygon = QPolygonF(
                [
                    QPointF(cx, 0),
                    QPointF(r.width, cy),
                    QPointF(cx, r.height),
                    QPointF(0, cy),
                ]
            )
            item = QGraphicsPolygonItem(polygon)
        elif shape.shape_type == ShapeType.TRIANGLE:
            polygon = QPolygonF(
                [
                    QPointF(r.width / 2, 0),
                    QPointF(r.width, r.height),
                    QPointF(0, r.height),
                ]
            )
            item = QGraphicsPolygonItem(polygon)
        elif shape.shape_type == ShapeType.PARALLELOGRAM:
            offset = r.width * 0.2
            polygon = QPolygonF(
                [
                    QPointF(offset, 0),
                    QPointF(r.width, 0),
                    QPointF(r.width - offset, r.height),
                    QPointF(0, r.height),
                ]
            )
            item = QGraphicsPolygonItem(polygon)
        else:
            item = QGraphicsRectItem(0, 0, r.width, r.height)

        item.setPos(r.x, r.y)
        item.setPen(pen)
        item.setBrush(brush)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        item.setData(0, shape.id)
        item.setZValue(shape.z_order)
        item.setOpacity(shape.opacity)
        return item

    def _create_connector_item(self, connector: Connector) -> QGraphicsLineItem | None:
        from_point = connector.from_point
        to_point = connector.to_point

        if from_point is None or to_point is None:
            if self._current_page is None:
                return None
            from_shape = self._current_page.get_shape_by_id(connector.from_shape_id)
            to_shape = self._current_page.get_shape_by_id(connector.to_shape_id)
            if from_shape is None or to_shape is None:
                return None
            from_point = from_shape.center
            to_point = to_shape.center

        if from_point is None or to_point is None:
            return None

        p1 = _mm_point_to_scene_px(from_point)
        p2 = _mm_point_to_scene_px(to_point)
        item = QGraphicsLineItem(p1.x(), p1.y(), p2.x(), p2.y())
        pen = QPen(QColor(connector.stroke_color), connector.stroke_width)
        item.setPen(pen)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setData(0, connector.id)
        return item

    def _create_text_item(self, text: TextBox) -> QGraphicsTextItem | None:
        r = _mm_to_px_rect(text.bounds)
        item = QGraphicsTextItem(text.text)
        item.setPos(r.x, r.y)
        font = item.font()
        font.setFamily(text.font_family)
        font.setPointSizeF(text.font_size_pt)
        font.setBold(text.bold)
        font.setItalic(text.italic)
        item.setFont(font)
        item.setDefaultTextColor(QColor(text.color))
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        item.setData(0, text.id)
        return item

    def highlight_shape(self, shape_id: str) -> None:
        item = self._shape_items.get(shape_id)
        if item is not None:
            item.setSelected(True)
            self.centerOn(item)

    def highlight_connector(self, connector_id: str) -> None:
        item = self._connector_items.get(connector_id)
        if item is not None:
            item.setSelected(True)
            self.centerOn(item)

    def highlight_text(self, text_id: str) -> None:
        item = self._text_items.get(text_id)
        if item is not None:
            item.setSelected(True)
            self.centerOn(item)

    def clear_highlight(self) -> None:
        for item in self._scene.selectedItems():
            item.setSelected(False)

    def current_zoom_percent(self) -> int:
        return round(self.transform().m11() * 100)

    def zoom_in(self) -> None:
        self.scale(1.2, 1.2)
        self.zoom_changed.emit()

    def zoom_out(self) -> None:
        self.scale(1 / 1.2, 1 / 1.2)
        self.zoom_changed.emit()

    def zoom_reset(self) -> None:
        self.resetTransform()
        if self._scene.sceneRect().width() > 0:
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.zoom_changed.emit()

    def zoom_fit(self) -> None:
        self.resetTransform()
        if self._scene.sceneRect().width() > 0:
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.zoom_changed.emit()

    def wheelEvent(self, event) -> None:
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event) -> None:
        item = self.itemAt(event.pos())
        if item is not None and bool(
            item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        ):
            self._old_drag_mode = self.dragMode()
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self._drag_original_positions = {}
            for selected in self._scene.selectedItems():
                if selected.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable:
                    sid = selected.data(0)
                    if sid:
                        self._drag_original_positions[sid] = selected.pos()
            clicked_id = item.data(0)
            if clicked_id and clicked_id not in self._drag_original_positions:
                self._drag_original_positions[clicked_id] = item.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)
        if self._drag_original_positions:
            self._commit_item_moves()
            self.setDragMode(self._old_drag_mode)
            self._drag_original_positions = {}

    def _commit_item_moves(self) -> None:
        if self._current_page is None:
            return
        for item_id, original_pos in self._drag_original_positions.items():
            item = self._shape_items.get(item_id) or self._text_items.get(item_id)
            if item is None:
                continue
            new_pos = item.pos()
            delta = new_pos - original_pos
            if delta.x() == 0 and delta.y() == 0:
                continue
            dx_mm = px_to_mm(delta.x() / MM_SCALE)
            dy_mm = px_to_mm(delta.y() / MM_SCALE)

            shape = self._current_page.get_shape_by_id(item_id)
            if shape is not None:
                shape.bounds = Rect(
                    shape.bounds.x + dx_mm,
                    shape.bounds.y + dy_mm,
                    shape.bounds.width,
                    shape.bounds.height,
                )
                self._update_connectors_for_shape(shape.id, dx_mm, dy_mm)
                self._model_positions[item_id] = new_pos
                continue

            text = self._current_page.get_text_by_id(item_id)
            if text is not None:
                text.bounds = Rect(
                    text.bounds.x + dx_mm,
                    text.bounds.y + dy_mm,
                    text.bounds.width,
                    text.bounds.height,
                )
                self._model_positions[item_id] = new_pos

    def _update_connectors_for_shape(self, shape_id: str, dx_mm: float, dy_mm: float) -> None:
        if self._current_page is None:
            return
        for connector in self._current_page.connectors:
            updated = False
            if connector.from_shape_id == shape_id and connector.from_point is not None:
                connector.from_point = Point(
                    connector.from_point.x + dx_mm,
                    connector.from_point.y + dy_mm,
                )
                updated = True
            if connector.to_shape_id == shape_id and connector.to_point is not None:
                connector.to_point = Point(
                    connector.to_point.x + dx_mm,
                    connector.to_point.y + dy_mm,
                )
                updated = True
            if updated:
                self._update_connector_graphics(connector.id)

    def _update_connector_graphics(self, connector_id: str) -> None:
        item = self._connector_items.get(connector_id)
        if item is None or self._current_page is None:
            return
        connector = None
        for c in self._current_page.connectors:
            if c.id == connector_id:
                connector = c
                break
        if connector is None:
            return

        from_point = connector.from_point
        to_point = connector.to_point
        if from_point is None or to_point is None:
            from_shape = self._current_page.get_shape_by_id(connector.from_shape_id)
            to_shape = self._current_page.get_shape_by_id(connector.to_shape_id)
            if from_shape is not None:
                from_point = from_shape.center
            if to_shape is not None:
                to_point = to_shape.center

        if from_point is None or to_point is None:
            return

        p1 = _mm_point_to_scene_px(from_point)
        p2 = _mm_point_to_scene_px(to_point)
        item.setLine(p1.x(), p1.y(), p2.x(), p2.y())


def _mm_point_to_scene_px(p: Point) -> QPointF:
    return QPointF(mm_to_px(p.x) * MM_SCALE, mm_to_px(p.y) * MM_SCALE)
