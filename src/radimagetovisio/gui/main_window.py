from pathlib import Path

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QSplitter,
    QStatusBar,
    QToolBar,
)

from radimagetovisio.gui.diagram_canvas import DiagramCanvas
from radimagetovisio.gui.image_view import ImageView
from radimagetovisio.gui.shape_palette import ShapePalette
from radimagetovisio.models.diagram import Diagram
from radimagetovisio.utils.image_io import load_image


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RadImageToVisio")
        self.setMinimumSize(1024, 768)

        self._current_image: np.ndarray | None = None
        self._current_image_path: Path | None = None
        self._current_diagram: Diagram | None = None

        self._image_view = ImageView()
        self._diagram_canvas = DiagramCanvas()
        self._shape_palette = ShapePalette()
        self._shape_palette.item_selected.connect(self._on_palette_item_selected)

        self._build_menu()
        self._build_toolbar()
        self._build_central_widget()
        self._build_palette_dock()
        self._build_status_bar()

        self._image_view.zoom_changed.connect(self._update_zoom_label)
        self._diagram_canvas.zoom_changed.connect(self._update_zoom_label)

    def _build_menu(self) -> None:
        menu = self.menuBar()

        file_menu = menu.addMenu("File")
        self._act_open = QAction("Open Image...", self)
        self._act_open.setShortcut(QKeySequence.StandardKey.Open)
        self._act_open.triggered.connect(self._on_open)
        file_menu.addAction(self._act_open)

        self._act_detect = QAction("Run Detection", self)
        self._act_detect.setShortcut(QKeySequence("Ctrl+D"))
        self._act_detect.triggered.connect(self._on_run_detection)
        self._act_detect.setEnabled(False)
        file_menu.addAction(self._act_detect)

        self._act_export = QAction("Export Diagram...", self)
        self._act_export.setShortcut(QKeySequence("Ctrl+E"))
        self._act_export.triggered.connect(self._on_export)
        self._act_export.setEnabled(False)
        file_menu.addAction(self._act_export)

        file_menu.addSeparator()
        self._act_quick = QAction("Quick Convert...", self)
        self._act_quick.setShortcut(QKeySequence("Ctrl+Q"))
        self._act_quick.triggered.connect(self._on_quick_convert)
        file_menu.addAction(self._act_quick)

        file_menu.addSeparator()
        self._act_exit = QAction("Exit", self)
        self._act_exit.setShortcut(QKeySequence.StandardKey.Quit)
        self._act_exit.triggered.connect(self.close)
        file_menu.addAction(self._act_exit)

        view_menu = menu.addMenu("View")
        act_zoom_in = QAction("Zoom In", self)
        act_zoom_in.setShortcut(QKeySequence.StandardKey.ZoomIn)
        act_zoom_in.triggered.connect(self._on_zoom_in)
        view_menu.addAction(act_zoom_in)

        act_zoom_out = QAction("Zoom Out", self)
        act_zoom_out.setShortcut(QKeySequence.StandardKey.ZoomOut)
        act_zoom_out.triggered.connect(self._on_zoom_out)
        view_menu.addAction(act_zoom_out)

        act_zoom_reset = QAction("Zoom Reset", self)
        act_zoom_reset.setShortcut(QKeySequence("Ctrl+0"))
        act_zoom_reset.triggered.connect(self._on_zoom_reset)
        view_menu.addAction(act_zoom_reset)

        act_zoom_fit = QAction("Zoom to Fit", self)
        act_zoom_fit.setShortcut(QKeySequence("Ctrl+9"))
        act_zoom_fit.triggered.connect(self._on_zoom_fit)
        view_menu.addAction(act_zoom_fit)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar", self)
        self.addToolBar(toolbar)

        toolbar.addAction(self._act_open)
        toolbar.addAction(self._act_detect)
        toolbar.addAction(self._act_export)
        toolbar.addSeparator()

        act_zoom_in = QAction("Zoom In", self)
        act_zoom_in.setShortcut(QKeySequence.StandardKey.ZoomIn)
        act_zoom_in.triggered.connect(self._on_zoom_in)
        toolbar.addAction(act_zoom_in)

        act_zoom_out = QAction("Zoom Out", self)
        act_zoom_out.setShortcut(QKeySequence.StandardKey.ZoomOut)
        act_zoom_out.triggered.connect(self._on_zoom_out)
        toolbar.addAction(act_zoom_out)

        act_zoom_reset = QAction("Reset Zoom", self)
        act_zoom_reset.setShortcut(QKeySequence("Ctrl+0"))
        act_zoom_reset.triggered.connect(self._on_zoom_reset)
        toolbar.addAction(act_zoom_reset)

    def _build_central_widget(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._image_view)
        splitter.addWidget(self._diagram_canvas)
        splitter.setSizes([512, 512])
        self.setCentralWidget(splitter)

    def _build_palette_dock(self) -> None:
        dock = QDockWidget("Palette", self)
        dock.setWidget(self._shape_palette)
        dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _build_status_bar(self) -> None:
        self._status_bar = QStatusBar(self)
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")
        self._zoom_label = QLabel("Image: 100% | Diagram: 100%")
        self._status_bar.addPermanentWidget(self._zoom_label)

    def _update_zoom_label(self) -> None:
        img = self._image_view.current_zoom_percent()
        dia = self._diagram_canvas.current_zoom_percent()
        self._zoom_label.setText(f"Image: {img}% | Diagram: {dia}%")

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif);;All Files (*)",
        )
        if not path:
            return

        try:
            result = load_image(path)
            self._current_image = result.array
            self._current_image_path = result.path
            self._image_view.load_image(result.array)
            self._status_bar.showMessage(
                f"Loaded {result.path.name} ({result.width}x{result.height})"
            )
            self._act_detect.setEnabled(True)
            self._act_export.setEnabled(False)
        except Exception as exc:
            QMessageBox.critical(self, "Open Error", str(exc))

    def _on_run_detection(self) -> None:
        if self._current_image is None:
            return

        progress = QProgressDialog("Running detection...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        def _progress_cb(step: str, percent: int) -> None:
            progress.setLabelText(step)
            progress.setValue(int(percent))

        try:
            from radimagetovisio.utils.image_io import ImageLoadResult
            from radimagetovisio.vision.pipeline import run_pipeline

            image_result = ImageLoadResult(
                path=self._current_image_path or Path(""),
                array=self._current_image,
                width=self._current_image.shape[1],
                height=self._current_image.shape[0],
                mode="RGB",
                dpi=(96.0, 96.0),
            )
            diagram = run_pipeline(
                image_result,
                progress=_progress_cb,
                detect_shapes=True,
                detect_text=True,
                deduplicate=True,
                infer_connectors=True,
            )
            self._current_diagram = diagram

            self._diagram_canvas.set_diagram(diagram)
            self._shape_palette.set_diagram(diagram)
            total_shapes = len(diagram.pages[0].shapes) if diagram.pages else 0
            total_connectors = len(diagram.pages[0].connectors) if diagram.pages else 0
            total_texts = len(diagram.pages[0].texts) if diagram.pages else 0
            self._status_bar.showMessage(
                f"Detected {total_shapes} shapes, {total_connectors} connectors, {total_texts} texts"
            )
            self._act_export.setEnabled(True)
        except Exception as exc:
            QMessageBox.critical(self, "Detection Error", str(exc))
        finally:
            progress.close()

    def _on_export(self) -> None:
        if self._current_diagram is None:
            return

        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Diagram",
            "",
            "Visio Files (*.vsdx);;SVG Files (*.svg)",
        )
        if not path:
            return

        try:
            if selected_filter.startswith("Visio") or path.lower().endswith(".vsdx"):
                from radimagetovisio.exporters.vsdx.package import export_vsdx

                export_vsdx(self._current_diagram, path)
            else:
                from radimagetovisio.exporters.svg_exporter import export_svg

                export_svg(self._current_diagram, path)
            self._status_bar.showMessage(f"Exported to {path}")
        except ImportError:
            QMessageBox.warning(self, "Export", "Exporter not yet available.")
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", str(exc))

    def _on_quick_convert(self) -> None:
        if self._current_image is None:
            self._on_open()
            if self._current_image is None:
                return

        self._on_run_detection()
        if self._current_diagram is None:
            return

        self._on_export()

    def _on_zoom_in(self) -> None:
        self._image_view.zoom_in()
        self._diagram_canvas.zoom_in()

    def _on_zoom_out(self) -> None:
        self._image_view.zoom_out()
        self._diagram_canvas.zoom_out()

    def _on_zoom_reset(self) -> None:
        self._image_view.zoom_reset()
        self._diagram_canvas.zoom_reset()

    def _on_zoom_fit(self) -> None:
        self._image_view.zoom_fit()
        self._diagram_canvas.zoom_fit()

    def _on_palette_item_selected(self, kind: str, item_id: str) -> None:
        self._diagram_canvas.clear_highlight()
        if kind == "shape":
            self._diagram_canvas.highlight_shape(item_id)
        elif kind == "connector":
            self._diagram_canvas.highlight_connector(item_id)
        elif kind == "text":
            self._diagram_canvas.highlight_text(item_id)
