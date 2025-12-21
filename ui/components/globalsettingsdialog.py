from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class GlobalSettingsDialog(QDialog):
    """Global settings dialog for app-wide configuration"""

    def __init__(self, history_limit, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Global Settings")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("Global Settings")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)

        # Global Options
        settings_group = QGroupBox("Application")
        settings_layout = QHBoxLayout()

        settings_layout.addWidget(QLabel("Undo/Redo History Limit (10 - 200):"))
        self.history_spin = QSpinBox()
        self.history_spin.setRange(10, 200)
        self.history_spin.setSingleStep(10)
        self.history_spin.setValue(history_limit)
        settings_layout.addWidget(self.history_spin)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "danger")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Save")
        btn_save.setProperty("class", "success")
        btn_save.clicked.connect(self.accept)
        btn_save.setDefault(True)
        button_layout.addWidget(btn_save)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_values(self):
        """Return (history_limit)"""
        return self.history_spin.value()
