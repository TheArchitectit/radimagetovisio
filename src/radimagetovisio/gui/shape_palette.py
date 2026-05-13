
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget

from radimagetovisio.models.diagram import Diagram, Page


class ShapePalette(QTreeWidget):
    item_selected = pyqtSignal(str, str)
    label_changed = pyqtSignal(str, str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._diagram: Diagram | None = None
        self._current_page: Page | None = None
        self._shape_nodes: dict[str, QTreeWidgetItem] = {}
        self._connector_nodes: dict[str, QTreeWidgetItem] = {}
        self._text_nodes: dict[str, QTreeWidgetItem] = {}

        self.setHeaderLabels(["Diagram Items"])
        self.setColumnCount(1)
        self.setEditTriggers(
            QTreeWidget.EditTrigger.DoubleClicked | QTreeWidget.EditTrigger.EditKeyPressed
        )
        self.itemClicked.connect(self._on_item_clicked)
        self.itemChanged.connect(self._on_item_changed)

    def set_diagram(self, diagram: Diagram | None) -> None:
        self._diagram = diagram
        self.clear()
        self._shape_nodes.clear()
        self._connector_nodes.clear()
        self._text_nodes.clear()

        if diagram is None or not diagram.pages:
            return

        self._current_page = diagram.pages[0]
        self._populate_tree(self._current_page)
        self.expandAll()

    def _populate_tree(self, page: Page) -> None:
        shapes_root = QTreeWidgetItem(self, ["Shapes"])
        shapes_root.setFlags(shapes_root.flags() & ~Qt.ItemFlag.ItemIsEditable)
        for shape in page.shapes:
            label = shape.label or f"{shape.shape_type.name} ({shape.id[:6]})"
            node = QTreeWidgetItem(shapes_root, [label])
            node.setFlags(node.flags() | Qt.ItemFlag.ItemIsEditable)
            node.setData(0, 1, ("shape", shape.id))
            self._shape_nodes[shape.id] = node

        connectors_root = QTreeWidgetItem(self, ["Connectors"])
        connectors_root.setFlags(connectors_root.flags() & ~Qt.ItemFlag.ItemIsEditable)
        for connector in page.connectors:
            label = connector.label or f"Connector ({connector.id[:6]})"
            node = QTreeWidgetItem(connectors_root, [label])
            node.setFlags(node.flags() | Qt.ItemFlag.ItemIsEditable)
            node.setData(0, 1, ("connector", connector.id))
            self._connector_nodes[connector.id] = node

        texts_root = QTreeWidgetItem(self, ["Texts"])
        texts_root.setFlags(texts_root.flags() & ~Qt.ItemFlag.ItemIsEditable)
        for text in page.texts:
            label = text.text or f"Text ({text.id[:6]})"
            node = QTreeWidgetItem(texts_root, [label])
            node.setFlags(node.flags() | Qt.ItemFlag.ItemIsEditable)
            node.setData(0, 1, ("text", text.id))
            self._text_nodes[text.id] = node

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        data = item.data(0, 1)
        if data is not None:
            kind, item_id = data
            self.item_selected.emit(kind, item_id)

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        data = item.data(0, 1)
        if data is None:
            return
        kind, item_id = data
        new_text = item.text(0)
        self.label_changed.emit(kind, item_id, new_text)

    def select_shape(self, shape_id: str) -> None:
        node = self._shape_nodes.get(shape_id)
        if node is not None:
            self.setCurrentItem(node)

    def select_connector(self, connector_id: str) -> None:
        node = self._connector_nodes.get(connector_id)
        if node is not None:
            self.setCurrentItem(node)

    def select_text(self, text_id: str) -> None:
        node = self._text_nodes.get(text_id)
        if node is not None:
            self.setCurrentItem(node)
