from collections import OrderedDict

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from simulator.truthtable import collect_influencing_inputs


class VirtualTruthTableModel(QAbstractTableModel):
    """A virtual table model that exposes 2^n rows and n+1 columns for inputs and output.

    Important: this model operates on the provided gate objects directly and will
    mutate gate state when computing rows. The caller should snapshot and pause
    simulation while the model is in use (e.g., take save_state and stop sim timer),
    then restore state after the dialog is closed.
    """

    def __init__(self, gates, find_source_func, led, inputs=None, cache_size=256):
        super().__init__()
        self.gates = gates
        self.find_source = find_source_func
        self.led = led

        if inputs is None:
            self.inputs = collect_influencing_inputs(self.find_source, self.led)
        else:
            self.inputs = list(inputs)

        self.n = len(self.inputs)
        self._row_count = 1 << self.n if self.n else 0

        # Small LRU-like cache (OrderedDict) of recently computed rows
        self._cache = OrderedDict()
        self._cache_size = max(16, cache_size)

    def rowCount(self, parent=QModelIndex()):
        return self._row_count

    def columnCount(self, parent=QModelIndex()):
        # n inputs + 1 output
        return self.n + 1

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if section < self.n:
                return self.inputs[section].label or f"IN{section+1}"
            return self.led.label or "LED"
        if orientation == Qt.Vertical:
            return str(section + 1)
        return None

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def _ensure_cached(self, row_idx):
        if row_idx in self._cache:
            # move to end
            val = self._cache.pop(row_idx)
            self._cache[row_idx] = val
            return val

        # Compute the row on-demand: set inputs, run stabilizer, evaluate led
        bits = [bool((row_idx >> i) & 1) for i in range(self.n)]
        # Apply bits to input switches
        for i, g in enumerate(self.inputs):
            bit = bits[i]
            if hasattr(g, "state"):
                g.state = bit
            if getattr(g, "outputs", []):
                try:
                    g.outputs[0].set_value(bit)
                except Exception:
                    pass

        # Single pass update for combinational logic (no feedback expected)
        for gate in self.gates:
            try:
                gate.update()
            except Exception:
                pass

        # Evaluate LED
        try:
            out_val = (
                self.led.eval()
                if hasattr(self.led, "eval")
                else (
                    self.led.inputs[0].get_value()
                    if getattr(self.led, "inputs", None)
                    else False
                )
            )
        except Exception:
            out_val = False

        result = (bits, bool(out_val))

        # Insert in cache
        self._cache[row_idx] = result
        if len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)
        return result

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.TextAlignmentRole):
            return None
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignCenter)

        row = index.row()
        col = index.column()
        bits, out_val = self._ensure_cached(row)
        if col < self.n:
            return "1" if bits[col] else "0"
        return "1" if out_val else "0"

    def get_row(self, idx):
        """Public accessor for a computed row.

        Returns (bits_list, out_val, was_cached)
        """
        if idx < 0 or idx >= self._row_count:
            raise IndexError("row index out of range")
        was_cached = idx in self._cache
        bits, out_val = self._ensure_cached(idx)
        return bits, out_val, was_cached
