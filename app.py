import sys
from pathlib import Path

from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from simulator.main import CircuitSimulator
from ui.theme import MODERN_STYLE


def main():
    """Main entry point"""
    # Create application
    app = QApplication(sys.argv)

    # Resolve resource path that works for development and PyInstaller onefile/onedir
    def resource_path(rel_path: str) -> Path:
        # When bundled by PyInstaller, resources are extracted to sys._MEIPASS
        if getattr(sys, "frozen", False):
            return Path(sys._MEIPASS) / rel_path
        return Path(__file__).parent / rel_path

    # Set application icon
    icon_path = resource_path("assets/icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Set application-wide font with robust fallbacks
    font = QFont()
    font.setFamilies(["Segoe UI", "San Francisco", "Helvetica Neue", "Arial"])
    font.setPointSize(10)
    app.setFont(font)

    # Apply modern stylesheet
    app.setStyleSheet(MODERN_STYLE)

    # Set application info
    app.setApplicationName("Circuit Playground Pro")
    app.setOrganizationName("Circuit Simulator")
    app.setApplicationVersion("3.1.0")

    # Create and show main window
    window = CircuitSimulator()
    window.showMaximized()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
