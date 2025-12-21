import pytest
import math
from core.base import Wire, Pin, Gate, calculate_rotated_pin_positions
from core.logic_gates import (
    ANDGate, ORGate, NANDGate, NORGate, XORGate, XNORGate, NOTGate
)

def test_wire_value():
    w = Wire()
    assert w.value is False
    w.value = True
    assert w.value is True

def test_pin_connection():
    p1 = Pin(0, 0)
    p2 = Pin(10, 10)
    p1.connected_to = p2
    p2.wire.value = True
    assert p1.get_value() is True
    p2.wire.value = False
    assert p1.get_value() is False

@pytest.mark.parametrize("gate_class, inputs, expected", [
    (ANDGate, [False, False], False),
    (ANDGate, [True, False], False),
    (ANDGate, [False, True], False),
    (ANDGate, [True, True], True),
    (ORGate, [False, False], False),
    (ORGate, [True, False], True),
    (ORGate, [False, True], True),
    (ORGate, [True, True], True),
    (NANDGate, [False, False], True),
    (NANDGate, [True, True], False),
    (NORGate, [False, False], True),
    (NORGate, [True, False], False),
    (XORGate, [True, True], False),
    (XORGate, [True, False], True),
    (XNORGate, [True, True], True),
    (XNORGate, [True, False], False),
])
def test_gates_2_inputs(gate_class, inputs, expected):
    gate = gate_class(0, 0, num_inputs=2)
    gate.inputs[0].wire.value = inputs[0]
    gate.inputs[1].wire.value = inputs[1]
    gate.update()
    assert gate.outputs[0].wire.value == expected

def test_not_gate():
    gate = NOTGate(0, 0)
    gate.inputs[0].wire.value = True
    gate.update()
    assert gate.outputs[0].wire.value is False
    gate.inputs[0].wire.value = False
    gate.update()
    assert gate.outputs[0].wire.value is True

def test_multi_input_gate_scaling():
    gate = ANDGate(0, 0, num_inputs=4)
    assert len(gate.inputs) == 4
    for p in gate.inputs:
        p.wire.value = True
    gate.update()
    assert gate.outputs[0].wire.value is True
    gate.inputs[3].wire.value = False
    gate.update()
    assert gate.outputs[0].wire.value is False

def test_rotation_math():
    # 90 degree rotation clockwise
    gate = ANDGate(0, 0)
    gate.rotation = 90
    calculate_rotated_pin_positions(gate)
    
    # Check output pin roughly (expected to move from right to bottom relative to center)
    # Original: (80, 30) with center (40, 30)
    # Relative: (40, 0)
    # Rotated 90 deg: (0, 40)
    # Final: (40, 70)
    out_pin = gate.outputs[0]
    assert math.isclose(out_pin.x, 40, abs_tol=0.1)
    assert math.isclose(out_pin.y, 70, abs_tol=0.1)
