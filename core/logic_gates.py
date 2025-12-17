from .base import Gate, Pin


class MultiInputGate(Gate):
    """Base class for gates with configurable number of inputs (AND, OR, XOR, NAND, NOR, XNOR)"""

    def __init__(self, x, y, name, num_inputs=2):
        super().__init__(x, y, name)
        self.num_inputs = num_inputs
        self.height = max(60, 20 + num_inputs * 15)

        # Create input pins on the left
        self.inputs = []
        for i in range(num_inputs):
            y_offset = self._calc_input_y_offset(i)
            self.inputs.append(Pin(x, y + y_offset))

        # Single output on the right
        self.outputs = [Pin(x + self.width, y + self.height // 2)]

    def _calc_input_y_offset(self, index):
        """Calculate Y offset for input pin at given index"""
        if self.num_inputs > 1:
            return 10 + (index * (self.height - 20) // (self.num_inputs - 1))
        return self.height // 2

    def update_pin_positions(self):
        """Update pin positions when gate is moved"""
        for i, pin in enumerate(self.inputs):
            pin.x = self.x
            pin.y = self.y + self._calc_input_y_offset(i)
        self.outputs[0].x = self.x + self.width
        self.outputs[0].y = self.y + self.height // 2


class ANDGate(MultiInputGate):
    """AND gate: output is True only if ALL inputs are True"""

    def __init__(self, x, y, num_inputs=2):
        super().__init__(x, y, "AND", num_inputs)

    def eval(self):
        return all(pin.get_value() for pin in self.inputs) if self.inputs else False


class ORGate(MultiInputGate):
    """OR gate: output is True if ANY input is True"""

    def __init__(self, x, y, num_inputs=2):
        super().__init__(x, y, "OR", num_inputs)

    def eval(self):
        return any(pin.get_value() for pin in self.inputs) if self.inputs else False


class NANDGate(MultiInputGate):
    """NAND gate: NOT AND"""

    def __init__(self, x, y, num_inputs=2):
        super().__init__(x, y, "NAND", num_inputs)

    def eval(self):
        return not all(pin.get_value() for pin in self.inputs) if self.inputs else False


class NORGate(MultiInputGate):
    """NOR gate: NOT OR"""

    def __init__(self, x, y, num_inputs=2):
        super().__init__(x, y, "NOR", num_inputs)

    def eval(self):
        return not any(pin.get_value() for pin in self.inputs) if self.inputs else True


class XORGate(MultiInputGate):
    """XOR gate: True if odd number of inputs are True"""

    def __init__(self, x, y, num_inputs=2):
        super().__init__(x, y, "XOR", num_inputs)

    def eval(self):
        return (
            sum(pin.get_value() for pin in self.inputs) % 2 == 1
            if len(self.inputs) >= 2
            else False
        )


class XNORGate(MultiInputGate):
    """XNOR gate: True if even number of inputs are True"""

    def __init__(self, x, y, num_inputs=2):
        super().__init__(x, y, "XNOR", num_inputs)

    def eval(self):
        return (
            sum(pin.get_value() for pin in self.inputs) % 2 == 0
            if len(self.inputs) >= 2
            else False
        )


class NOTGate(Gate):
    """NOT gate: inverts the input"""

    def __init__(self, x, y):
        super().__init__(x, y, "NOT")
        self.inputs = [Pin(x, y + 30)]
        self.outputs = [Pin(x + self.width, y + 30)]

    def eval(self):
        return not self.inputs[0].get_value() if self.inputs else False

    def update_pin_positions(self):
        self.inputs[0].x = self.x
        self.inputs[0].y = self.y + 30
        self.outputs[0].x = self.x + self.width
        self.outputs[0].y = self.y + 30
