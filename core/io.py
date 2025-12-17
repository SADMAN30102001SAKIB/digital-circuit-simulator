from .base import Gate, Pin


class InputSwitch(Gate):
    """Clickable input toggle"""

    def __init__(self, x, y):
        super().__init__(x, y, "INPUT")
        self.width = 70
        self.height = 50
        self.outputs = [Pin(x + self.width, y + 25)]
        self.state = False

    def toggle(self):
        """Flip the state"""
        self.state = not self.state
        self.outputs[0].set_value(self.state)

    def eval(self):
        return self.state

    def update(self):
        self.outputs[0].set_value(self.state)

    def update_pin_positions(self):
        self.outputs[0].x = self.x + self.width
        self.outputs[0].y = self.y + self.height // 2


class OutputLED(Gate):
    """Visual output indicator"""

    def __init__(self, x, y):
        super().__init__(x, y, "LED")
        self.width = 50
        self.height = 50
        self.inputs = [Pin(x, y + 25)]

    def eval(self):
        return self.inputs[0].get_value()

    def update(self):
        pass  # LED just displays, doesn't compute

    def update_pin_positions(self):
        self.inputs[0].x = self.x
        self.inputs[0].y = self.y + 25
