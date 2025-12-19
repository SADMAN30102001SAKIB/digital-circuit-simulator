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


def generate_truth_table_iter(gates, find_source_func, led):
    """Generator that yields (idx, bits_list, led_value) for each input combination.

    This simplified generator performs a single update pass per combination which is
    sufficient for combinational circuits (no feedback/sequential logic expected).
    """
    inputs = collect_influencing_inputs(find_source_func, led)
    n = len(inputs)
    total = 1 << n if n else 0

    for idx in range(total):
        # Set inputs according to bits
        for i, g in enumerate(inputs):
            bit = bool((idx >> i) & 1)
            if hasattr(g, "state"):
                g.state = bit
            if getattr(g, "outputs", []):
                try:
                    g.outputs[0].set_value(bit)
                except Exception:
                    pass

        # Single pass update for combinational logic
        for gate in gates:
            try:
                gate.update()
            except Exception:
                pass

        out_val = (
            led.eval()
            if hasattr(led, "eval")
            else (led.inputs[0].get_value() if getattr(led, "inputs", None) else False)
        )

        bits = [bool((idx >> i) & 1) for i in range(n)]
        yield idx, bits, bool(out_val)
