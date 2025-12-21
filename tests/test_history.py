import pytest
from core.logic_gates import ANDGate


def test_history_basic(clean_sim):
    sim = clean_sim
    # Initial state (empty)
    assert len(sim.history) == 1
    assert sim.history_index == 0

    # 1. Add a gate
    gate = ANDGate(100, 100)
    sim.gates.append(gate)
    sim.save_state()

    assert len(sim.history) == 2
    assert sim.history_index == 1
    assert len(sim.history[1]["gates"]) == 1

    # 2. Undo
    sim.undo()
    assert sim.history_index == 0
    assert len(sim.gates) == 0

    # 3. Redo
    sim.redo()
    assert sim.history_index == 1
    assert len(sim.gates) == 1
    assert isinstance(sim.gates[0], ANDGate)


def test_history_branching(clean_sim):
    sim = clean_sim
    # State 0: Empty
    # State 1: Gate A
    sim.gates.append(ANDGate(0, 0))
    sim.save_state()

    # State 2: Gate A + Gate B
    sim.gates.append(ANDGate(200, 200))
    sim.save_state()

    assert len(sim.history) == 3

    # Go back to State 1
    sim.undo()
    assert len(sim.gates) == 1

    # Add a DIFFERENT Gate C (branching)
    sim.gates.append(ANDGate(500, 500))
    sim.save_state()

    # History should have truncated the old State 2 and added new State 2
    assert len(sim.history) == 3
    assert sim.history_index == 2
    # Check that Gate C (at 500, 500) is in the new state
    assert sim.gates[1].x == 500


def test_history_limit(clean_sim):
    sim = clean_sim
    sim.max_history = 5

    # Fill history beyond limit
    for i in range(10):
        sim.gates.append(ANDGate(i * 10, i * 10))
        sim.save_state()

    assert len(sim.history) == 5
    assert sim.history_index == 4  # Max valid index for size 5
