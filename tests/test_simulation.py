import pytest
from core.logic_gates import ANDGate, ORGate, NOTGate
from core.io import InputSwitch, OutputLED

def test_signal_propagation():
    """Verify that flipping a switch propagates through gates to an LED."""
    sw = InputSwitch(0, 0)
    not_g = NOTGate(100, 0)
    led = OutputLED(200, 0)
    
    # Connect sw -> not -> led
    not_g.inputs[0].connected_to = sw.outputs[0]
    led.inputs[0].connected_to = not_g.outputs[0]
    
    # Simulation step 1: Switch OFF (False) -> NOT (True) -> LED (True)
    sw.state = False
    # Manual update loop (similar to Simulator.update_simulation)
    for _ in range(3): # Propagation depth 2-3
        sw.update()
        not_g.update()
        led.update()
    
    assert led.eval() is True
    
    # Simulation step 2: Switch ON (True) -> NOT (False) -> LED (False)
    sw.state = True
    for _ in range(3):
        sw.update()
        not_g.update()
        led.update()
    
    assert led.eval() is False

def test_complex_logic_tree():
    """Test a small logic tree (AND with one inverted input)."""
    sw1 = InputSwitch(0, 0)
    sw2 = InputSwitch(0, 50)
    not_g = NOTGate(100, 50)
    and_g = ANDGate(200, 25)
    led = OutputLED(300, 25)
    
    # (SW1) ----+
    #           |-- (AND) -- (LED)
    # (SW2) --(NOT)-+
    
    and_g.inputs[0].connected_to = sw1.outputs[0]
    not_g.inputs[0].connected_to = sw2.outputs[0]
    and_g.inputs[1].connected_to = not_g.outputs[0]
    led.inputs[0].connected_to = and_g.outputs[0]
    
    components = [sw1, sw2, not_g, and_g, led]
    
    def run_sim():
        for _ in range(5):
            for c in components:
                c.update()
                
    # Case: SW1=True, SW2=True -> NOT=False -> AND=False -> LED=False
    sw1.state = True
    sw2.state = True
    run_sim()
    assert led.eval() is False
    
    # Case: SW1=True, SW2=False -> NOT=True -> AND=True -> LED=True
    sw1.state = True
    sw2.state = False
    run_sim()
    assert led.eval() is True
