import logging
import platform
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QDockWidget,
    QFontComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.annotations import (
    Annotation,
    CircleAnnotation,
    RectangleAnnotation,
    TextAnnotation,
)


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

        # Update suspension flag and pending target (used to avoid UI updates while modal dialogs are open)
        self._suspend_updates = False
        self._pending_target = None

        # Show empty state
        self._show_component_list()

        # Schedule a short non-blocking pre-warm of commonly-used widgets to
        # avoid first-selection stalls caused by lazy initialization of Qt
        # style/font resources (this runs after the event loop starts).
        QTimer.singleShot(0, self._prewarm_widgets)

    def set_target(self, target):
        """Set the gate or annotation to display properties for

        If updates are suspended (e.g., while a modal dialog is open), record
        the pending target and avoid updating the UI until resumed.
        """
        if self._suspend_updates:
            # store pending target for later
            self._pending_target = target
            return

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
        # If suspended, don't modify the UI now
        if self._suspend_updates:
            return

        self._clear_layout()

        # Handle annotation display
        if self.target_annotation:
            self._update_annotation_display()
            return

        if not self.target_gate:
            self.setWindowTitle("Circuit Components")
            self._show_component_list()
            return

        # Update title based on component type
        if self.target_gate.name in ["INPUT", "LED"]:
            display_name = (
                getattr(self.target_gate, "label", None) or self.target_gate.name
            )
        else:
            display_name = self.target_gate.name

        self.setWindowTitle(f"Properties - {display_name}")

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

        # Label control (for inputs & LEDs)
        if self.target_gate.name in ["INPUT", "LED"]:
            label_group = QGroupBox("Label")
            label_layout = QVBoxLayout()

            label_input = QLineEdit()
            label_input.setPlaceholderText("Optional label (e.g. A, Vcc, OUT1)")
            label_input.setText(self.target_gate.label or "")

            # Update title live while editing (do not save every keystroke)
            label_input.textChanged.connect(
                lambda t, g=self.target_gate: self.setWindowTitle(
                    f"Properties - {t if t.strip() else g.name}"
                )
            )

            # Save on Enter or focus out
            label_input.editingFinished.connect(
                lambda: self._update_gate_property(
                    self.target_gate, "label", label_input.text()
                )
            )

            label_layout.addWidget(label_input)
            label_group.setLayout(label_layout)
            self.layout.addWidget(label_group)

            # Analysis group (only for LED)
            if self.target_gate.name == "LED":
                analysis_group = QGroupBox("Analysis")
                analysis_layout = QHBoxLayout()

                btn_truth = QPushButton("Generate Truth Table")
                btn_truth.setProperty("class", "primary")
                btn_truth.clicked.connect(
                    lambda: self.actionTriggered.emit("generate_truth_table")
                )
                analysis_layout.addWidget(btn_truth)

                analysis_group.setLayout(analysis_layout)
                self.layout.addWidget(analysis_group)

        # Control buttons
        self._add_control_buttons()

        # Add stretch at the end to keep everything pushed to the top
        self.layout.addStretch()

    def _prewarm_widgets(self):
        try:
            # Parent to self so they are cleaned up automatically
            qf = QFontComboBox(self)
            qf.setFontFilters(
                QFontComboBox.ScalableFonts
            )  # Filter out legacy bitmap fonts
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
                # Ensure the window title is the default (prewarm may have changed it)
                self.setWindowTitle("Circuit Components")
            finally:
                self.target_gate = saved_gate
                self.target_annotation = saved_annotation
        except Exception as e:
            # Non-fatal; pre-warm should never break normal startup
            logging.warning(f"Prewarm widgets failed: {e}")

    def suspend_updates(self):
        """Suspend UI updates until resume_updates is called. Useful when showing a modal dialog."""
        self._suspend_updates = True

    def resume_updates(self):
        """Resume UI updates and apply any pending target that was recorded while suspended."""
        self._suspend_updates = False
        # Apply pending target if present
        if self._pending_target is not None:
            pending = self._pending_target
            self._pending_target = None
            self.set_target(pending)

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

        # Add stretch at the end
        self.layout.addStretch()

    def _add_text_annotation_controls(self, annotation):
        """Add controls for text annotation"""
        # Text content
        text_group = QGroupBox("Text Content")
        if platform.system() == "Linux":
            # Surgical fix: Target JUST the gap by forcing the title and padding
            # On Linux Fusion style, the title is displaced; we force it tighter.
            text_group.setStyleSheet("""
                QGroupBox { 
                    margin-top: 2.8ex; 
                    padding-top: 4px; 
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left; 
                    padding: 0 5px;
                }
            """)
            text_layout = QVBoxLayout()
            text_layout.setContentsMargins(8, 0, 8, 8)
            text_layout.setSpacing(0)
        else:
            text_layout = QVBoxLayout()
            text_layout.setContentsMargins(8, 8, 8, 8)  # Windows Perfect

        text_input = QPlainTextEdit(annotation.text)
        text_input.document().setDocumentMargin(
            0
        )  # Remove internal platform-specific margins
        text_input.setPlaceholderText("Enter text...")

        # On Linux, these widgets have a very tall default sizeHint.
        # We force a smaller height to match the Windows 'perfect' density.
        if platform.system() == "Linux":
            text_input.setMinimumHeight(0)
            text_input.setFixedHeight(100)
            text_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        else:
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
        family_input.setFontFilters(
            QFontComboBox.ScalableFonts
        )  # Filter out legacy bitmap fonts
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
        self._add_border_controls(annotation, include_radius=True)

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
        self._add_border_controls(annotation, include_radius=False)

    def _add_border_controls(self, annotation, include_radius=False):
        """Add border controls (width, color, and optional radius)"""
        border_group = QGroupBox("Border")
        border_layout = QVBoxLayout()

        # Width
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

        # Color
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

        # Radius (optional)
        if include_radius:
            border_radius_layout = QHBoxLayout()
            border_radius_layout.addWidget(QLabel("Radius:"))
            radius_spin = QSpinBox()
            radius_spin.setRange(0, 100)
            radius_spin.setValue(int(getattr(annotation, "border_radius", 0)))
            radius_spin.valueChanged.connect(
                lambda v: self._update_annotation_property(
                    annotation, "border_radius", v
                )
            )
            border_radius_layout.addWidget(radius_spin)
            border_layout.addLayout(border_radius_layout)

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

    def _notify_gate_change(self, gate):
        """Notify that a gate (INPUT/LED/etc.) has changed"""
        if self.parent():
            canvas = self.parent().canvas
            if gate in canvas.gate_items:
                item = canvas.gate_items[gate]
                # ensure item updates (e.g., title or visual)
                item.prepareGeometryChange()
                item.update()
            # Mark as unsaved and schedule save
            self.parent().unsaved_changes = True
            self.parent().update_window_title()
            if hasattr(canvas, "schedule_save_state"):
                canvas.schedule_save_state()

    def _update_gate_property(self, gate, prop, value):
        """Update a gate property (label, etc.) and refresh canvas"""
        # Treat empty strings as None for labels
        if isinstance(value, str) and value.strip() == "":
            value = None
        setattr(gate, prop, value)
        # Update the gate item if exists
        if self.parent():
            canvas = self.parent().canvas
            if gate in canvas.gate_items:
                item = canvas.gate_items[gate]
                # If gate label changed, the property panel title should update
                item.update()
        # Notify parent about the change (saves state)
        self._notify_gate_change(gate)
        # If updates are suspended, defer display refresh until resume
        if not self._suspend_updates:
            self._update_display()
        else:
            self._pending_target = gate

    def _add_annotation_rotation_buttons(self):
        """Add rotation buttons for annotations"""
        if self._suspend_updates:
            return

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
        if self._suspend_updates:
            return
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
        if self._suspend_updates:
            return
        if not self.target_gate:
            return

        # Ensure pending target isn't stale (if any)
        if (
            self._pending_target is not None
            and self._pending_target is not self.target_gate
        ):
            self._pending_target = None
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
        # Don't update live values when updates are suspended (e.g., during truth-table generation)
        if self._suspend_updates:
            return

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
        if self._suspend_updates:
            return
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
                # Prefer label for INPUT/LED in the list view
                if gate.name in ["INPUT", "LED"]:
                    display_name = getattr(gate, "label", None) or gate.name
                else:
                    display_name = gate.name

                btn = QPushButton(f"{i + 1}. {display_name}")
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
                btn = QPushButton(f"{i + 1}. {annotation.name}")
                btn.clicked.connect(
                    lambda checked, a=annotation: self.actionTriggered.emit(
                        f"select_annotation_{id(a)}"
                    )
                )
                self.layout.addWidget(btn)
