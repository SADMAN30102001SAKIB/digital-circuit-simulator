from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsScene, QGraphicsView

from core.annotations import CircleAnnotation, RectangleAnnotation, TextAnnotation
from ui.items import (
    AnnotationItem,
    CircleAnnotationItem,
    GateItem,
    PinItem,
    RectangleAnnotationItem,
    TextAnnotationItem,
    WireItem,
)
from ui.theme import ACCENT, CANVAS_BG, GRID_COLOR


class CircuitCanvas(QGraphicsView):
    """Main canvas for drawing and interacting with circuits"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent

        # Scene setup
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-5000, -5000, 10000, 10000)
        self.setScene(self.scene)

        # View settings
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        self.setBackgroundBrush(QBrush(QColor(CANVAS_BG)))

        # Pan/zoom state
        self.panning = False
        self.pan_start = QPointF()
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 3.0

        # Wire connection state
        self.connecting_from = None
        self.temp_wire_line = None
        self.temp_waypoints = []

        # Item tracking
        self.gate_items = {}  # gate -> GateItem
        self.annotation_items = {}  # annotation -> AnnotationItem
        self.wire_items = []  # List of WireItem

        # Grid
        self.show_grid = True
        self.grid_size = 20

        # Debounce timer for saving state
        self.save_state_timer = QTimer()
        self.save_state_timer.setSingleShot(True)
        self.save_state_timer.timeout.connect(self._do_save_state)

    # === Drawing ===

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        if not self.show_grid:
            return

        painter.setPen(QPen(QColor(GRID_COLOR), 1))
        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)

        x = left
        while x < rect.right():
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += self.grid_size

        y = top
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += self.grid_size

    # === Mouse Events ===

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        new_zoom = self.zoom_level * factor
        if self.min_zoom <= new_zoom <= self.max_zoom:
            self.zoom_level = new_zoom
            self.scale(factor, factor)

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        item = self.scene.itemAt(scene_pos, self.transform())

        # Pin click - start/complete wire or remove wire
        if isinstance(item, PinItem):
            if event.button() == Qt.LeftButton:
                self._handle_pin_click(item)
            elif event.button() == Qt.RightButton:
                self._remove_wire_from_pin(item)
            event.accept()
            return

        # Add waypoint while wiring
        if event.button() == Qt.LeftButton and self.connecting_from:
            self.temp_waypoints.append((scene_pos.x(), scene_pos.y()))
            event.accept()
            return

        # Deselect on empty canvas click
        if event.button() == Qt.LeftButton and not isinstance(
            item, (GateItem, PinItem, AnnotationItem)
        ):
            if not self.connecting_from:
                self.scene.clearSelection()
                if self.parent_window:
                    self.parent_window.selected_gate = None
                    self.parent_window.selected_annotation = None
                    self.parent_window.property_panel.set_target(None)

        # Pan with middle-click, Ctrl+click, or empty canvas drag
        if (
            event.button() == Qt.MiddleButton
            or (
                event.button() == Qt.LeftButton
                and event.modifiers() == Qt.ControlModifier
            )
            or (
                event.button() == Qt.LeftButton
                and not isinstance(item, (GateItem, AnnotationItem))
                and not self.connecting_from
            )
        ):
            self.panning = True
            self.pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()

        if not isinstance(item, PinItem):
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.panning:
            delta = event.pos() - self.pan_start
            self.pan_start = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
        elif self.connecting_from:
            self._update_temp_wire(self.mapToScene(event.pos()))
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.panning and event.button() in (Qt.MiddleButton, Qt.LeftButton):
            self.panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if (
            event.key() == Qt.Key_Q
            and self.parent_window
            and (
                self.parent_window.selected_gate
                or self.parent_window.selected_annotation
            )
        ):
            self.parent_window.rotate_selected(90)
            event.accept()
        elif (
            event.key() == Qt.Key_E
            and self.parent_window
            and (
                self.parent_window.selected_gate
                or self.parent_window.selected_annotation
            )
        ):
            self.parent_window.rotate_selected(-90)
            event.accept()
        elif event.key() == Qt.Key_Escape and self.connecting_from:
            self.cancel_wire_connection()
            event.accept()

    # === Gate Management ===

    def add_gate(self, gate):
        gate_item = GateItem(gate)
        self.scene.addItem(gate_item)
        self.gate_items[gate] = gate_item

        gate_item.pin_items = []
        for pin in gate.inputs + gate.outputs:
            pin_item = PinItem(pin, gate_item)
            pin._pin_item = pin_item
            gate_item.pin_items.append(pin_item)

        return gate_item

    def remove_gate(self, gate):
        if gate in self.gate_items:
            self.scene.removeItem(self.gate_items[gate])
            del self.gate_items[gate]

    # === Annotation Management ===

    def add_annotation(self, annotation):
        """Add an annotation to the canvas"""
        if isinstance(annotation, TextAnnotation):
            annotation_item = TextAnnotationItem(annotation)
        elif isinstance(annotation, RectangleAnnotation):
            annotation_item = RectangleAnnotationItem(annotation)
        elif isinstance(annotation, CircleAnnotation):
            annotation_item = CircleAnnotationItem(annotation)
        else:
            return None

        self.scene.addItem(annotation_item)
        self.annotation_items[annotation] = annotation_item
        return annotation_item

    def remove_annotation(self, annotation):
        """Remove an annotation from the canvas"""
        if annotation in self.annotation_items:
            self.scene.removeItem(self.annotation_items[annotation])
            del self.annotation_items[annotation]

    def clear_all(self):
        self.scene.clear()
        self.gate_items.clear()
        self.annotation_items.clear()
        self.wire_items.clear()

    def reset_view(self):
        self.resetTransform()
        self.zoom_level = 1.0
        self.centerOn(0, 0)

    # === Wire Management ===

    def update_wires(self):
        for wire_item in self.wire_items:
            self.scene.removeItem(wire_item)
        self.wire_items.clear()

        for gate in self.gate_items.keys():
            for input_pin in gate.inputs:
                if input_pin.connected_to:
                    wire_item = WireItem(
                        input_pin.connected_to, input_pin, input_pin.waypoints
                    )
                    self.scene.addItem(wire_item)
                    self.wire_items.append(wire_item)

    def _handle_pin_click(self, pin_item):
        pin = pin_item.pin
        parent_gate = self._find_gate_for_pin_item(pin_item)
        if not parent_gate:
            return

        is_output = pin in parent_gate.outputs

        if self.connecting_from is None:
            # Start connection from output pin
            if is_output:
                self.connecting_from = pin
                self.temp_waypoints = []
                self.temp_wire_line = QGraphicsPathItem()
                self.temp_wire_line.setPen(QPen(QColor(ACCENT), 3, Qt.DashLine))
                self.temp_wire_line.setZValue(5)
                self.scene.addItem(self.temp_wire_line)
                pin_item.setBrush(QBrush(QColor(ACCENT)))
        else:
            # Complete connection to input pin
            from_gate = self._find_gate_for_pin(self.connecting_from)
            if from_gate and not is_output:
                pin.connected_to = self.connecting_from
                pin.waypoints = self.temp_waypoints.copy()
                self.update_wires()
                self._notify_change()
            self.cancel_wire_connection()

    def _remove_wire_from_pin(self, pin_item):
        pin = pin_item.pin
        parent_gate = self._find_gate_for_pin_item(pin_item)
        if parent_gate and pin in parent_gate.inputs and pin.connected_to:
            pin.connected_to = None
            pin.waypoints = []
            self.update_wires()
            self._notify_change()

    def _update_temp_wire(self, current_pos):
        if not self.connecting_from or not self.temp_wire_line:
            return

        path = QPainterPath()
        from_pos = QPointF(self.connecting_from.x, self.connecting_from.y)
        if hasattr(self.connecting_from, "_pin_item"):
            from_pos = self.connecting_from._pin_item.sceneBoundingRect().center()

        path.moveTo(from_pos)
        for wx, wy in self.temp_waypoints:
            path.lineTo(wx, wy)
        path.lineTo(current_pos.x(), current_pos.y())
        self.temp_wire_line.setPath(path)

    def cancel_wire_connection(self):
        if self.temp_wire_line:
            self.scene.removeItem(self.temp_wire_line)
            self.temp_wire_line = None
        self.connecting_from = None
        self.temp_waypoints = []
        self.update_wires()

    # === Helpers ===

    def _find_gate_for_pin_item(self, pin_item):
        for gate, gate_item in self.gate_items.items():
            if pin_item.parent_gate_item == gate_item:
                return gate
        return None

    def _find_gate_for_pin(self, pin):
        for gate in self.gate_items.keys():
            if pin in gate.outputs:
                return gate
        return None

    def _notify_change(self):
        if self.parent_window:
            self.parent_window.unsaved_changes = True
            self.parent_window.save_state()
            self.parent_window.update_window_title()

    def schedule_save_state(self):
        self.save_state_timer.stop()
        self.save_state_timer.start(300)

    def _do_save_state(self):
        self._notify_change()
