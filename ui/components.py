from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QDialog,
    QDockWidget,
    QFontComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.annotations import (
    Annotation,
    CircleAnnotation,
    RectangleAnnotation,
    TextAnnotation,
)
from ui.theme import *


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


class PropertyPanel(QDockWidget):
    """Right sidebar for component properties"""

    actionTriggered = Signal(str)  # action name

    def __init__(self, parent=None):
        super().__init__("Circuit Components", parent)  # Default title

        # Dock settings
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        )

        # Main widget with scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.content_widget = QWidget()
        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(12, 12, 12, 12)

        self.scroll_area.setWidget(self.content_widget)
        self.setWidget(self.scroll_area)

        # Set minimum width for better visibility
        # Increased to accommodate wider controls and numeric fields
        self.setMinimumWidth(305)

        # Current target (can be gate or annotation)
        self.target_gate = None
        self.target_annotation = None
        self.gates_list = []
        self.annotations_list = []
        self.live_labels = {}

        # Show empty state
        self._show_component_list()

        # Schedule a short non-blocking pre-warm of commonly-used widgets to
        # avoid first-selection stalls caused by lazy initialization of Qt
        # style/font resources (this runs after the event loop starts).
        QTimer.singleShot(0, self._prewarm_widgets)

    def set_target(self, target):
        """Set the gate or annotation to display properties for"""
        if isinstance(target, Annotation):
            self.target_annotation = target
            self.target_gate = None
        else:
            self.target_gate = target
            self.target_annotation = None
        self._update_display()

    def _clear_layout(self):
        """Clear all widgets from layout"""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _update_display(self):
        """Update the property display"""
        self._clear_layout()

        # Handle annotation display
        if self.target_annotation:
            self._update_annotation_display()
            return

        if not self.target_gate:
            self.setWindowTitle("Circuit Components")
            self._show_component_list()
            return

        # Update title to show Properties when a gate is selected
        self.setWindowTitle(f"Properties - {self.target_gate.name}")

        # Rotation
        rot_label = QLabel(f"Rotation: {self.target_gate.rotation}°")
        self.layout.addWidget(rot_label)

        # Store labels that need live updates
        self.live_labels = {}

        # Inputs/Outputs
        if self.target_gate.name in ["MUX", "DEMUX"]:
            if self.target_gate.name == "MUX":
                data_inputs = self.target_gate.num_data_inputs
            else:
                data_inputs = 1

            input_label = QLabel(f"Data Inputs: {data_inputs}")
            self.layout.addWidget(input_label)

            select_label = QLabel(f"Select Lines: {self.target_gate.select_bits}")
            self.layout.addWidget(select_label)
        elif hasattr(self.target_gate, "num_inputs"):
            input_label = QLabel(f"Inputs: {self.target_gate.num_inputs}")
            self.layout.addWidget(input_label)

        if hasattr(self.target_gate, "num_outputs"):
            output_label = QLabel(f"Outputs: {self.target_gate.num_outputs}")
            self.layout.addWidget(output_label)

        # Live state display for INPUT/LED
        if self.target_gate.name == "INPUT":
            state_label = QLabel()
            self.live_labels["input_state"] = state_label
            self.layout.addWidget(state_label)
        elif self.target_gate.name == "LED":
            state_label = QLabel()
            self.live_labels["led_state"] = state_label
            self.layout.addWidget(state_label)

        # Add spacing
        self.layout.addSpacing(8)

        # Control buttons
        self._add_control_buttons()

    def _prewarm_widgets(self):
        try:
            # Parent to self so they are cleaned up automatically
            qf = QFontComboBox(self)
            qp = QPlainTextEdit(self)
            qs = QSpinBox(self)
            qb = QPushButton("_")

            # Touch a few properties to force internal initialization
            _ = qf.currentFont()
            _ = qp.placeholderText()
            qs.setRange(0, 10)
            qb.setProperty("class", "prewarm")

            # Schedule deletion
            qf.deleteLater()
            qp.deleteLater()
            qs.deleteLater()
            qb.deleteLater()

            # Also pre-warm property panel UI by simulating a gate and an annotation
            class _DummyGate:
                def __init__(self):
                    self.name = "AND"
                    self.rotation = 0
                    self.num_inputs = 2
                    self.num_outputs = 1
                    self.num_data_inputs = 2
                    self.select_bits = 1

            class _DummyTextAnnotation:
                def __init__(self):
                    self.name = "TEXT"
                    self.rotation = 0
                    self.text = ""
                    self.font_family = "Segoe UI"
                    self.font_size = 14
                    self.font_bold = False
                    self.font_italic = False
                    self.text_color = "#DCDCE1"
                    self.width = 100
                    self.height = 20

            saved_gate = self.target_gate
            saved_annotation = self.target_annotation

            try:
                self.target_gate = _DummyGate()
                self._update_display()
                self._clear_layout()

                self.target_annotation = _DummyTextAnnotation()
                self._update_annotation_display()
                self._clear_layout()

                # Restore empty state
                self.target_gate = None
                self.target_annotation = None
                self._show_component_list()
            finally:
                self.target_gate = saved_gate
                self.target_annotation = saved_annotation

        except Exception as e:
            # Non-fatal; pre-warm should never break normal startup
            print("Warning: prewarm widgets failed:", e)

    def _update_annotation_display(self):
        """Update display for annotation properties"""
        annotation = self.target_annotation
        self.setWindowTitle(f"Properties - {annotation.name}")

        # Store labels that need live updates
        self.live_labels = {}

        # Common properties
        rot_label = QLabel(f"Rotation: {annotation.rotation}°")
        self.layout.addWidget(rot_label)

        # Type-specific properties
        if isinstance(annotation, TextAnnotation):
            self._add_text_annotation_controls(annotation)
        elif isinstance(annotation, RectangleAnnotation):
            self._add_rectangle_annotation_controls(annotation)
        elif isinstance(annotation, CircleAnnotation):
            self._add_circle_annotation_controls(annotation)

        # Add rotation buttons
        self.layout.addSpacing(8)
        self._add_annotation_rotation_buttons()

    def _add_text_annotation_controls(self, annotation):
        """Add controls for text annotation"""
        # Text content
        text_group = QGroupBox("Text Content")
        text_layout = QVBoxLayout()

        text_input = QPlainTextEdit(annotation.text)
        text_input.setPlaceholderText("Enter text...")
        text_input.setMaximumHeight(100)
        # Use simple textChanged signal for QPlainTextEdit
        text_input.textChanged.connect(
            lambda: self._update_text_property(
                annotation, "text", text_input.toPlainText()
            )
        )
        text_layout.addWidget(text_input)

        text_group.setLayout(text_layout)
        self.layout.addWidget(text_group)

        # Font properties
        font_group = QGroupBox("Font")
        font_layout = QVBoxLayout()

        # Font family
        family_layout = QHBoxLayout()
        family_layout.addWidget(QLabel("Family:"))
        family_input = QFontComboBox()
        family_input.setCurrentFont(QFont(annotation.font_family))
        family_input.currentFontChanged.connect(
            lambda f: self._update_text_property(annotation, "font_family", f.family())
        )
        family_layout.addWidget(family_input)
        font_layout.addLayout(family_layout)

        # Font size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Size:"))
        size_spin = QSpinBox()
        size_spin.setRange(6, 72)
        size_spin.setValue(annotation.font_size)
        size_spin.valueChanged.connect(
            lambda v: self._update_text_property(annotation, "font_size", v)
        )
        size_layout.addWidget(size_spin)
        font_layout.addLayout(size_layout)

        # Bold/Italic
        style_layout = QHBoxLayout()
        bold_check = QCheckBox("Bold")
        bold_check.setChecked(annotation.font_bold)
        bold_check.toggled.connect(
            lambda v: self._update_text_property(annotation, "font_bold", v)
        )
        style_layout.addWidget(bold_check)

        italic_check = QCheckBox("Italic")
        italic_check.setChecked(annotation.font_italic)
        italic_check.toggled.connect(
            lambda v: self._update_text_property(annotation, "font_italic", v)
        )
        style_layout.addWidget(italic_check)
        font_layout.addLayout(style_layout)

        font_group.setLayout(font_layout)
        self.layout.addWidget(font_group)

        # Color
        color_group = QGroupBox("Color")
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Text Color:"))

        # Color button
        color_btn = QPushButton(annotation.text_color)
        # Contrast text color for readability
        text_contrast = (
            "black" if QColor(annotation.text_color).lightness() > 128 else "white"
        )
        color_btn.setStyleSheet(
            f"background-color: {annotation.text_color}; color: {text_contrast}; border: 1px solid #555;"
        )
        color_btn.clicked.connect(lambda: self._pick_color(annotation, "text_color"))

        color_layout.addWidget(color_btn)
        color_group.setLayout(color_layout)
        self.layout.addWidget(color_group)

        # Size
        size_group = QGroupBox("Size")
        size_grp_layout = QVBoxLayout()

        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Width:"))
        width_spin = QSpinBox()
        width_spin.setRange(20, 500)
        width_spin.setValue(int(annotation.width))
        width_spin.valueChanged.connect(
            lambda v: self._update_text_property(annotation, "width", v)
        )
        width_layout.addWidget(width_spin)
        size_grp_layout.addLayout(width_layout)

        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("Height:"))
        height_spin = QSpinBox()
        height_spin.setRange(20, 500)
        height_spin.setValue(int(annotation.height))
        height_spin.valueChanged.connect(
            lambda v: self._update_text_property(annotation, "height", v)
        )
        height_layout.addWidget(height_spin)
        size_grp_layout.addLayout(height_layout)

        size_group.setLayout(size_grp_layout)
        self.layout.addWidget(size_group)

    def _add_rectangle_annotation_controls(self, annotation):
        """Add controls for rectangle annotation"""
        # Size
        size_group = QGroupBox("Size")
        size_layout = QVBoxLayout()

        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Width:"))
        width_spin = QSpinBox()
        width_spin.setRange(20, 1000)
        width_spin.setValue(int(annotation.width))
        width_spin.valueChanged.connect(
            lambda v: self._update_annotation_property(annotation, "width", v)
        )
        width_layout.addWidget(width_spin)
        size_layout.addLayout(width_layout)

        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("Height:"))
        height_spin = QSpinBox()
        height_spin.setRange(20, 1000)
        height_spin.setValue(int(annotation.height))
        height_spin.valueChanged.connect(
            lambda v: self._update_annotation_property(annotation, "height", v)
        )
        height_layout.addWidget(height_spin)
        size_layout.addLayout(height_layout)

        size_group.setLayout(size_layout)
        self.layout.addWidget(size_group)

        # Border
        border_group = QGroupBox("Border")
        border_layout = QVBoxLayout()

        border_width_layout = QHBoxLayout()
        border_width_layout.addWidget(QLabel("Width:"))
        border_spin = QSpinBox()
        border_spin.setRange(1, 20)
        border_spin.setValue(int(annotation.border_width))
        border_spin.valueChanged.connect(
            lambda v: self._update_annotation_property(annotation, "border_width", v)
        )
        border_width_layout.addWidget(border_spin)
        border_layout.addLayout(border_width_layout)

        border_color_layout = QHBoxLayout()
        border_color_layout.addWidget(QLabel("Color:"))

        # Color button
        color_btn = QPushButton(annotation.border_color)
        text_contrast = (
            "black" if QColor(annotation.border_color).lightness() > 128 else "white"
        )
        color_btn.setStyleSheet(
            f"background-color: {annotation.border_color}; color: {text_contrast}; border: 1px solid #555;"
        )
        color_btn.clicked.connect(lambda: self._pick_color(annotation, "border_color"))

        border_color_layout.addWidget(color_btn)
        border_layout.addLayout(border_color_layout)

        border_radius_layout = QHBoxLayout()
        border_radius_layout.addWidget(QLabel("Radius:"))
        radius_spin = QSpinBox()
        radius_spin.setRange(0, 100)
        radius_spin.setValue(int(getattr(annotation, "border_radius", 0)))
        radius_spin.valueChanged.connect(
            lambda v: self._update_annotation_property(annotation, "border_radius", v)
        )
        border_radius_layout.addWidget(radius_spin)
        border_layout.addLayout(border_radius_layout)

        border_group.setLayout(border_layout)
        self.layout.addWidget(border_group)

    def _add_circle_annotation_controls(self, annotation):
        """Add controls for circle annotation"""
        # Size
        size_group = QGroupBox("Size")
        size_layout = QVBoxLayout()

        diameter_layout = QHBoxLayout()
        diameter_layout.addWidget(QLabel("Diameter:"))
        diameter_spin = QSpinBox()
        diameter_spin.setRange(20, 1000)
        diameter_spin.setValue(int(annotation.diameter))
        diameter_spin.valueChanged.connect(
            lambda v: self._update_circle_diameter(annotation, v)
        )
        diameter_layout.addWidget(diameter_spin)
        size_layout.addLayout(diameter_layout)

        size_group.setLayout(size_layout)
        self.layout.addWidget(size_group)

        # Border
        border_group = QGroupBox("Border")
        border_layout = QVBoxLayout()

        border_width_layout = QHBoxLayout()
        border_width_layout.addWidget(QLabel("Width:"))
        border_spin = QSpinBox()
        border_spin.setRange(1, 20)
        border_spin.setValue(int(annotation.border_width))
        border_spin.valueChanged.connect(
            lambda v: self._update_annotation_property(annotation, "border_width", v)
        )
        border_width_layout.addWidget(border_spin)
        border_layout.addLayout(border_width_layout)

        border_color_layout = QHBoxLayout()
        border_color_layout.addWidget(QLabel("Color:"))

        # Color button
        color_btn = QPushButton(annotation.border_color)
        text_contrast = (
            "black" if QColor(annotation.border_color).lightness() > 128 else "white"
        )
        color_btn.setStyleSheet(
            f"background-color: {annotation.border_color}; color: {text_contrast}; border: 1px solid #555;"
        )
        color_btn.clicked.connect(lambda: self._pick_color(annotation, "border_color"))

        border_color_layout.addWidget(color_btn)
        border_layout.addLayout(border_color_layout)

        border_group.setLayout(border_layout)
        self.layout.addWidget(border_group)

    def _update_text_property(self, annotation, prop, value):
        """Update a text annotation property and refresh canvas"""
        setattr(annotation, prop, value)
        self._notify_annotation_change(annotation)

    def _pick_color(self, annotation, prop):
        """Open color picker dialog"""
        current = getattr(annotation, prop)
        color = QColorDialog.getColor(QColor(current), self, "Select Color")
        if color.isValid():
            self._update_annotation_property(annotation, prop, color.name())
            # Force refresh to update button color
            self._update_display()

    def _update_annotation_property(self, annotation, prop, value):
        """Update an annotation property and refresh canvas"""
        setattr(annotation, prop, value)
        self._notify_annotation_change(annotation)

    def _update_circle_diameter(self, annotation, value):
        """Update circle diameter (also updates width/height)"""
        annotation.diameter = value
        self._notify_annotation_change(annotation)

    def _notify_annotation_change(self, annotation):
        """Notify that an annotation has changed"""
        # Find the annotation item and update it
        if self.parent():
            canvas = self.parent().canvas
            if annotation in canvas.annotation_items:
                item = canvas.annotation_items[annotation]
                item.prepareGeometryChange()
                item.update()
            # Mark as unsaved
            self.parent().unsaved_changes = True
            self.parent().update_window_title()
            if hasattr(canvas, "schedule_save_state"):
                canvas.schedule_save_state()

    def _add_annotation_rotation_buttons(self):
        """Add rotation buttons for annotations"""
        rot_group = QGroupBox("Rotation")
        rot_layout = QHBoxLayout()

        btn_ccw = QPushButton("⟲ CCW")
        btn_ccw.clicked.connect(lambda: self._rotate_annotation(90))
        rot_layout.addWidget(btn_ccw)

        btn_cw = QPushButton("CW ⟳")
        btn_cw.clicked.connect(lambda: self._rotate_annotation(-90))
        rot_layout.addWidget(btn_cw)

        rot_group.setLayout(rot_layout)
        self.layout.addWidget(rot_group)

    def _rotate_annotation(self, angle):
        """Rotate the current annotation"""
        if not self.target_annotation:
            return

        annotation = self.target_annotation
        annotation.rotation = (annotation.rotation + angle) % 360

        # Update canvas item
        if self.parent():
            canvas = self.parent().canvas
            if annotation in canvas.annotation_items:
                item = canvas.annotation_items[annotation]
                item.setRotation(-annotation.rotation)
                item.update()

            # Mark as unsaved and save state
            self.parent().unsaved_changes = True
            self.parent().save_state()
            self.parent().update_window_title()

        # Refresh display to show new rotation value
        self._update_display()

    def _add_control_buttons(self):
        """Add control buttons based on gate type"""
        if not self.target_gate:
            return

        # Rotation buttons (all components)
        rot_group = QGroupBox("Rotation")
        rot_layout = QHBoxLayout()

        btn_ccw = QPushButton("⟲ CCW")
        btn_ccw.clicked.connect(lambda: self.actionTriggered.emit("rotate_ccw"))
        rot_layout.addWidget(btn_ccw)

        btn_cw = QPushButton("CW ⟳")
        btn_cw.clicked.connect(lambda: self.actionTriggered.emit("rotate_cw"))
        rot_layout.addWidget(btn_cw)

        rot_group.setLayout(rot_layout)
        self.layout.addWidget(rot_group)

        # Gate-specific controls
        if self.target_gate.name in ["AND", "OR", "NAND", "NOR", "XOR", "XNOR"]:
            self._add_size_control(
                "Inputs", "add_input", "remove_input", "+ Add", "− Remove"
            )

        elif self.target_gate.name in ["MUX", "DEMUX", "ENCODER", "DECODER"]:
            name = self.target_gate.name
            title = {
                "MUX": "MUX Size",
                "DEMUX": "DEMUX Size",
                "ENCODER": "Encoder Size",
                "DECODER": "Decoder Size",
            }[name]
            prefix = name.lower()
            self._add_size_control(title, f"{prefix}_add", f"{prefix}_remove")

    def _add_size_control(
        self,
        title,
        add_action,
        remove_action,
        add_text="+ Increase",
        remove_text="− Decrease",
    ):
        """Add a size control group with add/remove buttons"""
        group = QGroupBox(title)
        layout = QHBoxLayout()

        btn_add = QPushButton(add_text)
        btn_add.setProperty("class", "success")
        btn_add.clicked.connect(lambda: self.actionTriggered.emit(add_action))
        layout.addWidget(btn_add)

        btn_remove = QPushButton(remove_text)
        btn_remove.setProperty("class", "danger")
        btn_remove.clicked.connect(lambda: self.actionTriggered.emit(remove_action))
        layout.addWidget(btn_remove)

        group.setLayout(layout)
        self.layout.addWidget(group)

    def update_live_values(self):
        """Update live values in property panel"""
        if not self.target_gate:
            return

        # Update INPUT state
        if "input_state" in self.live_labels:
            state = "ON" if self.target_gate.state else "OFF"
            color = "#4ade80" if self.target_gate.state else "#64748b"
            self.live_labels["input_state"].setText(
                f"State: <span style='color:{color};font-weight:bold'>{state}</span>"
            )

        # Update LED state
        if "led_state" in self.live_labels:
            value = self.target_gate.eval()
            state = "ON" if value else "OFF"
            color = "#ef4444" if value else "#64748b"
            self.live_labels["led_state"].setText(
                f"State: <span style='color:{color};font-weight:bold'>{state}</span>"
            )

    def refresh_component_list(self):
        """Refresh the component list if it's currently displayed"""
        if not self.target_gate and not self.target_annotation:
            self._show_component_list()

    def _show_component_list(self):
        """Show list of all components when nothing is selected"""
        self._clear_layout()

        total_count = len(self.gates_list) + len(self.annotations_list)
        title = QLabel(f"Components: {total_count}")
        title.setProperty("class", "title")
        self.layout.addWidget(title)

        # List of gates
        if self.gates_list:
            gates_label = QLabel("Gates:")
            gates_label.setProperty("class", "dim")
            self.layout.addWidget(gates_label)

            for i, gate in enumerate(self.gates_list):
                btn = QPushButton(f"{i+1}. {gate.name}")
                btn.clicked.connect(
                    lambda checked, g=gate: self.actionTriggered.emit(
                        f"select_gate_{id(g)}"
                    )
                )
                self.layout.addWidget(btn)

        # List of annotations
        if self.annotations_list:
            annotations_label = QLabel("Annotations:")
            annotations_label.setProperty("class", "dim")
            self.layout.addWidget(annotations_label)

            for i, annotation in enumerate(self.annotations_list):
                btn = QPushButton(f"{i+1}. {annotation.name}")
                btn.clicked.connect(
                    lambda checked, a=annotation: self.actionTriggered.emit(
                        f"select_annotation_{id(a)}"
                    )
                )
                self.layout.addWidget(btn)


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


class HelpDialog(QDialog):
    """Custom help dialog with scrollable content"""

    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(600, 500)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Title
        title_label = QLabel(title)
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)

        # Content content
        browser = QTextBrowser()
        browser.setHtml(content)
        browser.setOpenExternalLinks(True)
        # Style the browser to match theme
        browser.setStyleSheet(
            """
            QTextBrowser {
                background-color: #28292E;
                color: #DCDCE1;
                border: 2px solid #3C3E44;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
            }
        """
        )
        layout.addWidget(browser)

        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setProperty("class", "success")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)
        self.setLayout(layout)
