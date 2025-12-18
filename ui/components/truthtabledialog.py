from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


class TruthTableDialog(QDialog):
    """Dialog that displays a generated truth table and offers CSV export"""

    def __init__(self, input_names, output_name, rows, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Truth Table")
        self.setModal(True)
        self.resize(700, 500)

        # Keep a reference to the original rows so we can clear it on close to free memory
        self._rows = rows

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        title_label = QLabel("Truth Table")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)

        # Table
        from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

        cols = len(input_names) + 1
        table = QTableWidget()
        table.setColumnCount(cols)
        table.setRowCount(len(rows))
        headers = list(input_names) + [output_name]
        table.setHorizontalHeaderLabels(headers)

        for r, (bits, outv) in enumerate(rows):
            for c, b in enumerate(bits):
                item = QTableWidgetItem("1" if b else "0")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(r, c, item)
            item = QTableWidgetItem("1" if outv else "0")
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignCenter)
            table.setItem(r, cols - 1, item)

        # Center header labels
        table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)

        # Expose table for tests
        self.table = table

        table.resizeColumnsToContents()
        layout.addWidget(table)

        # Buttons: Copy CSV and Close
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_copy = QPushButton("Copy CSV")
        btn_copy.setProperty("class", "primary")
        btn_copy.clicked.connect(lambda: self._copy_csv(input_names, output_name, rows))
        btn_layout.addWidget(btn_copy)

        btn_close = QPushButton("Close")
        btn_close.setProperty("class", "success")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _copy_csv(self, input_names, output_name, rows):
        # Build CSV string and copy to clipboard
        import csv
        from io import StringIO

        from PySide6.QtGui import QGuiApplication

        sio = StringIO()
        writer = csv.writer(sio)
        writer.writerow(list(input_names) + [output_name])
        for bits, outv in rows:
            writer.writerow(["1" if b else "0" for b in bits] + ["1" if outv else "0"])

        QGuiApplication.clipboard().setText(sio.getvalue())
        # Provide feedback
        QMessageBox.information(self, "Copied", "CSV copied to clipboard")

    def _cleanup(self):
        """Free large in-memory data and Qt widgets to release memory when dialog closes."""
        try:
            # Clear underlying rows list if it was passed in
            if hasattr(self, "_rows") and isinstance(self._rows, list):
                try:
                    self._rows.clear()
                except Exception:
                    pass
                try:
                    del self._rows
                except Exception:
                    pass
        except Exception:
            pass

        try:
            if hasattr(self, "table"):
                try:
                    self.table.clearContents()
                    self.table.setRowCount(0)
                    self.table.deleteLater()
                except Exception:
                    pass
                try:
                    del self.table
                except Exception:
                    pass
        except Exception:
            pass

        try:
            import gc

            gc.collect()
        except Exception:
            pass

    def accept(self):
        # Ensure memory is released before dialog is destroyed
        self._cleanup()
        return super().accept()

    def reject(self):
        self._cleanup()
        return super().reject()

    def closeEvent(self, event):
        self._cleanup()
        return super().closeEvent(event)
