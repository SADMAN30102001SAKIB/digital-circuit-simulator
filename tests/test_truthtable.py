"""Tests for simulator/truthtable.py - Input collection for truth table generation."""

from core import ANDGate, InputSwitch, ORGate


class TestCollectInfluencingInputs:
    """Test the collect_influencing_inputs function."""

    def test_single_input_to_gate(self):
        """Single input connected to a gate should be collected."""
        from simulator.truthtable import collect_influencing_inputs

        # Create a simple circuit: InputSwitch -> AND gate
        inp = InputSwitch(0, 0)
        inp.label = "A"
        gate = ANDGate(100, 0)

        # Connect input to gate (input's output pin -> gate's input pin)
        gate.inputs[0].connected_to = inp.outputs[0]

        # Mock find_source_func
        def find_source(pin):
            if pin is inp.outputs[0]:
                return inp
            return None

        result = collect_influencing_inputs(find_source, gate)
        assert len(result) == 1
        assert result[0] is inp

    def test_multiple_inputs_sorted_by_label(self):
        """Multiple inputs should be sorted by label."""
        from simulator.truthtable import collect_influencing_inputs

        inp_b = InputSwitch(0, 0)
        inp_b.label = "B"
        inp_a = InputSwitch(0, 50)
        inp_a.label = "A"
        gate = ANDGate(100, 0)

        gate.inputs[0].connected_to = inp_b.outputs[0]
        gate.inputs[1].connected_to = inp_a.outputs[0]

        def find_source(pin):
            if pin is inp_a.outputs[0]:
                return inp_a
            if pin is inp_b.outputs[0]:
                return inp_b
            return None

        result = collect_influencing_inputs(find_source, gate)
        assert len(result) == 2
        assert result[0].label == "A"
        assert result[1].label == "B"

    def test_no_inputs_connected(self):
        """Gate with no connected inputs should return empty list."""
        from simulator.truthtable import collect_influencing_inputs

        gate = ANDGate(0, 0)

        def find_source(pin):
            return None

        result = collect_influencing_inputs(find_source, gate)
        assert result == []

    def test_chained_gates(self):
        """Inputs through chained gates should be collected."""
        from simulator.truthtable import collect_influencing_inputs

        # Circuit: InputSwitch -> OR -> AND
        inp = InputSwitch(0, 0)
        inp.label = "X"
        or_gate = ORGate(100, 0)
        and_gate = ANDGate(200, 0)

        or_gate.inputs[0].connected_to = inp.outputs[0]
        and_gate.inputs[0].connected_to = or_gate.outputs[0]

        def find_source(pin):
            if pin is inp.outputs[0]:
                return inp
            if pin is or_gate.outputs[0]:
                return or_gate
            return None

        result = collect_influencing_inputs(find_source, and_gate)
        assert len(result) == 1
        assert result[0] is inp

    def test_duplicate_input_not_collected_twice(self):
        """Same input connected to multiple pins should only appear once."""
        from simulator.truthtable import collect_influencing_inputs

        inp = InputSwitch(0, 0)
        inp.label = "A"
        gate = ANDGate(100, 0)

        # Connect same input to both pins
        gate.inputs[0].connected_to = inp.outputs[0]
        gate.inputs[1].connected_to = inp.outputs[0]

        def find_source(pin):
            if pin is inp.outputs[0]:
                return inp
            return None

        result = collect_influencing_inputs(find_source, gate)
        assert len(result) == 1
