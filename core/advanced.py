import math

from .base import Gate, Pin


class Multiplexer(Gate):
    """N-to-1 Multiplexer: selects one of N inputs based on select lines"""

    def __init__(self, x, y, select_bits=1):
        super().__init__(x, y, "MUX")
        self.select_bits = select_bits
        self.num_data_inputs = 2**select_bits
        self.num_inputs = self.num_data_inputs + select_bits  # Total inputs for display
        self.num_outputs = 1  # MUX always has 1 output
        self.width = 80
        self.height = max(80, 20 + (self.num_data_inputs + select_bits) * 12)

        # Data inputs on left side
        self.inputs = []
        for i in range(self.num_data_inputs):
            y_offset = (
                10 + (i * (self.height - 20) // max(1, self.num_data_inputs - 1))
                if self.num_data_inputs > 1
                else self.height // 2
            )
            self.inputs.append(Pin(x, y + y_offset))

        # Select inputs on bottom
        for i in range(select_bits):
            x_offset = (
                20 + (i * (self.width - 40) // max(1, select_bits - 1))
                if select_bits > 1
                else self.width // 2
            )
            self.inputs.append(Pin(x + x_offset, y + self.height))

        self.outputs = [Pin(x + self.width, y + self.height // 2)]

    def eval(self):
        if len(self.inputs) < self.num_data_inputs + self.select_bits:
            return False

        # Calculate selected index from select bits
        selected = 0
        for i in range(self.select_bits):
            if self.inputs[self.num_data_inputs + i].get_value():
                selected |= 1 << i

        # Return selected input
        if selected < self.num_data_inputs:
            return self.inputs[selected].get_value()
        return False

    def update_pin_positions(self):
        # Update data input positions
        for i in range(self.num_data_inputs):
            y_offset = (
                10 + (i * (self.height - 20) // max(1, self.num_data_inputs - 1))
                if self.num_data_inputs > 1
                else self.height // 2
            )
            self.inputs[i].x = self.x
            self.inputs[i].y = self.y + y_offset

        # Update select input positions
        for i in range(self.select_bits):
            x_offset = (
                20 + (i * (self.width - 40) // max(1, self.select_bits - 1))
                if self.select_bits > 1
                else self.width // 2
            )
            self.inputs[self.num_data_inputs + i].x = self.x + x_offset
            self.inputs[self.num_data_inputs + i].y = self.y + self.height

        self.outputs[0].x = self.x + self.width
        self.outputs[0].y = self.y + self.height // 2


class Demultiplexer(Gate):
    """1-to-N Demultiplexer: routes input to one of N outputs based on select"""

    def __init__(self, x, y, select_bits=1):
        super().__init__(x, y, "DEMUX")
        self.select_bits = select_bits
        self.num_outputs = 2**select_bits
        self.num_inputs = 1 + select_bits  # 1 data input + select bits
        self.width = 80
        self.height = max(80, 20 + (self.num_outputs + select_bits) * 12)

        # Data input on left
        self.inputs = [Pin(x, y + self.height // 2)]

        # Select inputs on bottom
        for i in range(select_bits):
            x_offset = (
                20 + (i * (self.width - 40) // max(1, select_bits - 1))
                if select_bits > 1
                else self.width // 2
            )
            self.inputs.append(Pin(x + x_offset, y + self.height))

        # Data outputs on right side
        self.outputs = []
        for i in range(self.num_outputs):
            y_offset = (
                10 + (i * (self.height - 20) // max(1, self.num_outputs - 1))
                if self.num_outputs > 1
                else self.height // 2
            )
            self.outputs.append(Pin(x + self.width, y + y_offset))

    def eval(self):
        # For multi-output gates, we need special handling
        return False

    def update(self):
        """Custom update for multiple outputs"""
        if len(self.inputs) < 1 + self.select_bits:
            return

        data = self.inputs[0].get_value()

        # Calculate selected index from select bits
        selected = 0
        for i in range(self.select_bits):
            if self.inputs[1 + i].get_value():
                selected |= 1 << i

        # Route data to selected output, others are 0
        for i in range(self.num_outputs):
            if i == selected:
                self.outputs[i].set_value(data)
            else:
                self.outputs[i].set_value(False)

    def update_pin_positions(self):
        # Data input
        self.inputs[0].x = self.x
        self.inputs[0].y = self.y + self.height // 2

        # Select inputs
        for i in range(self.select_bits):
            x_offset = (
                20 + (i * (self.width - 40) // max(1, self.select_bits - 1))
                if self.select_bits > 1
                else self.width // 2
            )
            self.inputs[1 + i].x = self.x + x_offset
            self.inputs[1 + i].y = self.y + self.height

        # Data outputs
        for i in range(self.num_outputs):
            y_offset = (
                10 + (i * (self.height - 20) // max(1, self.num_outputs - 1))
                if self.num_outputs > 1
                else self.height // 2
            )
            self.outputs[i].x = self.x + self.width
            self.outputs[i].y = self.y + y_offset


class Encoder(Gate):
    """Priority Encoder: converts active input index to binary output"""

    def __init__(self, x, y, num_inputs=4):
        super().__init__(x, y, "ENCODER")
        self.num_inputs = num_inputs
        self.width = 90
        self.height = max(80, 20 + num_inputs * 15)

        # Create input pins
        self.inputs = []
        for i in range(num_inputs):
            y_offset = (
                10 + (i * (self.height - 20) // (num_inputs - 1))
                if num_inputs > 1
                else self.height // 2
            )
            self.inputs.append(Pin(x, y + y_offset))

        # Output bits (log2 of inputs)
        num_outputs = max(1, int(math.ceil(math.log2(num_inputs))))
        self.num_outputs = num_outputs
        self.outputs = []
        for i in range(num_outputs):
            y_offset = (
                20 + (i * (self.height - 40) // (num_outputs - 1))
                if num_outputs > 1
                else self.height // 2
            )
            self.outputs.append(Pin(x + self.width, y + y_offset))

    def eval(self):
        # Priority encoder: highest active input wins
        active_index = -1
        for i in range(len(self.inputs) - 1, -1, -1):
            if self.inputs[i].get_value():
                active_index = i
                break
        return active_index != -1

    def update(self):
        """Custom update for multiple outputs"""
        active_index = -1
        for i in range(len(self.inputs) - 1, -1, -1):
            if self.inputs[i].get_value():
                active_index = i
                break

        # Convert to binary
        if active_index == -1:
            # No input active - all outputs 0
            for output in self.outputs:
                output.set_value(False)
        else:
            # Set binary representation
            for i, output in enumerate(self.outputs):
                bit = (active_index >> i) & 1
                output.set_value(bool(bit))

    def update_pin_positions(self):
        for i, pin in enumerate(self.inputs):
            y_offset = (
                10 + (i * (self.height - 20) // (self.num_inputs - 1))
                if self.num_inputs > 1
                else self.height // 2
            )
            pin.x = self.x
            pin.y = self.y + y_offset

        for i, pin in enumerate(self.outputs):
            y_offset = (
                20 + (i * (self.height - 40) // (self.num_outputs - 1))
                if self.num_outputs > 1
                else self.height // 2
            )
            pin.x = self.x + self.width
            pin.y = self.y + y_offset


class Decoder(Gate):
    """Binary Decoder: activates one output based on binary input"""

    def __init__(self, x, y, num_inputs=2):
        super().__init__(x, y, "DECODER")
        self.num_inputs = num_inputs
        self.width = 90

        # Output count is 2^inputs
        num_outputs = 2**num_inputs
        self.num_outputs = num_outputs
        self.height = max(80, 20 + num_outputs * 15)

        # Binary inputs
        self.inputs = []
        for i in range(num_inputs):
            y_offset = (
                20 + (i * (self.height - 40) // (num_inputs - 1))
                if num_inputs > 1
                else self.height // 2
            )
            self.inputs.append(Pin(x, y + y_offset))

        # Decoded outputs
        self.outputs = []
        for i in range(num_outputs):
            y_offset = (
                10 + (i * (self.height - 20) // (num_outputs - 1))
                if num_outputs > 1
                else self.height // 2
            )
            self.outputs.append(Pin(x + self.width, y + y_offset))

    def eval(self):
        return False  # Multi-output

    def update(self):
        """Custom update for multiple outputs"""
        # Read binary input value
        value = 0
        for i, inp in enumerate(self.inputs):
            if inp.get_value():
                value |= 1 << i

        # Activate corresponding output
        for i, output in enumerate(self.outputs):
            output.set_value(i == value)

    def update_pin_positions(self):
        for i, pin in enumerate(self.inputs):
            y_offset = (
                20 + (i * (self.height - 40) // (self.num_inputs - 1))
                if self.num_inputs > 1
                else self.height // 2
            )
            pin.x = self.x
            pin.y = self.y + y_offset

        for i, pin in enumerate(self.outputs):
            y_offset = (
                10 + (i * (self.height - 20) // (self.num_outputs - 1))
                if self.num_outputs > 1
                else self.height // 2
            )
            pin.x = self.x + self.width
            pin.y = self.y + y_offset
