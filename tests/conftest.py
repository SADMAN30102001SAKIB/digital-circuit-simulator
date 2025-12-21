import pytest
from PySide6.QtWidgets import QApplication
import sys


@pytest.fixture(scope="session")
def qapp():
    """Shared QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def clean_sim(qapp):
    """Provides a clean CircuitSimulator instance (headless if possible)."""
    from simulator.main import CircuitSimulator

    sim = CircuitSimulator()
    # Mocking some UI interactions that might block
    sim.show = lambda: None
    return sim
