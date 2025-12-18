from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class InputDialog(QDialog):
    """Modern input dialog"""

    def __init__(self, title, placeholder="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)

        # Layout
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel(title)
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)

        # Input field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(placeholder)
        self.input_field.returnPressed.connect(self.accept)
        layout.addWidget(self.input_field)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "danger")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)

        btn_ok = QPushButton("OK")
        btn_ok.setProperty("class", "success")
        btn_ok.clicked.connect(self.accept)
        btn_ok.setDefault(True)
        button_layout.addWidget(btn_ok)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_text(self):
        """Get the entered text"""
        return self.input_field.text()
