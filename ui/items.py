from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QGraphicsPathItem

from core.base import calculate_rotated_pin_positions
from ui.theme import *


class GateItem(QGraphicsItem):
    """Visual representation of a logic gate"""

    def __init__(self, gate, parent=None):
        super().__init__(parent)
        self.gate = gate
        self._initializing = True

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

        # Set rotation using Qt's transform (rotates around center)
        self.setTransformOriginPoint(gate.width / 2, gate.height / 2)
        self.setRotation(-gate.rotation)
        self.setPos(gate.x, gate.y)
        self.setZValue(10)

        self._initializing = False

    def boundingRect(self):
        margin = 6
        if self.gate.name == "LED":
            size = max(self.gate.width, self.gate.height) + margin * 2
            return QRectF(-margin, -margin, size, size)
        return QRectF(
            -margin,
            -margin,
            self.gate.width + margin * 2,
            self.gate.height + margin * 2,
        )

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)

        # Get color based on gate type and state
        if self.gate.name == "INPUT":
            color = QColor(SUCCESS if self.gate.state else WIRE_INACTIVE)
        elif self.gate.name == "LED":
            color = QColor(DANGER if self.gate.eval() else WIRE_INACTIVE)
        else:
            color = QColor(GATE_COLORS.get(self.gate.name, ACCENT))

        # Draw selection border
        if self.isSelected():
            painter.setPen(
                QPen(QColor(SELECTION), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            )
            painter.setBrush(Qt.NoBrush)
            if self.gate.name == "LED":
                painter.drawEllipse(
                    QRectF(-3, -3, self.gate.width + 6, self.gate.height + 6)
                )
            else:
                painter.drawRoundedRect(
                    QRectF(-3, -3, self.gate.width + 6, self.gate.height + 6), 8, 8
                )

        # Draw gate body
        painter.setPen(QPen(QColor(TEXT_COLOR), 2))
        painter.setBrush(QBrush(color))

        if self.gate.name == "LED":
            painter.drawEllipse(QRectF(0, 0, self.gate.width, self.gate.height))
        else:
            painter.drawRoundedRect(
                QRectF(0, 0, self.gate.width, self.gate.height), 6, 6
            )

        # Draw label
        painter.setPen(QColor(TEXT_COLOR))
        font = QFont("Segoe UI", 12 if self.gate.name == "LED" else 11, QFont.Bold)
        painter.setFont(font)
        painter.drawText(
            QRectF(0, 0, self.gate.width, self.gate.height),
            Qt.AlignCenter,
            self.gate.name,
        )

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            if hasattr(self, "_initializing") and self._initializing:
                return super().itemChange(change, value)

            # Update gate position and recalculate pins
            self.gate.x = value.x()
            self.gate.y = value.y()
            calculate_rotated_pin_positions(self.gate)

            # Notify view to update wires
            if self.scene() and self.scene().views():
                view = self.scene().views()[0]
                if hasattr(view, "update_wires"):
                    view.update_wires()

        elif change == QGraphicsItem.ItemPositionHasChanged:
            # Mark as unsaved and schedule state save
            if self.scene() and self.scene().views():
                view = self.scene().views()[0]
                if hasattr(view, "parent_window"):
                    view.parent_window.unsaved_changes = True
                    view.parent_window.update_window_title()
                    if hasattr(view, "schedule_save_state"):
                        view.schedule_save_state()

        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        """Toggle INPUT on double-click"""
        if self.gate.name == "INPUT":
            self.gate.toggle()
            self.update()
            if self.scene() and self.scene().views():
                view = self.scene().views()[0]
                if hasattr(view, "update_wires"):
                    view.update_wires()
                if hasattr(view, "parent_window"):
                    view.parent_window.unsaved_changes = True
                    view.parent_window.save_state()
                    view.parent_window.update_window_title()
        super().mouseDoubleClickEvent(event)


class PinItem(QGraphicsEllipseItem):
    """Visual representation of a connection pin"""

    def __init__(self, pin, parent_gate_item):
        super().__init__(-4, -4, 8, 8, parent_gate_item)
        self.pin = pin
        self.parent_gate_item = parent_gate_item

        self.setPen(QPen(QColor(TEXT_COLOR), 2))
        self.setBrush(QBrush(QColor(WIRE_INACTIVE)))
        self.setZValue(15)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)

        # Hover state (used to avoid flicker when simulation updates colors)
        self._hovered = False

        self.update_position()

    def update_position(self):
        """Update pin position relative to gate"""
        gate = self.parent_gate_item.gate
        if not hasattr(self.pin, "local_x"):
            self.pin.local_x = self.pin.x - gate.x
            self.pin.local_y = self.pin.y - gate.y
        self.setPos(self.pin.local_x, self.pin.local_y)

    def hoverEnterEvent(self, event):
        # Mark hovered to prevent simulation updates from overriding hover color
        self._hovered = True
        self.setBrush(QBrush(QColor(ACCENT)))
        try:
            self.setCursor(Qt.PointingHandCursor)
        except Exception:
            pass
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        # Clear hovered flag and refresh color based on signal value
        self._hovered = False
        try:
            self.unsetCursor()
        except Exception:
            pass
        self.update_color()
        super().hoverLeaveEvent(event)

    def update_color(self):
        """Update color based on signal value. Preserve hover color when hovered."""
        if getattr(self, "_hovered", False):
            self.setBrush(QBrush(QColor(ACCENT)))
            return
        color = WIRE_ACTIVE if self.pin.get_value() else WIRE_INACTIVE
        self.setBrush(QBrush(QColor(color)))


class WireItem(QGraphicsPathItem):
    """Visual representation of a wire connection"""

    def __init__(self, from_pin, to_pin, waypoints=None):
        super().__init__()
        self.from_pin = from_pin
        self.to_pin = to_pin
        self.waypoints = waypoints or []
        self.setZValue(5)
        self.update_path()

    def update_path(self):
        """Update wire path and color"""
        path = QPainterPath()

        # Get pin positions (use scene position if available)
        from_pos = QPointF(self.from_pin.x, self.from_pin.y)
        to_pos = QPointF(self.to_pin.x, self.to_pin.y)

        if hasattr(self.from_pin, "_pin_item"):
            from_pos = self.from_pin._pin_item.sceneBoundingRect().center()
        if hasattr(self.to_pin, "_pin_item"):
            to_pos = self.to_pin._pin_item.sceneBoundingRect().center()

        # Build path
        path.moveTo(from_pos)
        for wx, wy in self.waypoints:
            path.lineTo(wx, wy)
        path.lineTo(to_pos)

        self.setPath(path)

        # Color based on signal
        color = QColor(WIRE_ACTIVE if self.to_pin.get_value() else WIRE_INACTIVE)
        self.setPen(QPen(color, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))


class AnnotationItem(QGraphicsItem):
    """Base class for annotation items (movable, no pins)"""

    def __init__(self, annotation, parent=None):
        super().__init__(parent)
        self.annotation = annotation
        self._initializing = True

        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

        # Set rotation using Qt's transform
        self.setTransformOriginPoint(annotation.width / 2, annotation.height / 2)
        self.setRotation(-annotation.rotation)
        self.setPos(annotation.x, annotation.y)
        self.setZValue(8)  # Below gates but above wires

        self._initializing = False

    def boundingRect(self):
        margin = 12  # Increased margin to avoid clipping text descenders/ascenders
        return QRectF(
            -margin,
            -margin,
            self.annotation.width + margin * 2,
            self.annotation.height + margin * 2,
        )

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            if hasattr(self, "_initializing") and self._initializing:
                return super().itemChange(change, value)

            # Update annotation position
            self.annotation.x = value.x()
            self.annotation.y = value.y()

        elif change == QGraphicsItem.ItemPositionHasChanged:
            # Mark as unsaved and schedule state save
            if self.scene() and self.scene().views():
                view = self.scene().views()[0]
                if hasattr(view, "parent_window"):
                    view.parent_window.unsaved_changes = True
                    view.parent_window.update_window_title()
                    if hasattr(view, "schedule_save_state"):
                        view.schedule_save_state()

        return super().itemChange(change, value)

    def paint(self, painter, option, widget):
        """Override in subclasses"""
        pass


class TextAnnotationItem(AnnotationItem):
    """Visual representation of a text annotation"""

    def __init__(self, annotation, parent=None):
        super().__init__(annotation, parent)
        self.setZValue(20)  # Always on top per user request

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        annotation = self.annotation

        # Draw selection border
        if self.isSelected():
            painter.setPen(
                QPen(QColor(SELECTION), 2, Qt.DashLine, Qt.RoundCap, Qt.RoundJoin)
            )
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(
                QRectF(-2, -2, annotation.width + 4, annotation.height + 4), 4, 4
            )

        # Setup font
        font = QFont(annotation.font_family, annotation.font_size)
        if annotation.font_bold:
            font.setBold(True)
        if annotation.font_italic:
            font.setItalic(True)
        painter.setFont(font)

        # Draw text
        painter.setPen(QColor(annotation.text_color))
        # Use a larger rect for drawing text to prevent clipping of descenders
        # boundingRect has margin=12, so we can draw up to +/- 10 comfortably
        text_rect = QRectF(0, -10, annotation.width, annotation.height + 20)
        painter.drawText(
            text_rect,
            Qt.AlignCenter | Qt.TextWordWrap,
            annotation.text,
        )


class RectangleAnnotationItem(AnnotationItem):
    """Visual representation of a transparent rectangle with border"""

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)

        annotation = self.annotation

        # Draw selection border (outer)
        if self.isSelected():
            painter.setPen(
                QPen(QColor(SELECTION), 2, Qt.DashLine, Qt.RoundCap, Qt.RoundJoin)
            )
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(
                QRectF(-4, -4, annotation.width + 8, annotation.height + 8), 6, 6
            )

        # Draw rectangle border (transparent fill)
        painter.setPen(
            QPen(
                QColor(annotation.border_color),
                annotation.border_width,
                Qt.SolidLine,
                Qt.SquareCap,
                Qt.MiterJoin,
            )
        )
        painter.setBrush(Qt.NoBrush)
        radius = getattr(annotation, "border_radius", 0)  # Handle legacy objects
        painter.drawRoundedRect(
            QRectF(0, 0, annotation.width, annotation.height), radius, radius
        )


class CircleAnnotationItem(AnnotationItem):
    """Visual representation of a transparent circle with border"""

    def boundingRect(self):
        margin = 6
        diameter = self.annotation.diameter
        return QRectF(-margin, -margin, diameter + margin * 2, diameter + margin * 2)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)

        annotation = self.annotation
        diameter = annotation.diameter

        # Update transform origin for circle
        self.setTransformOriginPoint(diameter / 2, diameter / 2)

        # Draw selection border (outer)
        if self.isSelected():
            painter.setPen(
                QPen(QColor(SELECTION), 2, Qt.DashLine, Qt.RoundCap, Qt.RoundJoin)
            )
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QRectF(-4, -4, diameter + 8, diameter + 8))

        # Draw circle border (transparent fill)
        painter.setPen(
            QPen(
                QColor(annotation.border_color),
                annotation.border_width,
                Qt.SolidLine,
                Qt.RoundCap,
                Qt.RoundJoin,
            )
        )
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(0, 0, diameter, diameter))
