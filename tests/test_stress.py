import pytest
from core.logic_gates import ANDGate, NOTGate
from core.io import InputSwitch, OutputLED


def test_feedback_loop(clean_sim):
    """Test that a feedback loop (oscillator) Doesn't crash the simulator."""
    sim = clean_sim

    # 1. Create a NOT gate oscillator (NOT output to its own input)
    not_gate = NOTGate(100, 100)
    sim.gates.append(not_gate)

    # Connect input pin to output pin (Input reads from Output)
    not_gate.inputs[0].connected_to = not_gate.outputs[0]

    # Run simulation for several steps
    # On first step: Input=0 -> Output=1
    sim.update_simulation()
    assert not_gate.outputs[0].get_value() is True

    # On second step: Input=1 -> Output=0
    sim.update_simulation()
    assert not_gate.outputs[0].get_value() is False

    # On third step: Input=0 -> Output=1
    sim.update_simulation()
    assert not_gate.outputs[0].get_value() is True


def test_long_chain_propagation(clean_sim):
    """Test that signals propagate through a long chain over multiple frames."""
    sim = clean_sim

    sw = InputSwitch(0, 0)
    sim.gates.append(sw)

    prev_gate = sw
    chain_length = 10
    not_gates = []

    for i in range(chain_length):
        ng = NOTGate(100 * (i + 1), 0)
        sim.gates.append(ng)
        not_gates.append(ng)
        # Connect new input to prev output
        ng.inputs[0].connected_to = prev_gate.outputs[0]
        prev_gate = ng

    led = OutputLED(1200, 0)
    sim.gates.append(led)
    led.inputs[0].connected_to = prev_gate.outputs[0]

    # Turn switch ON
    sw.toggle()
    assert sw.outputs[0].get_value() is True

    # It should take exactly 'chain_length + 1' frames to reach the LED
    for frame in range(chain_length + 1):
        sim.update_simulation()

    # Switch is 1. 10 NOT gates. LED should be 1 (10 is even)
    assert led.inputs[0].get_value() is True


def test_large_circuit_stability(clean_sim):
    """Create a large grid of gates and ensure it runs within time limits."""
    sim = clean_sim
    import time

    size = 10
    for i in range(size):
        for j in range(size):
            sim.gates.append(ANDGate(i * 100, j * 100))

    start = time.time()
    for _ in range(100):
        sim.update_simulation()
    duration = time.time() - start

    # 100 gates, 100 updates. Under 1 second is very safe for 10,000 updates total.
    assert duration < 1.0
