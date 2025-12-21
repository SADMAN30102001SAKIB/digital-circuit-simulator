import math


def calculate_rotated_pin_positions(gate):
    """Calculate pin positions after rotation - shared helper function"""
    if gate.rotation == 0:
        gate.update_pin_positions()
        return

    # Get base positions (no rotation)
    saved_rotation = gate.rotation
    gate.rotation = 0
    gate.update_pin_positions()

    # Calculate center and angle
    cx = gate.x + gate.width / 2
    cy = gate.y + gate.height / 2
    angle_rad = math.radians(saved_rotation)
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)

    # Rotate each pin around gate center
    for pin in gate.inputs + gate.outputs:
        # Store local coordinates for Qt rendering
        pin.local_x = pin.x - gate.x
        pin.local_y = pin.y - gate.y

        # Calculate rotated world position for wire connections
        dx = pin.local_x - gate.width / 2
        dy = pin.local_y - gate.height / 2
        pin.x = cx + dx * cos_a - dy * sin_a
        pin.y = cy + dx * sin_a + dy * cos_a

    gate.rotation = saved_rotation


class Wire:
    """A wire carries a boolean value. That's it."""

    def __init__(self):
        self.value = False

    def __repr__(self):
        return f"Wire({self.value})"


class Pin:
    """Visual connection point for wires"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.wire = Wire()  # Each pin has its own wire
        self.connected_to = None  # Can connect to another pin
        self.waypoints = []  # List of (x, y) waypoints for wire path

    def get_value(self):
        """Get the value from connected pin or own wire"""
        if self.connected_to:
            return self.connected_to.wire.value
        return self.wire.value

    def set_value(self, value):
        """Set value on the wire"""
        self.wire.value = value


class Gate:
    """Base class for all logic gates"""

    def __init__(self, x, y, name="GATE"):
        self.x = x
        self.y = y
        self.name = name
        self.label = None  # Optional user-friendly label for inputs/LEDs
        self.width = 80
        self.height = 60
        self.inputs = []
        self.outputs = []
        self.num_inputs = 2
        self.rotation = 0

    def eval(self):
        """Override this in subclasses"""
        return False

    def update(self):
        """Compute output based on inputs"""
        result = self.eval()
        if self.outputs:
            self.outputs[0].set_value(result)
