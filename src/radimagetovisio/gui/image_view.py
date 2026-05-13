from pathlib import Path

import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QWidget,
)


class ImageView(QGraphicsView):
    zoom_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._pixmap_item: QGraphicsPixmapItem | None = None
        self._overlay_item: QGraphicsPixmapItem | None = None
        self._overlay_visible = False
        self._zoom_factor = 1.0

        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setRenderHints(self.renderHints())

    def load_image(self, source: str | Path | np.ndarray) -> None:
        if isinstance(source, (str, Path)):
            pixmap = QPixmap(str(source))
        elif isinstance(source, np.ndarray):
            pixmap = self._numpy_to_pixmap(source)
        else:
            raise TypeError(f"Unsupported image source type: {type(source)}")

        self._scene.clear()
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(pixmap.rect().toRectF())
        self._zoom_factor = 1.0
        self.resetTransform()
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.zoom_changed.emit()

    def _numpy_to_pixmap(self, arr: np.ndarray) -> QPixmap:
        if arr.ndim == 2:
            height, width = arr.shape
            bytes_per_line = width
            image = QImage(arr.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)
        elif arr.ndim == 3 and arr.shape[2] == 3:
            height, width, _ = arr.shape
            bytes_per_line = 3 * width
            image = QImage(arr.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        elif arr.ndim == 3 and arr.shape[2] == 4:
            height, width, _ = arr.shape
            bytes_per_line = 4 * width
            image = QImage(arr.data, width, height, bytes_per_line, QImage.Format.Format_ARGB32)
        else:
            raise ValueError(f"Unsupported array shape for QImage: {arr.shape}")
        return QPixmap.fromImage(image)

    def clear(self) -> None:
        self._scene.clear()
        self._pixmap_item = None
        self._overlay_item = None
        self._zoom_factor = 1.0
        self.resetTransform()

    def set_overlay_visible(self, visible: bool) -> None:
        self._overlay_visible = visible
        if self._overlay_item is not None:
            self._overlay_item.setVisible(visible)

    def set_overlay_image(self, arr: np.ndarray) -> None:
        pixmap = self._numpy_to_pixmap(arr)
        if self._overlay_item is not None:
            self._scene.removeItem(self._overlay_item)
        self._overlay_item = self._scene.addPixmap(pixmap)
        self._overlay_item.setVisible(self._overlay_visible)
        self._overlay_item.setZValue(10)

    def current_zoom_percent(self) -> int:
        return round(self.transform().m11() * 100)

    def zoom_in(self) -> None:
        self._zoom_factor *= 1.2
        self.scale(1.2, 1.2)
        self.zoom_changed.emit()

    def zoom_out(self) -> None:
        self._zoom_factor /= 1.2
        self.scale(1 / 1.2, 1 / 1.2)
        self.zoom_changed.emit()

    def zoom_reset(self) -> None:
        self._zoom_factor = 1.0
        self.resetTransform()
        if self._pixmap_item is not None:
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.zoom_changed.emit()

    def zoom_fit(self) -> None:
        self._zoom_factor = 1.0
        self.resetTransform()
        if self._pixmap_item is not None:
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
