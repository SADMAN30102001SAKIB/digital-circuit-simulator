import pytest
import yaml
from simulator.persistence import get_save_state, load_from_state
from core.logic_gates import ANDGate, NOTGate
from core.io import InputSwitch, OutputLED

def test_full_serialization_cycle(clean_sim):
    sim = clean_sim
    
    # Create a simple circuit: Switch -> NOT -> LED
    sw = InputSwitch(0, 0)
    not_g = NOTGate(100, 0)
    led = OutputLED(200, 0)
    
    sim.gates = [sw, not_g, led]
    
    # Connect them
    not_g.inputs[0].connected_to = sw.outputs[0]
    led.inputs[0].connected_to = not_g.outputs[0]
    
    # Set properties
    sw.label = "MySwitch"
    sw.state = True
    
    state = get_save_state(sim)
    
    # Clear and Reload
    sim.gates.clear()
    load_from_state(sim, state, apply_settings=False)
    
    assert len(sim.gates) == 3
    
    # Find components in reloaded list
    sw_re = next(g for g in sim.gates if isinstance(g, InputSwitch))
    not_re = next(g for g in sim.gates if isinstance(g, NOTGate))
    led_re = next(g for g in sim.gates if isinstance(g, OutputLED))
    
    assert sw_re.label == "MySwitch"
    assert sw_re.state is True
    
    # Check connections
    assert not_re.inputs[0].connected_to == sw_re.outputs[0]
    assert led_re.inputs[0].connected_to == not_re.outputs[0]

def test_malformed_load_graceful(clean_sim):
    sim = clean_sim
    # Load completely empty/missing state
    load_from_state(sim, {}, apply_settings=True)
    assert len(sim.gates) == 0
    
    # Load state with unknown gate class
    bad_state = {
        "gates": [{"class": "AlienTechGate", "x": 10, "y": 10}]
    }
    load_from_state(sim, bad_state) 
    assert len(sim.gates) == 0 # Should skip unknown classes without crashing
