import pytest
from PySide6.QtCore import Qt
from ui.components.truthtablemodel import VirtualTruthTableModel
from core.logic_gates import ANDGate
from core.io import InputSwitch, OutputLED

def test_truthtable_model_logic(qapp):
    """Verify that the virtual model returns correct values for a simple AND gate."""
    sw1 = InputSwitch(0, 0)
    sw2 = InputSwitch(0, 50)
    and_g = ANDGate(100, 25)
    and_g.inputs[0].connected_to = sw1.outputs[0]
    and_g.inputs[1].connected_to = sw2.outputs[0]
    
    # Mock find_source_gate
    def mock_find_source(pin):
        for g in [sw1, sw2, and_g]:
            if pin in g.outputs:
                return g
        return None

    model = VirtualTruthTableModel([sw1, sw2, and_g], mock_find_source, led=and_g, inputs=[sw1, sw2])
    
    # Truth table for 2 inputs has 4 rows
    assert model.rowCount() == 4
    assert model.columnCount() == 3 # IN1, IN2, AND_OUT
    
    # Row 0: 0, 0 -> 0 (False, False -> False)
    # Row 3: 1, 1 -> 1 (True, True -> True)
    
    # Check data for row 0
    assert model.data(model.index(0, 0), Qt.DisplayRole) == "0"
    assert model.data(model.index(0, 1), Qt.DisplayRole) == "0"
    assert model.data(model.index(0, 2), Qt.DisplayRole) == "0"
    
    # Check data for row 3
    assert model.data(model.index(3, 0), Qt.DisplayRole) == "1"
    assert model.data(model.index(3, 1), Qt.DisplayRole) == "1"
    assert model.data(model.index(3, 2), Qt.DisplayRole) == "1"

def test_truthtable_model_caching(qapp):
    """Verify that the model cache stores and retrieves values."""
    sw1 = InputSwitch(0, 0)
    and_g = ANDGate(100, 25)
    
    def mock_find_source(pin): return None

    model = VirtualTruthTableModel([sw1, and_g], mock_find_source, led=and_g, inputs=[sw1])
    
    # Request row 1
    model.data(model.index(1, 0), Qt.DisplayRole)
    
    # Internal check: verify it's in cache
    assert 1 in model._cache
    
    # Change switch property (label) shouldn't invalidate cache
    sw1.label = "CHANGED"
    assert 1 in model._cache
