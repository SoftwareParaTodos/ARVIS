import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from ui.arvis_window import ArvisWindow


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("ARVIS")
    app.setOrganizationName("ARVIS Open Source")

    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)

    window = ArvisWindow()
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
