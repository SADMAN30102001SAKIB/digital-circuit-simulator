import logging
import sys
import uuid
from pathlib import Path
from typing import Dict

from core import (
    ANDGate,
    CircleAnnotation,
    Decoder,
    Demultiplexer,
    Encoder,
    InputSwitch,
    Multiplexer,
    NANDGate,
    NORGate,
    NOTGate,
    ORGate,
    OutputLED,
    RectangleAnnotation,
    TextAnnotation,
    XNORGate,
    XORGate,
)

CLASS_MAP: Dict[str, type] = {
    cls.__name__: cls
    for cls in [
        ANDGate,
        ORGate,
        NOTGate,
        XORGate,
        NANDGate,
        NORGate,
        XNORGate,
        Multiplexer,
        Demultiplexer,
        Encoder,
        Decoder,
        InputSwitch,
        OutputLED,
    ]
}

ANNOTATION_CLASS_MAP: Dict[str, type] = {
    cls.__name__: cls for cls in [TextAnnotation, RectangleAnnotation, CircleAnnotation]
}


def ensure_uid(obj):
    """Ensure an object has a stable `uid` attribute. Returns the uid string."""
    if getattr(obj, "uid", None) is None:
        obj.uid = str(uuid.uuid4())
    return obj.uid


def ensure_uids_for_all(gates, annotations):
    """Assign uids to gates and annotations if they're missing."""
    for g in gates:
        ensure_uid(g)
    for a in annotations:
        ensure_uid(a)


def get_resource_path(rel_path: str) -> Path:
    """
    Robust path resolver for Dev, PyInstaller, and Nuitka.
    Checks for _MEIPASS (PyInstaller) and other bundle indicators.
    """
    # PyInstaller
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / rel_path

    # Nuitka / Development
    # Base is the parent of the 'simulator' directory
    base_path = Path(__file__).parents[1]
    return base_path / rel_path


def setup_logging(log_file: Path):
    """
    Setup professional logging to both console and file.
    """
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.info("--- Session Started ---")
    logging.info(f"OS: {sys.platform}")
    logging.info(f"Executable: {sys.executable}")
