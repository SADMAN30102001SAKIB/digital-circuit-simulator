from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class SettingsDialog(QDialog):
    """Settings dialog for canvas and simulation options"""

    def __init__(self, canvas_size, grid_size, sim_fps, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("Settings")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)

        # Canvas Size
        canvas_group = QGroupBox("Canvas")
        canvas_layout = QVBoxLayout()

        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Canvas Size (10000 - 50000):"))
        self.canvas_size_spin = QSpinBox()
        self.canvas_size_spin.setRange(10000, 50000)
        self.canvas_size_spin.setSingleStep(5000)
        self.canvas_size_spin.setValue(canvas_size)
        self.canvas_size_spin.setSuffix(" px")
        size_layout.addWidget(self.canvas_size_spin)
        canvas_layout.addLayout(size_layout)

        grid_layout = QHBoxLayout()
        grid_layout.addWidget(QLabel("Grid Size (10 - 100):"))
        self.grid_size_spin = QSpinBox()
        self.grid_size_spin.setRange(10, 100)
        self.grid_size_spin.setSingleStep(10)
        self.grid_size_spin.setValue(grid_size)
        self.grid_size_spin.setSuffix(" px")
        grid_layout.addWidget(self.grid_size_spin)
        canvas_layout.addLayout(grid_layout)

        canvas_group.setLayout(canvas_layout)
        layout.addWidget(canvas_group)

        # Simulation
        sim_group = QGroupBox("Simulation")
        sim_layout = QHBoxLayout()
        sim_layout.addWidget(QLabel("Update Rate (15 - 120):"))
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(15, 120)
        self.fps_spin.setSingleStep(10)
        self.fps_spin.setValue(sim_fps)
        self.fps_spin.setSuffix(" FPS")
        sim_layout.addWidget(self.fps_spin)
        sim_group.setLayout(sim_layout)
        layout.addWidget(sim_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "danger")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)

        btn_apply = QPushButton("Apply")
        btn_apply.setProperty("class", "success")
        btn_apply.clicked.connect(self.accept)
        btn_apply.setDefault(True)
        button_layout.addWidget(btn_apply)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_values(self):
        """Return (canvas_size, grid_size, fps)"""
        return (
            self.canvas_size_spin.value(),
            self.grid_size_spin.value(),
            self.fps_spin.value(),
        )
