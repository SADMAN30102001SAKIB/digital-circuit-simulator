import logging
from pathlib import Path

from PySide6.QtCore import QSettings, QStandardPaths, Qt, QTimer, Slot
from PySide6.QtWidgets import QDialog, QMainWindow, QMessageBox

from assets.help_text import ABOUT_TEXT, HELP_TEXT

# Import classes needed for COMPONENTS and type checks
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
from ui.components.globalsettingsdialog import GlobalSettingsDialog
from ui.components.helpdialog import HelpDialog
from ui.components.propertypanel import PropertyPanel
from ui.components.settingsdialog import SettingsDialog
from ui.components.truthtabledialog import TruthTableDialog

from .persistence import (
    get_save_state,
    load_circuit,
    load_from_state,
    load_global_settings,
    save_circuit,
    save_global_settings,
)
from .setup import setup_menu, setup_statusbar, setup_toolbar
from .truthtable import collect_influencing_inputs


class CircuitSimulator(QMainWindow):
    """Main Qt application window (slimmed)"""

    # Component definitions (kept here for ComponentLibrary construction)
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

    DEFAULT_CANVAS_SIZE = 10000
    DEFAULT_GRID_SIZE = 20
    DEFAULT_FPS = 60
    DEFAULT_HISTORY_LIMIT = 50

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Circuit Playground Pro")
        self.resize(1400, 800)
        # Setup Directories in User Documents with robust fallback
        docs = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        if docs:
            self.SAVE_DIR = Path(docs) / "CircuitPlaygroundPro"
        else:
            self.SAVE_DIR = Path("save_files")

        try:
            self.SAVE_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # Fallback if Documents folder is restricted or malformed
            logging.warning(
                f"Could not use Documents folder ({e}). Falling back to local 'save_files'."
            )
            self.SAVE_DIR = Path("save_files")
            self.SAVE_DIR.mkdir(parents=True, exist_ok=True)

        self.SETTINGS_FILE = self.SAVE_DIR / "settings.yaml"
        self.CIRCUITS_DIR = self.SAVE_DIR / "circuits"

        # Ensure circuits directory exists
        self.CIRCUITS_DIR.mkdir(parents=True, exist_ok=True)

        # Circuit state
        self.gates = []
        self.annotations = []
        self.selected_gate = None
        self.selected_annotation = None
        self.current_file = None
        self.unsaved_changes = False

        # Settings
        self.canvas_size = self.DEFAULT_CANVAS_SIZE
        self.grid_size = self.DEFAULT_GRID_SIZE
        self.sim_fps = self.DEFAULT_FPS
        self.max_history = self.DEFAULT_HISTORY_LIMIT

        # Load global settings
        load_global_settings(self)

        # Undo/redo
        self.history = []
        self.history_index = -1
        self.saved_history_index = -1

        # Setup UI
        self._setup_ui()
        setup_toolbar(self)
        setup_menu(self)
        setup_statusbar(self)

        # Simulation timer
        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self.update_simulation)
        self.sim_timer.start(1000 // self.sim_fps)

        # Apply settings
        self._apply_settings()

        # Initial state
        self.save_state()
        self.update_window_title()

        # Restore window state
        self.read_settings()

    def read_settings(self):
        """Restore window geometry and state from QSettings"""
        settings = QSettings()
        geom = settings.value("geometry")
        if geom:
            self.restoreGeometry(geom)
        state = settings.value("windowState")
        if state:
            self.restoreState(state)

    def write_settings(self):
        """Save window geometry and state to QSettings"""
        settings = QSettings()
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

    def _setup_ui(self):
        self.canvas = CircuitCanvas(self)
        self.setCentralWidget(self.canvas)
        self.canvas.scene.selectionChanged.connect(self._on_selection_changed)

        self.component_library = ComponentLibrary(self.COMPONENTS, self)
        self.component_library.setObjectName("ComponentLibrary")
        self.addDockWidget(Qt.LeftDockWidgetArea, self.component_library)
        self.component_library.componentSelected.connect(self._on_component_selected)

        self.property_panel = PropertyPanel(self)
        self.property_panel.setObjectName("PropertyPanel")
        self.addDockWidget(Qt.RightDockWidgetArea, self.property_panel)
        self.property_panel.actionTriggered.connect(self._on_property_action)

    # The rest of the methods are intentionally thin wrappers or delegates

    def load_global_settings(self):
        load_global_settings(self)

    def save_global_settings(self):
        save_global_settings(self)

    def save_circuit(self):
        save_circuit(self)

    def load_circuit(self):
        load_circuit(self)

    def get_save_state(self):
        return get_save_state(self)

    def load_from_state(self, state, apply_settings=True):
        return load_from_state(self, state, apply_settings=apply_settings)

    def _show_help(self):
        dialog = HelpDialog("How to Use", HELP_TEXT, self)
        dialog.exec()

    def _show_about(self):
        QMessageBox.about(self, "About Circuit Playground Pro", ABOUT_TEXT)

    def update_window_title(self):
        if self.current_file:
            title = f"Circuit Playground Pro - {self.current_file.stem}"
        else:
            title = "Circuit Playground Pro"
        if self.unsaved_changes:
            title += " *"
        self.setWindowTitle(title)

    def _setup_statusbar(self):
        setup_statusbar(self)

    def _toggle_grid(self):
        self.canvas.show_grid = not self.canvas.show_grid
        self.canvas.viewport().update()

    def _toggle_component_library(self):
        center = self.canvas.mapToScene(self.canvas.viewport().rect().center())
        self.component_library.setVisible(not self.component_library.isVisible())
        QTimer.singleShot(0, lambda: self.canvas.centerOn(center))

    def _toggle_properties(self):
        center = self.canvas.mapToScene(self.canvas.viewport().rect().center())
        self.property_panel.setVisible(not self.property_panel.isVisible())
        QTimer.singleShot(0, lambda: self.canvas.centerOn(center))

    def _show_settings(self):
        dialog = SettingsDialog(
            canvas_size=self.canvas_size,
            grid_size=self.grid_size,
            sim_fps=self.sim_fps,
            parent=self,
        )
        if dialog.exec() == QDialog.Accepted:
            new_canvas_size, new_grid_size, new_fps = dialog.get_values()
            settings_changed = (
                new_canvas_size != self.canvas_size
                or new_grid_size != self.grid_size
                or new_fps != self.sim_fps
            )
            if settings_changed:
                self.canvas_size = new_canvas_size
                self.grid_size = new_grid_size
                self.sim_fps = new_fps
                self._apply_settings()
                self.unsaved_changes = True
                self.save_state()
                self.update_window_title()
                self.statusbar.showMessage("Settings applied")

    def _show_global_settings(self):
        dialog = GlobalSettingsDialog(
            history_limit=self.max_history,
            parent=self,
        )
        if dialog.exec() == QDialog.Accepted:
            new_history = dialog.get_values()
            if new_history != self.max_history:
                self.max_history = new_history
                save_global_settings(self)
                self.statusbar.showMessage("Global Settings applied")

    def _apply_settings(self):
        half = self.canvas_size // 2
        self.canvas.scene.setSceneRect(-half, -half, self.canvas_size, self.canvas_size)
        self.canvas.grid_size = self.grid_size
        self.canvas.viewport().update()
        self.sim_timer.setInterval(1000 // self.sim_fps)

    @Slot(object, str)
    def _on_component_selected(self, component_class, name):
        component = component_class(0, 0)

        # Assign default label to new inputs
        if component.name == "INPUT" and not getattr(component, "label", None):
            component.label = self._generate_default_input_label()
        if isinstance(
            component, (TextAnnotation, RectangleAnnotation, CircleAnnotation)
        ):
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
        selected_items = self.canvas.scene.selectedItems()
        if selected_items:
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
        if action.startswith("select_gate_"):
            gate_id = int(action.replace("select_gate_", ""))
            for gate in self.gates:
                if id(gate) == gate_id:
                    self.selected_gate = gate
                    self.selected_annotation = None
                    self.property_panel.set_target(gate)
                    self.canvas.scene.clearSelection()
                    if gate in self.canvas.gate_items:
                        gate_item = self.canvas.gate_items[gate]
                        gate_item.setSelected(True)
                    break
            return
        if action.startswith("select_annotation_"):
            annotation_id = int(action.replace("select_annotation_", ""))
            for annotation in self.annotations:
                if id(annotation) == annotation_id:
                    self.selected_annotation = annotation
                    self.selected_gate = None
                    self.property_panel.set_target(annotation)
                    self.canvas.scene.clearSelection()
                    if annotation in self.canvas.annotation_items:
                        annotation_item = self.canvas.annotation_items[annotation]
                        annotation_item.setSelected(True)
                    break
            return
        if not self.selected_gate:
            return
        if action == "rotate_cw":
            self.rotate_selected(90)
        elif action == "rotate_ccw":
            self.rotate_selected(-90)
        elif action == "add_input":
            self.modify_gate_inputs(self.selected_gate, 1)
        elif action == "remove_input":
            self.modify_gate_inputs(self.selected_gate, -1)
        elif action == "mux_add":
            self.modify_mux(self.selected_gate, 1)
        elif action == "mux_remove":
            self.modify_mux(self.selected_gate, -1)
        elif action == "demux_add":
            self.modify_demux(self.selected_gate, 1)
        elif action == "demux_remove":
            self.modify_demux(self.selected_gate, -1)
        elif action == "encoder_add":
            self.modify_encoder(self.selected_gate, 1)
        elif action == "encoder_remove":
            self.modify_encoder(self.selected_gate, -1)
        elif action == "decoder_add":
            self.modify_decoder(self.selected_gate, 1)
        elif action == "decoder_remove":
            self.modify_decoder(self.selected_gate, -1)
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

    def _generate_default_input_label(self):
        """Find the next available INx label for a new input switch"""
        existing_nums = set()
        for g in self.gates:
            label = getattr(g, "label", None)
            if g.name == "INPUT" and label and label.startswith("IN"):
                try:
                    num = int(label[2:])
                    existing_nums.add(num)
                except ValueError:
                    pass

        # Find the smallest positive integer not in use
        num = 1
        while num in existing_nums:
            num += 1
        return f"IN{num}"

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

    def save_state(self):
        """Save current state for undo/redo"""
        state = self.get_save_state()

        # If we are branching (making a change while index is not at the end),
        # any "future" saved state is now lost.
        if self.saved_history_index > self.history_index:
            self.saved_history_index = -1

        # Remove future states
        self.history = self.history[: self.history_index + 1]

        # Add new state
        self.history.append(state)
        if len(self.history) > self.max_history:
            self.history.pop(0)
            # Since the list shifted, we must decrement the saved index.
            # If it was 0, it becomes -1 (saved state is no longer in history).
            if self.saved_history_index != -1:
                self.saved_history_index -= 1
        else:
            # history_index only increases if we didn't pop from the front
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
        for g in self.gates:
            if pin in getattr(g, "outputs", []):
                return g
        return None

    def _generate_truth_table_for_selected_led(self):
        if not self.selected_gate or self.selected_gate.name != "LED":
            QMessageBox.warning(
                self, "Truth Table", "Select an LED to generate its truth table."
            )
            return
        led = self.selected_gate

        # Collect inputs first and ask for confirmation on large tables
        inputs = collect_influencing_inputs(self._find_source_gate_for_pin, led)
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

        # Snapshot state to restore later (must be taken BEFORE generation)
        snapshot = self.get_save_state()

        # Suspend property panel updates and pause simulation so the model can
        # compute on the live gate objects without visual flicker.
        panel_suspended = False
        sim_was_running = False
        if hasattr(self, "property_panel"):
            self.property_panel.suspend_updates()
            panel_suspended = True
        try:
            # If the timer was running, stop it and remember to restart later
            sim_was_running = bool(self.sim_timer.isActive())
            if sim_was_running:
                self.sim_timer.stop()
        except Exception:
            sim_was_running = False

        # Build a virtual model (will compute rows on demand)
        from ui.components.truthtablemodel import VirtualTruthTableModel

        model = VirtualTruthTableModel(
            self.gates, self._find_source_gate_for_pin, led, inputs=inputs
        )

        input_names = [g.label or f"IN{i + 1}" for i, g in enumerate(inputs)]
        output_name = led.label or "LED"

        try:
            dialog = TruthTableDialog(
                input_names, output_name, model=model, parent=self
            )
            dialog.exec()
        finally:
            # Restore original snapshot and UI state
            self.restore_state(snapshot)
            self.property_panel.gates_list = self.gates
            if panel_suspended:
                self.property_panel.resume_updates()
            if sim_was_running:
                try:
                    self.sim_timer.start(1000 // self.sim_fps)
                except Exception:
                    pass

            # Find matched gate in restored state
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

        # Restore selected gate and properties
        if matched:
            self.selected_gate = matched
            self.selected_annotation = None
            self.property_panel.set_target(matched)
            self.canvas.scene.clearSelection()
            if matched in self.canvas.gate_items:
                self.canvas.gate_items[matched].setSelected(True)
        else:
            self.selected_gate = None
            self.property_panel.refresh_component_list()

    def closeEvent(self, event):
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

        # Save window state before exiting
        self.write_settings()
        event.accept()
