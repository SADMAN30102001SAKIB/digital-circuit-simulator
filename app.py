import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from simulator.main import CircuitSimulator
from simulator.utils import get_resource_path, setup_logging
from ui.theme import MODERN_STYLE


def main():
    """Main entry point"""
    # Create application
    app = QApplication(sys.argv)

    # Setup Logging in User Documents
    docs = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
    app_dir = (
        Path(docs) / "CircuitPlaygroundPro" if docs else Path("CircuitPlaygroundPro")
    )
    app_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(app_dir / "simulator.log")

    # Set application info
    app.setApplicationName("Circuit Playground Pro")
    app.setOrganizationName("Circuit Simulator")
    app.setApplicationVersion("3.1.1")

    # Set application icon
    icon_path = get_resource_path("assets/icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Set application-wide font with robust fallbacks
    font = QFont()
    font.setFamilies(["Segoe UI", "San Francisco", "Helvetica Neue", "Arial"])
    font.setPointSize(10)
    app.setFont(font)

    # Apply modern stylesheet
    app.setStyleSheet(MODERN_STYLE)

    # Create and show main window
    window = CircuitSimulator()
    window.show()  # Let QSettings handle showMaximized if it was saved that way

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
