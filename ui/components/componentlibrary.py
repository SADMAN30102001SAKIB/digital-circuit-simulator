from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QDockWidget, QListWidget, QListWidgetItem

from ui.theme import ACCENT, GATE_COLORS, NAVBAR_BG, TEXT_DIM


class ComponentLibrary(QDockWidget):
    """Left sidebar with draggable components"""

    componentSelected = Signal(object, str)  # component_class, name

    def __init__(self, components, parent=None):
        super().__init__("Components", parent)

        # Dock settings
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        )

        # Create list widget
        self.list_widget = QListWidget()
        self.list_widget.setSpacing(2)

        # Populate with components
        current_category = None
        for name, cls, category in components:
            if category and category != current_category:
                # Add category header
                current_category = category
                header_item = QListWidgetItem(f"  {category}  ")
                header_item.setFlags(Qt.NoItemFlags)
                header_item.setBackground(QColor(NAVBAR_BG))
                header_item.setForeground(QColor(TEXT_DIM))
                font = QFont("Segoe UI", 10, QFont.Bold)
                header_item.setFont(font)
                self.list_widget.addItem(header_item)

            # Add component
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, (cls, name))

            # Set background color
            color = GATE_COLORS.get(name, ACCENT)
            item.setBackground(QColor(color))
            item.setForeground(QColor("#FFFFFF"))

            font = QFont("Segoe UI", 12, QFont.Bold)
            item.setFont(font)
            item.setSizeHint(QSize(0, 44))

            self.list_widget.addItem(item)

        # Connect signal
        self.list_widget.itemClicked.connect(self._on_item_clicked)

        self.setWidget(self.list_widget)

    def _on_item_clicked(self, item):
        """Handle component selection"""
        data = item.data(Qt.UserRole)
        if data:
            component_class, name = data
            self.componentSelected.emit(component_class, name)
