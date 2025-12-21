from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)


class FileListDialog(QDialog):
    """Dialog to select from a list of files"""

    def __init__(self, title, file_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(500, 400)

        # Layout
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel(title)
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)

        # List
        self.list_widget = QListWidget()
        for file in file_list:
            item = QListWidgetItem(file.stem)
            item.setData(Qt.UserRole, file)
            self.list_widget.addItem(item)

        self.list_widget.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.list_widget)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "danger")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)

        btn_load = QPushButton("Load")
        btn_load.setProperty("class", "success")
        btn_load.clicked.connect(self.accept)
        btn_load.setDefault(True)
        button_layout.addWidget(btn_load)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_selected_file(self):
        """Get the selected file"""
        current = self.list_widget.currentItem()
        if current:
            return current.data(Qt.UserRole)
        return None
