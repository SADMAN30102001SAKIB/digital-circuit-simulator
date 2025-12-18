from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class ConfirmDialog(QDialog):
    """Confirmation dialog"""

    def __init__(self, title, message, yes_text="Yes", no_text="No", parent=None):
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

        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        btn_no = QPushButton(no_text)
        btn_no.setProperty("class", "danger")
        btn_no.clicked.connect(self.reject)
        button_layout.addWidget(btn_no)

        btn_yes = QPushButton(yes_text)
        btn_yes.setProperty("class", "success")
        btn_yes.clicked.connect(self.accept)
        btn_yes.setDefault(True)
        button_layout.addWidget(btn_yes)

        layout.addLayout(button_layout)
        self.setLayout(layout)
