import sys

from PyQt6.QtWidgets import QApplication

from radimagetovisio.gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("radimagetovisio")
    app.setApplicationDisplayName("RadImageToVisio")
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    return app.exec()
