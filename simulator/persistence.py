import logging

import yaml
from PySide6.QtWidgets import QMessageBox

from core import calculate_rotated_pin_positions

from .utils import ANNOTATION_CLASS_MAP, CLASS_MAP, ensure_uids_for_all


def load_global_settings(sim):
    """Load global settings into simulator instance."""
    if not sim.SETTINGS_FILE.exists():
        return
    try:
        with open(sim.SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = yaml.safe_load(f) or {}
            sim.max_history = settings.get("history_limit", sim.DEFAULT_HISTORY_LIMIT)
    except Exception as e:
        logging.warning(f"Error loading settings: {e}")


def save_global_settings(sim):
    settings = {"history_limit": sim.max_history}
    try:
        with open(sim.SETTINGS_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(settings, f, sort_keys=False)
    except Exception as e:
        logging.error(f"Error saving settings: {e}")


def get_save_state(sim):
    """Return serialisable save-state dict for simulator instance."""
    # ensure stable uids
    ensure_uids_for_all(sim.gates, sim.annotations)

    gates_data = []
    for gate in sim.gates:
        gate_dict = {
            "class": gate.__class__.__name__,
            "uid": getattr(gate, "uid", None),
            "x": gate.x,
            "y": gate.y,
            "rotation": gate.rotation,
            "num_inputs": gate.num_inputs if hasattr(gate, "num_inputs") else None,
            "num_outputs": gate.num_outputs if hasattr(gate, "num_outputs") else None,
            "select_bits": gate.select_bits if hasattr(gate, "select_bits") else None,
            "state": gate.state if hasattr(gate, "state") else None,
            "label": getattr(gate, "label", None),
        }
        gates_data.append(gate_dict)

    # annotations
    annotations_data = []
    for annotation in sim.annotations:
        annotation_dict = {
            "class": annotation.__class__.__name__,
            "uid": getattr(annotation, "uid", None),
            "x": annotation.x,
            "y": annotation.y,
            "rotation": annotation.rotation,
            "width": annotation.width,
            "height": annotation.height,
        }
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

    # connections
    connections = []
    for i, gate in enumerate(sim.gates):
        for j, pin in enumerate(gate.inputs):
            if pin.connected_to:
                for k, other_gate in enumerate(sim.gates):
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
            "canvas_size": sim.canvas_size,
            "grid_size": sim.grid_size,
            "sim_fps": sim.sim_fps,
        },
    }


def load_from_state(sim, state, apply_settings=True):
    """Load simulator state from dict with graceful defaults."""
    if apply_settings and "settings" in state:
        settings = state.get("settings", {})
        sim.canvas_size = settings.get("canvas_size", sim.DEFAULT_CANVAS_SIZE)
        sim.grid_size = settings.get("grid_size", sim.DEFAULT_GRID_SIZE)
        sim.sim_fps = settings.get("sim_fps", sim.DEFAULT_FPS)
        sim._apply_settings()

    # Clear
    sim.gates.clear()
    sim.annotations.clear()
    sim.canvas.clear_all()

    # Use provided maps
    class_map = CLASS_MAP
    annotation_class_map = ANNOTATION_CLASS_MAP

    # Create gates safely
    for gate_data in state.get("gates", []):
        cls_name = gate_data.get("class")
        if cls_name not in class_map:
            continue
        gate_class = class_map[cls_name]
        num_inputs = gate_data.get("num_inputs")
        select_bits = gate_data.get("select_bits")

        if gate_class in [
            class_map.get("ANDGate"),
            class_map.get("ORGate"),
            class_map.get("NANDGate"),
            class_map.get("NORGate"),
            class_map.get("XORGate"),
            class_map.get("XNORGate"),
        ]:
            gate = gate_class(
                gate_data.get("x", 0), gate_data.get("y", 0), num_inputs or 2
            )
        elif gate_class in [
            class_map.get("Multiplexer"),
            class_map.get("Demultiplexer"),
        ]:
            gate = gate_class(
                gate_data.get("x", 0), gate_data.get("y", 0), select_bits or 1
            )
        elif gate_class == class_map.get("Encoder"):
            gate = gate_class(
                gate_data.get("x", 0), gate_data.get("y", 0), num_inputs or 4
            )
        elif gate_class == class_map.get("Decoder"):
            gate = gate_class(
                gate_data.get("x", 0), gate_data.get("y", 0), num_inputs or 2
            )
        else:
            gate = gate_class(gate_data.get("x", 0), gate_data.get("y", 0))

        # rotation
        rotation_value = gate_data.get("rotation", 0)
        gate.rotation = float(rotation_value) if rotation_value else 0

        # restore uid & label & state
        if gate_data.get("uid"):
            gate.uid = gate_data.get("uid")
        if gate_data.get("label") is not None:
            gate.label = gate_data.get("label")
        if hasattr(gate, "state") and gate_data.get("state") is not None:
            gate.state = gate_data["state"]

        sim.gates.append(gate)
        # calculate pins & add to canvas
        calculate_rotated_pin_positions(gate)
        sim.canvas.add_gate(gate)

    # Annotations
    for annotation_data in state.get("annotations", []):
        ann_cls_name = annotation_data.get("class")
        annotation_class = annotation_class_map.get(ann_cls_name)
        if not annotation_class:
            continue
        annotation = annotation_class(
            annotation_data.get("x", 0), annotation_data.get("y", 0)
        )
        annotation.rotation = annotation_data.get("rotation", 0)
        annotation.width = annotation_data.get("width", getattr(annotation, "width", 0))
        annotation.height = annotation_data.get(
            "height", getattr(annotation, "height", 0)
        )
        if annotation_data.get("uid"):
            annotation.uid = annotation_data.get("uid")

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

        sim.annotations.append(annotation)
        sim.canvas.add_annotation(annotation)

    # connections
    for conn in state.get("connections", []):
        i = conn.get("dest_gate")
        j = conn.get("dest_input")
        k = conn.get("src_gate")
        m = conn.get("src_output")
        waypoints = conn.get("waypoints", None)

        try:
            sim.gates[i].inputs[j].connected_to = sim.gates[k].outputs[m]
            if waypoints:
                sim.gates[i].inputs[j].waypoints = waypoints
        except Exception:
            # skip malformed connection
            continue

    sim.canvas.update_wires()


def save_circuit(sim):
    if not sim.current_file:
        from ui.components.confirmdialog import ConfirmDialog
        from ui.components.inputdialog import InputDialog

        dialog = InputDialog("Save Circuit", "Enter filename", sim)
        if dialog.exec() != 1:
            return
        filename = dialog.get_text()
        if not filename:
            return
        filepath = sim.CIRCUITS_DIR / f"{filename}.yaml"
        if filepath.exists():
            confirm = ConfirmDialog(
                "File Exists",
                f"File '{filename}' already exists. Overwrite?",
                "Overwrite",
                "Cancel",
                sim,
            )
            if confirm.exec() != 1:
                return
        sim.current_file = filepath

    state = get_save_state(sim)
    try:
        with open(sim.current_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(state, f, sort_keys=False)
    except Exception as e:
        QMessageBox.critical(sim, "Save Error", f"Failed to save circuit:\n{e}")
        return

    sim.unsaved_changes = False
    sim.saved_history_index = sim.history_index
    sim.update_window_title()
    sim.statusbar.showMessage(f"Saved to {sim.current_file.stem}")


def load_circuit(sim):
    from ui.components.confirmdialog import ConfirmDialog
    from ui.components.filelistdialog import FileListDialog

    if sim.unsaved_changes:
        dialog = ConfirmDialog(
            "Unsaved Changes",
            "You have unsaved changes. Continue without saving?",
            "Yes",
            "No",
            sim,
        )
        if dialog.exec() != 1:
            return

    if not sim.CIRCUITS_DIR.exists():
        QMessageBox.information(sim, "No Circuits", "No saved circuits found.")
        return

    circuit_files = list(sim.CIRCUITS_DIR.glob("*.yaml"))
    if not circuit_files:
        QMessageBox.information(sim, "No Circuits", "No saved circuits found.")
        return

    dialog = FileListDialog("Load Circuit", circuit_files, sim)
    if dialog.exec() != 1:
        return

    selected_file = dialog.get_selected_file()
    if not selected_file:
        return

    try:
        with open(selected_file, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f) or {}
        load_from_state(sim, state)
        sim.current_file = selected_file
        sim.unsaved_changes = False
        sim.history.clear()
        sim.history_index = -1
        sim.save_state()
        sim.saved_history_index = sim.history_index
        sim.property_panel.gates_list = sim.gates
        sim.property_panel.refresh_component_list()
        sim.update_window_title()
        sim.statusbar.showMessage(f"Loaded {selected_file.stem}")
    except Exception as e:
        QMessageBox.critical(sim, "Load Error", f"Failed to load circuit:\n{str(e)}")
