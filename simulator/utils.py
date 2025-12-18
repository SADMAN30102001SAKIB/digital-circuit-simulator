import uuid
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
