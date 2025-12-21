from core import InputSwitch


def collect_influencing_inputs(find_source_func, start_gate):
    """Traverse upstream from start_gate and collect all InputSwitch gates that influence it.

    - find_source_func: callable(pin) -> gate that owns that output pin
    Returns list of InputSwitch objects in deterministic order (label, id)
    """
    inputs = []
    visited = set()
    queue = []

    # Start from input pins of the start gate
    for pin in getattr(start_gate, "inputs", []):
        src = pin.connected_to
        if not src:
            continue
        src_gate = find_source_func(src)
        if src_gate:
            queue.append(src_gate)

    while queue:
        g = queue.pop(0)
        if id(g) in visited:
            continue
        visited.add(id(g))

        if isinstance(g, InputSwitch):
            inputs.append(g)
            continue

        for pin in getattr(g, "inputs", []):
            if pin.connected_to:
                src_gate = find_source_func(pin.connected_to)
                if src_gate and id(src_gate) not in visited:
                    queue.append(src_gate)

    inputs.sort(key=lambda x: (x.label or "", id(x)))
    return inputs
