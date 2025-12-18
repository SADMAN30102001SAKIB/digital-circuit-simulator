from pathlib import Path

import yaml
from PySide6.QtCore import QCoreApplication, Qt, QTimer, Slot
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QStatusBar,
    QToolBar,
)

from core import (
    ANDGate,
    CircleAnnotation,
    Decoder,
    Demultiplexer,
    Encoder,
    InputSwitch,
    Multiplexer,
    NANDGate,
    NORGate,
    NOTGate,
    ORGate,
    OutputLED,
    RectangleAnnotation,
    TextAnnotation,
    XNORGate,
    XORGate,
    calculate_rotated_pin_positions,
)
from ui.canvas import CircuitCanvas
from ui.components.componentlibrary import ComponentLibrary
from ui.components.confirmdialog import ConfirmDialog
from ui.components.filelistdialog import FileListDialog
from ui.components.globalsettingsdialog import GlobalSettingsDialog
from ui.components.helpdialog import HelpDialog
from ui.components.inputdialog import InputDialog
from ui.components.propertypanel import PropertyPanel
from ui.components.settingsdialog import SettingsDialog
from ui.components.truthtabledialog import TruthTableDialog


class CircuitSimulator(QMainWindow):
    """Main Qt application window"""

    # Component definitions
    COMPONENTS = [
        ("AND", ANDGate, "Logic Gates"),
        ("OR", ORGate, None),
        ("NOT", NOTGate, None),
        ("XOR", XORGate, None),
        ("NAND", NANDGate, None),
        ("NOR", NORGate, None),
        ("XNOR", XNORGate, None),
        ("MUX", Multiplexer, "Advanced"),
        ("DEMUX", Demultiplexer, None),
        ("ENCODER", Encoder, None),
        ("DECODER", Decoder, None),
        ("INPUT", InputSwitch, "I/O"),
        ("LED", OutputLED, None),
        ("TEXT", TextAnnotation, "Annotations"),
        ("RECT", RectangleAnnotation, None),
        ("CIRCLE", CircleAnnotation, None),
    ]

    # Annotation classes for type checking
    ANNOTATION_CLASSES = (TextAnnotation, RectangleAnnotation, CircleAnnotation)

    # Settings paths
    SAVE_DIR = Path("save_files")
    SETTINGS_FILE = SAVE_DIR / "settings.yaml"
    CIRCUITS_DIR = SAVE_DIR / "circuits"

    # Default settings
    DEFAULT_CANVAS_SIZE = 10000
    DEFAULT_GRID_SIZE = 20
    DEFAULT_FPS = 60
    DEFAULT_HISTORY_LIMIT = 50

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Circuit Playground Pro")
        self.resize(1400, 800)

        # Ensure directories exist
        self.SAVE_DIR.mkdir(exist_ok=True)
        self.CIRCUITS_DIR.mkdir(exist_ok=True)

        # Circuit state
        self.gates = []
        self.annotations = []  # UI annotations (text, shapes)
        self.selected_gate = None
        self.selected_annotation = None
        self.current_file = None
        self.unsaved_changes = False

        # Settings (will be applied after UI setup)
        self.canvas_size = self.DEFAULT_CANVAS_SIZE
        self.grid_size = self.DEFAULT_GRID_SIZE
        self.sim_fps = self.DEFAULT_FPS
        self.max_history = self.DEFAULT_HISTORY_LIMIT

        # Load global settings
        self.load_global_settings()

        # Undo/redo
        self.history = []
        self.history_index = -1
        self.saved_history_index = -1  # Track which state was saved

        # Setup UI
        self._setup_ui()
        self._setup_toolbar()
        self._setup_menu()
        self._setup_statusbar()

        # Simulation timer
        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self.update_simulation)
        self.sim_timer.start(1000 // self.sim_fps)

        # Apply default settings to canvas
        self._apply_settings()

        # Initial state
        self.save_state()
        self.update_window_title()

    def load_global_settings(self):
        """Load global settings from YAML file"""
        if not self.SETTINGS_FILE.exists():
            return

        try:
            with open(self.SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = yaml.safe_load(f) or {}
                self.max_history = settings.get(
                    "history_limit", self.DEFAULT_HISTORY_LIMIT
                )
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_global_settings(self):
        """Save global settings to YAML file"""
        settings = {"history_limit": self.max_history}
        try:
            with open(self.SETTINGS_FILE, "w", encoding="utf-8") as f:
                yaml.safe_dump(settings, f, sort_keys=False)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def update_window_title(self):
        """Update window title with file name and unsaved indicator"""
        if self.current_file:
            # Use .stem to avoid showing the file extension (e.g., .json)
            title = f"Circuit Playground Pro - {self.current_file.stem}"
        else:
            title = "Circuit Playground Pro"

        if self.unsaved_changes:
            title += " *"

        self.setWindowTitle(title)

    def _setup_ui(self):
        """Setup the main UI"""
        # Central widget - Canvas
        self.canvas = CircuitCanvas(self)
        self.setCentralWidget(self.canvas)

        # Connect canvas signals
        self.canvas.scene.selectionChanged.connect(self._on_selection_changed)

        # Component library (left dock)
        self.component_library = ComponentLibrary(self.COMPONENTS, self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.component_library)
        self.component_library.componentSelected.connect(self._on_component_selected)

        # Property panel (right dock)
        self.property_panel = PropertyPanel(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.property_panel)
        self.property_panel.actionTriggered.connect(self._on_property_action)

    def _setup_toolbar(self):
        """Setup toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # New
        action_new = QAction("New", self)
        action_new.setShortcut(QKeySequence.New)
        action_new.setToolTip("New circuit (Ctrl+N)")
        action_new.triggered.connect(self.new_circuit)
        toolbar.addAction(action_new)

        # Save
        action_save = QAction("Save", self)
        action_save.setShortcut(QKeySequence.Save)
        action_save.setToolTip("Save circuit (Ctrl+S)")
        action_save.triggered.connect(self.save_circuit)
        toolbar.addAction(action_save)

        # Load
        action_load = QAction("Load", self)
        action_load.setShortcut("Ctrl+L")
        action_load.setToolTip("Load circuit (Ctrl+L)")
        action_load.triggered.connect(self.load_circuit)
        toolbar.addAction(action_load)

        toolbar.addSeparator()

        # Undo
        action_undo = QAction("Undo", self)
        action_undo.setShortcut(QKeySequence.Undo)
        action_undo.setToolTip("Undo (Ctrl+Z)")
        action_undo.triggered.connect(self.undo)
        toolbar.addAction(action_undo)

        # Redo
        action_redo = QAction("Redo", self)
        action_redo.setShortcut(QKeySequence.Redo)
        action_redo.setToolTip("Redo (Ctrl+Y)")
        action_redo.triggered.connect(self.redo)
        toolbar.addAction(action_redo)

        toolbar.addSeparator()

        # Reset View
        action_reset = QAction("Reset View", self)
        action_reset.setToolTip("Reset view (R)")
        action_reset.triggered.connect(self.canvas.reset_view)
        toolbar.addAction(action_reset)

        # Delete
        action_delete = QAction("Delete", self)
        action_delete.setShortcut(QKeySequence.Delete)
        action_delete.setToolTip("Delete selected (Del)")
        action_delete.triggered.connect(self.delete_selected)
        toolbar.addAction(action_delete)

    def _setup_menu(self):
        """Setup menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction("&New (Ctrl+N)", self.new_circuit)
        file_menu.addAction("&Save (Ctrl+S)", self.save_circuit)
        file_menu.addAction("&Load (Ctrl+L)", self.load_circuit)
        file_menu.addSeparator()
        file_menu.addAction("E&xit", self.close)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction("&Undo (Ctrl+Z)", self.undo)
        edit_menu.addAction("&Redo (Ctrl+Y)", self.redo)
        edit_menu.addSeparator()
        edit_menu.addAction("&Delete (Del)", self.delete_selected)

        # View menu with shortcuts
        view_menu = menubar.addMenu("&View")

        action_reset = view_menu.addAction("&Reset View", self.canvas.reset_view)
        action_reset.setShortcut("R")

        action_grid = view_menu.addAction("Toggle &Grid", self._toggle_grid)
        action_grid.setShortcut("G")

        view_menu.addSeparator()

        action_components = view_menu.addAction(
            "&Component Library", self._toggle_component_library
        )
        action_components.setShortcut("C")

        action_props = view_menu.addAction("&Properties", self._toggle_properties)
        action_props.setShortcut("P")

        # Settings menu
        settings_menu = menubar.addMenu("&Settings")
        settings_menu.addAction("&Preferences...", self._show_settings)
        settings_menu.addAction("&Global Settings...", self._show_global_settings)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("&How to Use", self._show_help)
        help_menu.addAction("&About", self._show_about)

    def _show_help(self):
        """Show help dialog with all shortcuts and instructions"""
        help_text = """
            <h2>🎮 Controls</h2>

            <h3>Mouse</h3>
            <table>
            <tr><td><b>Left-click drag</b></td><td>Pan the canvas</td></tr>
            <tr><td><b>Scroll wheel</b></td><td>Zoom in/out</td></tr>
            <tr><td><b>Click component</b></td><td>Select it</td></tr>
            <tr><td><b>Drag component</b></td><td>Move it</td></tr>
            <tr><td><b>Double-click INPUT</b></td><td>Toggle ON/OFF</td></tr>
            <tr><td><b>Click output pin</b></td><td>Start wire</td></tr>
            <tr><td><b>Click input pin</b></td><td>Complete wire</td></tr>
            <tr><td><b>Click while wiring</b></td><td>Add waypoint</td></tr>
            <tr><td><b>Right-click input pin</b></td><td>Remove wire</td></tr>
            </table>

            <h3>Keyboard Shortcuts</h3>
            <table>
            <tr><td><b>Ctrl+N</b></td><td>New circuit</td></tr>
            <tr><td><b>Ctrl+S</b></td><td>Save circuit</td></tr>
            <tr><td><b>Ctrl+L</b></td><td>Load circuit</td></tr>
            <tr><td><b>Ctrl+Z</b></td><td>Undo</td></tr>
            <tr><td><b>Ctrl+Y</b></td><td>Redo</td></tr>
            <tr><td><b>Delete</b></td><td>Delete selected</td></tr>
            <tr><td><b>Q</b></td><td>Rotate counter-clockwise</td></tr>
            <tr><td><b>E</b></td><td>Rotate clockwise</td></tr>
            <tr><td><b>R</b></td><td>Reset view</td></tr>
            <tr><td><b>G</b></td><td>Toggle grid</td></tr>
            <tr><td><b>C</b></td><td>Toggle component library</td></tr>
            <tr><td><b>P</b></td><td>Toggle properties panel</td></tr>
            <tr><td><b>Escape</b></td><td>Cancel wire connection</td></tr>
            </table>

            <h3>Building Circuits</h3>
            <ol>
            <li>Click a component in the library to add it</li>
            <li>Drag components to position them</li>
            <li>Click an output pin (right side), then click an input pin (left side) to connect</li>
            <li>Double-click INPUT switches to toggle them</li>
            <li>Watch the LED respond to your logic!</li>
            </ol>

            <h3>Settings</h3>
            <p>Go to <b>Settings > Preferences</b> to configure:</p>
            <ul>
            <li><b>Canvas Size</b>: Adjust workspace dimensions</li>
            <li><b>Grid Size</b>: Change snap-to-grid spacing</li>
            <li><b>Simulation FPS</b>: Control simulation speed</li>
            </ul>

            <p>For application-wide options, open <b>Settings > Global Settings</b>:</p>
            <ul>
            <li><b>Undo/Redo History Limit</b>: Set how many undo/redo steps are kept (10-200). Increasing this lets you go back further but may use more memory; a value like 50-100 is a good balance.</li>
            </ul>
        """
        dialog = HelpDialog("How to Use", help_text, self)
        dialog.exec()

    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Circuit Playground Pro",
            "<h2>Circuit Playground Pro</h2>"
            "<p>A visual logic circuit simulator.</p>"
            "<p>Build and test digital logic circuits with gates like "
            "AND, OR, NOT, XOR, NAND, NOR, XNOR, MUX, DEMUX, Encoder, and Decoder.</p>"
            "<p><b>Version:</b> 2.0.0</p>",
        )

    def _setup_statusbar(self):
        """Setup status bar"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage(
            "Pan: Drag | Wire: Click output→input | Rotate: Q/E | Toggle input: Double-click"
        )

    def _toggle_grid(self):
        """Toggle grid visibility"""
        self.canvas.show_grid = not self.canvas.show_grid
        self.canvas.viewport().update()

    def _toggle_component_library(self):
        """Toggle component library panel"""
        center = self.canvas.mapToScene(self.canvas.viewport().rect().center())
        self.component_library.setVisible(not self.component_library.isVisible())
        # Delay centerOn until after layout completes
        QTimer.singleShot(0, lambda: self.canvas.centerOn(center))

    def _toggle_properties(self):
        """Toggle properties panel"""
        center = self.canvas.mapToScene(self.canvas.viewport().rect().center())
        self.property_panel.setVisible(not self.property_panel.isVisible())
        # Delay centerOn until after layout completes
        QTimer.singleShot(0, lambda: self.canvas.centerOn(center))

    def _show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(
            canvas_size=self.canvas_size,
            grid_size=self.grid_size,
            sim_fps=self.sim_fps,
            parent=self,
        )
        if dialog.exec() == QDialog.Accepted:
            new_canvas_size, new_grid_size, new_fps = dialog.get_values()

            # Check if anything changed
            settings_changed = (
                new_canvas_size != self.canvas_size
                or new_grid_size != self.grid_size
                or new_fps != self.sim_fps
            )

            if settings_changed:
                # Update settings
                self.canvas_size = new_canvas_size
                self.grid_size = new_grid_size
                self.sim_fps = new_fps

                # Apply to UI
                self._apply_settings()

                # Track as change (for undo/redo and unsaved indicator)
                self.unsaved_changes = True
                self.save_state()
                self.update_window_title()
                self.statusbar.showMessage("Settings applied")

    def _show_global_settings(self):
        """Show global settings dialog"""
        dialog = GlobalSettingsDialog(
            history_limit=self.max_history,
            parent=self,
        )
        if dialog.exec() == QDialog.Accepted:
            new_history = dialog.get_values()

            if new_history != self.max_history:
                self.max_history = new_history
                self.save_global_settings()
                self.statusbar.showMessage("Global Settings applied")

    def _apply_settings(self):
        """Apply current settings to UI"""
        # Canvas size
        half = self.canvas_size // 2
        self.canvas.scene.setSceneRect(-half, -half, self.canvas_size, self.canvas_size)

        # Grid size
        self.canvas.grid_size = self.grid_size
        self.canvas.viewport().update()

        # FPS
        self.sim_timer.setInterval(1000 // self.sim_fps)

    @Slot(object, str)
    def _on_component_selected(self, component_class, name):
        """Handle component selection from library - adds component to canvas"""
        component = component_class(0, 0)

        # Check if it's an annotation or a gate
        if isinstance(component, self.ANNOTATION_CLASSES):
            self.annotations.append(component)
            self.canvas.add_annotation(component)
            self.property_panel.annotations_list = self.annotations
        else:
            self.gates.append(component)
            self.canvas.add_gate(component)
            self.property_panel.gates_list = self.gates

        self.unsaved_changes = True
        self.property_panel.refresh_component_list()
        self.save_state()
        self.update_window_title()
        self.statusbar.showMessage(f"{name} added")

    @Slot()
    def _on_selection_changed(self):
        """Handle selection changes in canvas"""
        selected_items = self.canvas.scene.selectedItems()
        if selected_items:
            # Get first selected item (gate or annotation)
            for item in selected_items:
                if hasattr(item, "gate"):
                    self.selected_gate = item.gate
                    self.selected_annotation = None
                    self.property_panel.set_target(self.selected_gate)
                    return
                elif hasattr(item, "annotation"):
                    self.selected_annotation = item.annotation
                    self.selected_gate = None
                    self.property_panel.set_target(self.selected_annotation)
                    return

        self.selected_gate = None
        self.selected_annotation = None
        self.property_panel.set_target(None)

    @Slot(str)
    def _on_property_action(self, action):
        """Handle property panel actions"""
        # Check if it's a gate selection action
        if action.startswith("select_gate_"):
            gate_id = int(action.replace("select_gate_", ""))
            for gate in self.gates:
                if id(gate) == gate_id:
                    self.selected_gate = gate
                    self.selected_annotation = None
                    self.property_panel.set_target(gate)
                    # Select in canvas
                    self.canvas.scene.clearSelection()
                    if gate in self.canvas.gate_items:
                        gate_item = self.canvas.gate_items[gate]
                        gate_item.setSelected(True)
                    break
            return

        # Check if it's an annotation selection action
        if action.startswith("select_annotation_"):
            annotation_id = int(action.replace("select_annotation_", ""))
            for annotation in self.annotations:
                if id(annotation) == annotation_id:
                    self.selected_annotation = annotation
                    self.selected_gate = None
                    self.property_panel.set_target(annotation)
                    # Select in canvas
                    self.canvas.scene.clearSelection()
                    if annotation in self.canvas.annotation_items:
                        annotation_item = self.canvas.annotation_items[annotation]
                        annotation_item.setSelected(True)
                    break
            return

        if not self.selected_gate:
            return

        # Handle rotation
        if action == "rotate_cw":
            self.rotate_selected(90)
        elif action == "rotate_ccw":
            self.rotate_selected(-90)

        # Handle input modification
        elif action == "add_input":
            self.modify_gate_inputs(self.selected_gate, 1)
        elif action == "remove_input":
            self.modify_gate_inputs(self.selected_gate, -1)

        # Handle MUX/DEMUX
        elif action == "mux_add":
            self.modify_mux(self.selected_gate, 1)
        elif action == "mux_remove":
            self.modify_mux(self.selected_gate, -1)
        elif action == "demux_add":
            self.modify_demux(self.selected_gate, 1)
        elif action == "demux_remove":
            self.modify_demux(self.selected_gate, -1)

        # Handle Encoder/Decoder
        elif action == "encoder_add":
            self.modify_encoder(self.selected_gate, 1)
        elif action == "encoder_remove":
            self.modify_encoder(self.selected_gate, -1)
        elif action == "decoder_add":
            self.modify_decoder(self.selected_gate, 1)
        elif action == "decoder_remove":
            self.modify_decoder(self.selected_gate, -1)

        # Truth table generation for LED
        elif action == "generate_truth_table":
            self._generate_truth_table_for_selected_led()

    def rotate_selected(self, angle):
        """Rotate selected gate or annotation"""
        if self.selected_gate:
            self.selected_gate.rotation = (self.selected_gate.rotation + angle) % 360
            self.update_gate_pins_for_rotation(self.selected_gate)

            # Update canvas and gate item rotation
            if self.selected_gate in self.canvas.gate_items:
                gate_item = self.canvas.gate_items[self.selected_gate]
                gate_item.setRotation(-self.selected_gate.rotation)
                gate_item.update()
                self.canvas.update_wires()

            self.property_panel.set_target(self.selected_gate)

        elif self.selected_annotation:
            self.selected_annotation.rotation = (
                self.selected_annotation.rotation + angle
            ) % 360

            # Update canvas item
            if self.selected_annotation in self.canvas.annotation_items:
                item = self.canvas.annotation_items[self.selected_annotation]
                item.setRotation(-self.selected_annotation.rotation)
                item.update()

            self.property_panel.set_target(self.selected_annotation)

        else:
            return

        self.unsaved_changes = True
        self.save_state()
        self.update_window_title()

    def modify_gate_inputs(self, gate, delta):
        """Modify number of inputs for a gate"""
        if gate.name not in ["AND", "OR", "NAND", "NOR", "XOR", "XNOR"]:
            return

        new_inputs = max(2, min(8, gate.num_inputs + delta))
        if new_inputs == gate.num_inputs:
            return

        self._recreate_component(gate, type(gate), new_inputs)

    def modify_mux(self, gate, delta):
        """Modify MUX size"""
        if gate.name != "MUX":
            return

        new_select_bits = max(1, min(3, gate.select_bits + delta))
        if new_select_bits == gate.select_bits:
            return

        self._recreate_component(gate, Multiplexer, new_select_bits)

    def modify_demux(self, gate, delta):
        """Modify DEMUX size"""
        if gate.name != "DEMUX":
            return

        new_select_bits = max(1, min(3, gate.select_bits + delta))
        if new_select_bits == gate.select_bits:
            return

        self._recreate_component(gate, Demultiplexer, new_select_bits)

    def modify_encoder(self, gate, delta):
        """Modify Encoder size"""
        if gate.name != "ENCODER":
            return

        # Encoder sizes should be powers of 2: 2, 4, 8, 16
        current = gate.num_inputs
        sizes = [2, 4, 8, 16]

        try:
            current_index = sizes.index(current)
        except ValueError:
            # If current size not in list, find closest
            current_index = min(
                range(len(sizes)), key=lambda i: abs(sizes[i] - current)
            )

        new_index = max(0, min(len(sizes) - 1, current_index + delta))
        new_inputs = sizes[new_index]

        if new_inputs == gate.num_inputs:
            return

        self._recreate_component(gate, Encoder, new_inputs)

    def modify_decoder(self, gate, delta):
        """Modify Decoder size"""
        if gate.name != "DECODER":
            return

        new_inputs = max(1, min(4, gate.num_inputs + delta))
        if new_inputs == gate.num_inputs:
            return

        self._recreate_component(gate, Decoder, new_inputs)

    def _recreate_component(self, old_gate, gate_class, *args):
        """Helper to recreate a component with new parameters"""
        old_rotation = old_gate.rotation
        x, y = old_gate.x, old_gate.y

        # Create new gate
        new_gate = gate_class(x, y, *args)
        new_gate.rotation = old_rotation

        # Replace in list
        index = self.gates.index(old_gate)
        self.gates[index] = new_gate

        # Update canvas
        self.canvas.remove_gate(old_gate)
        self.canvas.add_gate(new_gate)

        # Update selection
        self.selected_gate = new_gate
        self.property_panel.set_target(new_gate)

        if new_gate in self.canvas.gate_items:
            self.canvas.gate_items[new_gate].setSelected(True)

        self.update_gate_pins_for_rotation(new_gate)
        self.canvas.update_wires()

        self.unsaved_changes = True
        self.save_state()
        self.update_window_title()

    def update_gate_pins_for_rotation(self, gate):
        """Update pin positions after rotation"""
        calculate_rotated_pin_positions(gate)

        # Update visual elements
        if gate in self.canvas.gate_items:
            gate_item = self.canvas.gate_items[gate]
            gate_item.setRotation(-gate.rotation)
            if hasattr(gate_item, "pin_items"):
                for pin_item in gate_item.pin_items:
                    pin_item.update_position()

    def delete_selected(self):
        """Delete selected component (gate or annotation)"""
        # Delete selected annotation
        if self.selected_annotation:
            self.annotations.remove(self.selected_annotation)
            self.canvas.remove_annotation(self.selected_annotation)
            self.selected_annotation = None
            self.property_panel.set_target(None)
            self.property_panel.annotations_list = self.annotations
            self.property_panel.refresh_component_list()
            self.unsaved_changes = True
            self.save_state()
            self.update_window_title()
            return

        # Delete selected gate
        if not self.selected_gate:
            return

        # Remove connections
        for gate in self.gates:
            for input_pin in gate.inputs:
                if (
                    input_pin.connected_to
                    and input_pin.connected_to in self.selected_gate.outputs
                ):
                    input_pin.connected_to = None
                    input_pin.waypoints = []

        # Remove gate
        self.gates.remove(self.selected_gate)
        self.canvas.remove_gate(self.selected_gate)

        self.selected_gate = None
        self.property_panel.set_target(None)
        self.property_panel.gates_list = self.gates
        self.property_panel.refresh_component_list()
        self.canvas.update_wires()

        self.unsaved_changes = True
        self.save_state()
        self.update_window_title()

    def new_circuit(self):
        """Create new circuit"""
        if self.unsaved_changes:
            dialog = ConfirmDialog(
                "Unsaved Changes",
                "You have unsaved changes. Continue without saving?",
                "Yes",
                "No",
                self,
            )
            if dialog.exec() != QDialog.Accepted:
                return

        self.gates.clear()
        self.annotations.clear()
        self.canvas.clear_all()
        self.selected_gate = None
        self.selected_annotation = None
        self.current_file = None
        self.unsaved_changes = False

        # Reset settings to defaults
        self.canvas_size = self.DEFAULT_CANVAS_SIZE
        self.grid_size = self.DEFAULT_GRID_SIZE
        self.sim_fps = self.DEFAULT_FPS
        self._apply_settings()

        self.property_panel.set_target(None)
        self.property_panel.gates_list = self.gates
        self.property_panel.annotations_list = self.annotations
        self.property_panel.refresh_component_list()

        self.history.clear()
        self.history_index = -1
        self.save_state()
        self.saved_history_index = self.history_index  # Mark as saved

        self.update_window_title()
        self.statusbar.showMessage("New circuit created")

    def save_circuit(self):
        """Save circuit to YAML file"""
        if not self.current_file:
            # Ask for filename
            dialog = InputDialog("Save Circuit", "Enter filename", self)
            if dialog.exec() != QDialog.Accepted:
                return

            filename = dialog.get_text()
            if not filename:
                return

            filepath = self.CIRCUITS_DIR / f"{filename}.yaml"

            # Check if exists
            if filepath.exists():
                confirm = ConfirmDialog(
                    "File Exists",
                    f"File '{filename}' already exists. Overwrite?",
                    "Overwrite",
                    "Cancel",
                    self,
                )
                if confirm.exec() != QDialog.Accepted:
                    return

            self.current_file = filepath

        # Save to file
        state = self.get_save_state()
        try:
            with open(self.current_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(state, f, sort_keys=False)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save circuit:\n{e}")
            return

        self.unsaved_changes = False
        self.saved_history_index = self.history_index  # Mark current state as saved
        self.update_window_title()
        self.statusbar.showMessage(f"Saved to {self.current_file.stem}")

    def load_circuit(self):
        """Load circuit from YAML file"""
        if self.unsaved_changes:
            dialog = ConfirmDialog(
                "Unsaved Changes",
                "You have unsaved changes. Continue without saving?",
                "Yes",
                "No",
                self,
            )
            if dialog.exec() != QDialog.Accepted:
                return

        if not self.CIRCUITS_DIR.exists():
            QMessageBox.information(self, "No Circuits", "No saved circuits found.")
            return

        circuit_files = list(self.CIRCUITS_DIR.glob("*.yaml"))
        if not circuit_files:
            QMessageBox.information(self, "No Circuits", "No saved circuits found.")
            return

        # Show file list dialog
        dialog = FileListDialog("Load Circuit", circuit_files, self)
        if dialog.exec() != QDialog.Accepted:
            return

        selected_file = dialog.get_selected_file()
        if not selected_file:
            return

        try:
            with open(selected_file, "r", encoding="utf-8") as f:
                state = yaml.safe_load(f) or {}

            self.load_from_state(state)
            self.current_file = selected_file
            self.unsaved_changes = False

            # Save initial state after loading
            self.history.clear()
            self.history_index = -1
            self.save_state()
            self.saved_history_index = self.history_index  # Mark as saved

            # Update property panel
            self.property_panel.gates_list = self.gates
            self.property_panel.refresh_component_list()

            self.update_window_title()
            self.statusbar.showMessage(f"Loaded {selected_file.stem}")

        except Exception as e:
            QMessageBox.critical(
                self, "Load Error", f"Failed to load circuit:\n{str(e)}"
            )

    def get_save_state(self):
        """Get current state for saving"""
        gates_data = []
        for gate in self.gates:
            gate_dict = {
                "class": gate.__class__.__name__,
                "x": gate.x,
                "y": gate.y,
                "rotation": gate.rotation,
                "num_inputs": gate.num_inputs if hasattr(gate, "num_inputs") else None,
                "num_outputs": (
                    gate.num_outputs if hasattr(gate, "num_outputs") else None
                ),
                "select_bits": (
                    gate.select_bits if hasattr(gate, "select_bits") else None
                ),
                "state": gate.state if hasattr(gate, "state") else None,
                "label": getattr(gate, "label", None),
            }
            gates_data.append(gate_dict)

        # Save annotations
        annotations_data = []
        for annotation in self.annotations:
            annotation_dict = {
                "class": annotation.__class__.__name__,
                "x": annotation.x,
                "y": annotation.y,
                "rotation": annotation.rotation,
                "width": annotation.width,
                "height": annotation.height,
            }
            # Add type-specific properties
            if annotation.name == "TEXT":
                annotation_dict.update(
                    {
                        "text": annotation.text,
                        "font_family": annotation.font_family,
                        "font_size": annotation.font_size,
                        "font_bold": annotation.font_bold,
                        "font_italic": annotation.font_italic,
                        "text_color": annotation.text_color,
                    }
                )
            elif annotation.name == "RECT":
                annotation_dict.update(
                    {
                        "border_width": annotation.border_width,
                        "border_color": annotation.border_color,
                        "border_radius": getattr(annotation, "border_radius", 0),
                    }
                )
            elif annotation.name == "CIRCLE":
                annotation_dict.update(
                    {
                        "diameter": annotation.diameter,
                        "border_width": annotation.border_width,
                        "border_color": annotation.border_color,
                    }
                )
            annotations_data.append(annotation_dict)

        # Save connections
        connections = []
        for i, gate in enumerate(self.gates):
            for j, pin in enumerate(gate.inputs):
                if pin.connected_to:
                    for k, other_gate in enumerate(self.gates):
                        if pin.connected_to in other_gate.outputs:
                            m = other_gate.outputs.index(pin.connected_to)
                            rec = {
                                "dest_gate": i,
                                "dest_input": j,
                                "src_gate": k,
                                "src_output": m,
                            }
                            if pin.waypoints:
                                rec["waypoints"] = pin.waypoints
                            connections.append(rec)
                            break

        return {
            "gates": gates_data,
            "annotations": annotations_data,
            "connections": connections,
            "settings": {
                "canvas_size": self.canvas_size,
                "grid_size": self.grid_size,
                "sim_fps": self.sim_fps,
            },
        }

    def load_from_state(self, state, apply_settings=True):
        """Load circuit from state"""
        # Load settings if present
        if apply_settings and "settings" in state:
            settings = state["settings"]
            self.canvas_size = settings.get("canvas_size", self.DEFAULT_CANVAS_SIZE)
            self.grid_size = settings.get("grid_size", self.DEFAULT_GRID_SIZE)
            self.sim_fps = settings.get("sim_fps", self.DEFAULT_FPS)
            self._apply_settings()

        # Clear current
        self.gates.clear()
        self.annotations.clear()
        self.canvas.clear_all()

        # Class mapping for gates
        class_map = {
            "ANDGate": ANDGate,
            "ORGate": ORGate,
            "NOTGate": NOTGate,
            "XORGate": XORGate,
            "NANDGate": NANDGate,
            "NORGate": NORGate,
            "XNORGate": XNORGate,
            "Multiplexer": Multiplexer,
            "Demultiplexer": Demultiplexer,
            "Encoder": Encoder,
            "Decoder": Decoder,
            "InputSwitch": InputSwitch,
            "OutputLED": OutputLED,
        }

        # Annotation class mapping
        annotation_class_map = {
            "TextAnnotation": TextAnnotation,
            "RectangleAnnotation": RectangleAnnotation,
            "CircleAnnotation": CircleAnnotation,
        }

        # Create gates
        for gate_data in state["gates"]:
            gate_class = class_map[gate_data["class"]]
            num_inputs = gate_data.get("num_inputs")
            select_bits = gate_data.get("select_bits")

            # Create gate with appropriate parameters
            if gate_class in [ANDGate, ORGate, NANDGate, NORGate, XORGate, XNORGate]:
                gate = gate_class(gate_data["x"], gate_data["y"], num_inputs or 2)
            elif gate_class in [Multiplexer, Demultiplexer]:
                gate = gate_class(gate_data["x"], gate_data["y"], select_bits or 1)
            elif gate_class == Encoder:
                gate = gate_class(gate_data["x"], gate_data["y"], num_inputs or 4)
            elif gate_class == Decoder:
                gate = gate_class(gate_data["x"], gate_data["y"], num_inputs or 2)
            else:
                gate = gate_class(gate_data["x"], gate_data["y"])

            # Set rotation BEFORE adding to canvas so GateItem gets correct value
            rotation_value = gate_data.get("rotation", 0)
            gate.rotation = float(rotation_value) if rotation_value else 0

            # Restore label if present
            if gate_data.get("label") is not None:
                gate.label = gate_data.get("label")

            if hasattr(gate, "state") and gate_data.get("state") is not None:
                gate.state = gate_data["state"]

            self.gates.append(gate)

            # Calculate pin positions with rotation BEFORE adding to canvas
            calculate_rotated_pin_positions(gate)

            # Add to canvas (GateItem will read gate.rotation in __init__)
            self.canvas.add_gate(gate)

        # Create annotations
        for annotation_data in state.get("annotations", []):
            annotation_class = annotation_class_map.get(annotation_data["class"])
            if not annotation_class:
                continue

            annotation = annotation_class(annotation_data["x"], annotation_data["y"])

            # Restore common properties
            annotation.rotation = annotation_data.get("rotation", 0)
            annotation.width = annotation_data.get("width", annotation.width)
            annotation.height = annotation_data.get("height", annotation.height)

            # Restore type-specific properties
            if annotation.name == "TEXT":
                annotation.text = annotation_data.get("text", "Text")
                annotation.font_family = annotation_data.get("font_family", "Segoe UI")
                annotation.font_size = annotation_data.get("font_size", 14)
                annotation.font_bold = annotation_data.get("font_bold", False)
                annotation.font_italic = annotation_data.get("font_italic", False)
                annotation.text_color = annotation_data.get("text_color", "#DCDCE1")
            elif annotation.name == "RECT":
                annotation.border_width = annotation_data.get("border_width", 2)
                annotation.border_color = annotation_data.get("border_color", "#5096FF")
                annotation.border_radius = annotation_data.get("border_radius", 0)
            elif annotation.name == "CIRCLE":
                annotation.diameter = annotation_data.get("diameter", 80)
                annotation.border_width = annotation_data.get("border_width", 2)
                annotation.border_color = annotation_data.get("border_color", "#5096FF")

            self.annotations.append(annotation)
            self.canvas.add_annotation(annotation)

        # Restore connections
        for conn in state["connections"]:
            i = conn.get("dest_gate")
            j = conn.get("dest_input")
            k = conn.get("src_gate")
            m = conn.get("src_output")
            waypoints = conn.get("waypoints", None)

            self.gates[i].inputs[j].connected_to = self.gates[k].outputs[m]
            if waypoints:
                self.gates[i].inputs[j].waypoints = waypoints

        self.canvas.update_wires()

    def save_state(self):
        """Save current state for undo/redo"""
        state = self.get_save_state()

        # Remove future states
        self.history = self.history[: self.history_index + 1]

        # Add new state
        self.history.append(state)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        else:
            self.history_index += 1

    def restore_state(self, state):
        """Restore a state without saving (used internally for undo/redo)"""
        self.load_from_state(state, apply_settings=True)

    def undo(self):
        """Undo last action"""
        if self.history_index > 0:
            self.history_index -= 1
            # Temporarily disable save to prevent corrupting history
            self.restore_state(self.history[self.history_index])
            self.property_panel.gates_list = self.gates
            self.property_panel.refresh_component_list()
            # Check if we're back at the saved state
            self.unsaved_changes = self.history_index != self.saved_history_index
            self.update_window_title()
            self.statusbar.showMessage(
                f"Undo ({self.history_index + 1}/{len(self.history)})"
            )

    def redo(self):
        """Redo action"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            # Temporarily disable save to prevent corrupting history
            self.restore_state(self.history[self.history_index])
            self.property_panel.gates_list = self.gates
            self.property_panel.refresh_component_list()
            # Check if we're back at the saved state
            self.unsaved_changes = self.history_index != self.saved_history_index
            self.update_window_title()
            self.statusbar.showMessage(
                f"Redo ({self.history_index + 1}/{len(self.history)})"
            )

    def update_simulation(self):
        """Update circuit simulation"""
        for gate in self.gates:
            gate.update()

        # Update wire colors
        for wire_item in self.canvas.wire_items:
            wire_item.update_path()

        # Update pin colors and gate visuals
        for gate, gate_item in self.canvas.gate_items.items():
            # Update gate item (for LED color changes)
            gate_item.update()

            # Update pin colors
            if hasattr(gate_item, "pin_items"):
                for pin_item in gate_item.pin_items:
                    if hasattr(pin_item, "update_color"):
                        pin_item.update_color()

        # Update property panel live values (for INPUT/LED state display)
        if self.selected_gate:
            self.property_panel.update_live_values()

    def _find_source_gate_for_pin(self, pin):
        """Return the gate that owns the provided output pin, or None"""
        for g in self.gates:
            if pin in getattr(g, "outputs", []):
                return g
        return None

    def _collect_influencing_inputs(self, start_gate):
        """Traverse upstream from start_gate and collect all InputSwitch gates that influence it.

        Returns a list of unique InputSwitch gates in deterministic order.
        """
        inputs = []
        visited = set()
        queue = []

        # Start from the input pins of the start gate
        for pin in getattr(start_gate, "inputs", []):
            src = pin.connected_to
            if not src:
                continue
            src_gate = self._find_source_gate_for_pin(src)
            if src_gate:
                queue.append(src_gate)

        while queue:
            g = queue.pop(0)
            if id(g) in visited:
                continue
            visited.add(id(g))

            # If it's an input switch, collect it
            if isinstance(g, InputSwitch):
                inputs.append(g)
                continue

            # Otherwise, add upstream sources
            for pin in getattr(g, "inputs", []):
                if pin.connected_to:
                    src_gate = self._find_source_gate_for_pin(pin.connected_to)
                    if src_gate and id(src_gate) not in visited:
                        queue.append(src_gate)

        # Deterministic ordering: sort by label (if present) then by id
        inputs.sort(key=lambda x: (x.label or "", id(x)))
        return inputs

    def _generate_truth_table_for_selected_led(self):
        """Generate truth table for currently selected LED and show dialog.

        This runs a combinational evaluation by brute-force enumerating input combinations.
        """
        if not self.selected_gate or self.selected_gate.name != "LED":
            QMessageBox.warning(
                self, "Truth Table", "Select an LED to generate its truth table."
            )
            return

        led = self.selected_gate
        inputs = self._collect_influencing_inputs(led)

        if not inputs:
            QMessageBox.information(
                self, "Truth Table", "No input switches found upstream of this LED."
            )
            return

        n = len(inputs)
        total = 1 << n
        if n > 16:
            resp = QMessageBox.question(
                self,
                "Large Truth Table",
                f"This LED has {n} inputs, which results in {total} rows. Continue?",
            )
            if resp != QMessageBox.Yes:
                return

        # Snapshot state to restore later
        snapshot = self.get_save_state()

        rows = []

        # Progress dialog
        progress = QProgressDialog(
            "Generating truth table...", "Cancel", 0, total, self
        )
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        max_iters = max(10, len(self.gates) * 3)

        # Suspend property panel updates so the LED state doesn't flicker while we iterate inputs
        panel_suspended = False
        if hasattr(self, "property_panel"):
            self.property_panel.suspend_updates()
            panel_suspended = True

        any_non_converging = False
        canceled = False
        try:
            for idx in range(total):
                # Check for user cancel
                if progress.wasCanceled():
                    canceled = True
                    break

                # Set inputs
                for i, g in enumerate(inputs):
                    bit = bool((idx >> i) & 1)
                    if hasattr(g, "state"):
                        g.state = bit
                    if getattr(g, "outputs", []):
                        g.outputs[0].set_value(bit)

                # Stabilize with propagation
                converged = False
                for _ in range(max_iters):
                    # snapshot outputs
                    prev = []
                    for gate in self.gates:
                        for out in getattr(gate, "outputs", []):
                            prev.append(out.wire.value)

                    for gate in self.gates:
                        gate.update()

                    after = []
                    for gate in self.gates:
                        for out in getattr(gate, "outputs", []):
                            after.append(out.wire.value)

                    if prev == after:
                        converged = True
                        break

                if not converged:
                    any_non_converging = True

                # Read LED value
                out_val = (
                    led.eval()
                    if hasattr(led, "eval")
                    else (
                        led.inputs[0].get_value()
                        if getattr(led, "inputs", None)
                        else False
                    )
                )

                bits = [bool((idx >> i) & 1) for i in range(n)]
                rows.append((bits, bool(out_val)))

                progress.setValue(idx + 1)
                QCoreApplication.processEvents()

        finally:
            progress.close()
            # Restore snapshot (property panel already suspended before generation)
            self.restore_state(snapshot)
            self.property_panel.gates_list = self.gates

            # Determine a matching gate in the restored state but do NOT set it yet
            matched = None
            for g in self.gates:
                if (
                    g.__class__ is led.__class__
                    and getattr(g, "label", None) == getattr(led, "label", None)
                    and g.x == led.x
                    and g.y == led.y
                ):
                    matched = g
                    break

        # If user canceled, do not show partial results; re-select after cancel
        if canceled:
            QMessageBox.information(
                self, "Cancelled", "Truth table generation was cancelled."
            )
            # Re-select the matched LED (if any) so property panel displays correctly now
            if matched:
                self.selected_gate = matched
                self.selected_annotation = None
                if panel_suspended:
                    self.property_panel.resume_updates()
                self.property_panel.set_target(matched)
                self.canvas.scene.clearSelection()
                if matched in self.canvas.gate_items:
                    self.canvas.gate_items[matched].setSelected(True)
            else:
                # resume updates then show component list
                if panel_suspended:
                    self.property_panel.resume_updates()
                self.property_panel.refresh_component_list()
            return
        # Warn if any iteration didn't converge
        if any_non_converging:
            QMessageBox.warning(
                self,
                "Non-converging",
                "Circuit did not converge for some input combinations; results may be unreliable for sequential circuits.",
            )

        # Build names
        input_names = [g.label or f"IN{i+1}" for i, g in enumerate(inputs)]
        output_name = led.label or "LED"

        # Show dialog (modal). Only after it closes we resume property panel updates and set the target to avoid rendering glitches
        dialog = TruthTableDialog(input_names, output_name, rows, parent=self)
        dialog.exec()

        # Resume property panel updates and apply pending target (only if we suspended it)
        if panel_suspended:
            self.property_panel.resume_updates()

        # Re-select the matched LED now that the dialog has closed
        if matched:
            self.selected_gate = matched
            self.selected_annotation = None
            self.property_panel.set_target(matched)
            self.canvas.scene.clearSelection()
            if matched in self.canvas.gate_items:
                self.canvas.gate_items[matched].setSelected(True)
        else:
            self.property_panel.refresh_component_list()

        # After dialog closes, re-apply selection to ensure property panel shows only the LED properties
        if self.selected_gate:
            self.property_panel.set_target(self.selected_gate)
        else:
            self.property_panel.refresh_component_list()

    def closeEvent(self, event):
        """Handle window close"""
        if self.unsaved_changes:
            dialog = ConfirmDialog(
                "Unsaved Changes",
                "You have unsaved changes. Exit anyway?",
                "Exit",
                "Cancel",
                self,
            )
            if dialog.exec() != QDialog.Accepted:
                event.ignore()
                return

        event.accept()
