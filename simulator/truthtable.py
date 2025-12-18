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


def stabilize_until_converged(gates, max_iters):
    """Run updates on gates until outputs converge or max_iters reached.

    Returns True if converged, False otherwise.
    """
    for _ in range(max_iters):
        prev = []
        for gate in gates:
            for out in getattr(gate, "outputs", []):
                prev.append(out.wire.value)

        for gate in gates:
            gate.update()

        after = []
        for gate in gates:
            for out in getattr(gate, "outputs", []):
                after.append(out.wire.value)

        if prev == after:
            return True
    return False


def generate_truth_table_iter(gates, find_source_func, led, max_iters=None):
    """Generator that yields (idx, bits_list, led_value, converged_bool) for each input combination.

    Use this in UI to support progress and cancellation.
    """
    inputs = collect_influencing_inputs(find_source_func, led)
    n = len(inputs)
    total = 1 << n if n else 0
    if max_iters is None:
        max_iters = max(10, len(gates) * 3)

    for idx in range(total):
        # Set inputs according to bits
        for i, g in enumerate(inputs):
            bit = bool((idx >> i) & 1)
            if hasattr(g, "state"):
                g.state = bit
            if getattr(g, "outputs", []):
                g.outputs[0].set_value(bit)

        converged = stabilize_until_converged(gates, max_iters)

        out_val = (
            led.eval()
            if hasattr(led, "eval")
            else (led.inputs[0].get_value() if getattr(led, "inputs", None) else False)
        )

        bits = [bool((idx >> i) & 1) for i in range(n)]
        yield idx, bits, bool(out_val), converged
