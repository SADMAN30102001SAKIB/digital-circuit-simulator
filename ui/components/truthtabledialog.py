import csv
import gc
import logging
import os
import platform
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QPoint, Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QTableView,
    QVBoxLayout,
)


class TruthTableDialog(QDialog):
    """Dialog that displays a generated truth table and offers CSV export.

    This dialog is model-driven: pass a `QAbstractTableModel` (`model`) which
    lazily provides rows and keeps memory usage low for very large truth tables.
    """

    def __init__(self, input_names, output_name, model, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Truth Table")
        self.setModal(True)
        self.resize(900, 600)

        # Model is required (no in-memory fallback)
        if model is None:
            raise ValueError("TruthTableDialog requires a `model` instance")
        self._model = model
        self._temp_csv = None

        # Export state trackers (used to allow safe cleanup when an export is active)
        self._export_in_progress = False
        self._export_cancel_requested = False
        self._export_file_handle = None
        self._exporting_path = None
        self._closing = False

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        title_label = QLabel("Truth Table")
        title_label.setProperty("class", "title")
        layout.addWidget(title_label)

        # Table area
        # Table area
        headers = list(input_names) + [output_name]

        # Virtual model (required)
        table_view = QTableView()
        table_view.setModel(model)

        # Center header alignment and set interactive width with minimum size
        h = table_view.horizontalHeader()
        h.setDefaultAlignment(Qt.AlignCenter)
        h.setMinimumSectionSize(40)
        try:
            h.setSectionResizeMode(QHeaderView.Interactive)
        except Exception:
            # Fall back if method unavailable in this Qt binding/version
            h.setStretchLastSection(True)

        # Manually resize columns based on header text only to avoid scanning 65K+ rows
        # This prevents the UI freeze reported with ResizeToContents.
        try:
            from PySide6.QtGui import QFontMetrics

            fm = QFontMetrics(table_view.font())
            for i, name in enumerate(headers):
                # Calculate width of header text + some padding
                w = fm.horizontalAdvance(name) + 24
                table_view.setColumnWidth(i, max(40, w))
        except Exception:
            logging.exception("Failed to manually resize truth table columns")

        # Show vertical row numbers (1-based) and center them
        v = table_view.verticalHeader()
        v.setVisible(True)
        v.setDefaultAlignment(Qt.AlignCenter)
        v.setDefaultSectionSize(20)

        # Expose for tests
        self.table = table_view
        layout.addWidget(table_view)

        # Buttons: Export and Close
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        # Export and preview actions (model-driven)
        btn_export = QPushButton("Export CSV")
        btn_export.setProperty("class", "primary")
        btn_export.clicked.connect(self._export_csv)
        # Expose for tests / to allow disabling during export
        self._btn_export = btn_export
        btn_layout.addWidget(btn_export)

        btn_close = QPushButton("Close")
        btn_close.setProperty("class", "success")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _export_csv(self):
        """Export CSV using a chunked main-thread worker with a modal progress dialog.

        This performs export in small timed chunks via QTimer to keep the UI
        responsive and avoid unsafe cross-thread access to model/UI state.
        The model provides `get_row(idx)` and `snapshot_cache_keys()` to keep
        the dialog ignorant of model internals.
        """
        model = getattr(self, "_model", None)
        if model is None:
            QMessageBox.information(
                self, "Export Unavailable", "No model available to export."
            )
            return

        # Prevent concurrent exports
        if getattr(self, "_export_in_progress", False):
            QMessageBox.information(
                self, "Export In Progress", "An export is already in progress."
            )
            return

        # Determine destination: Downloads if writable, otherwise a temporary file
        downloads_dir = None
        try:
            home = Path.home()
            candidate = home / "Downloads"
            if (
                candidate.exists()
                and candidate.is_dir()
                and os.access(candidate, os.W_OK)
            ):
                downloads_dir = candidate
        except Exception:
            downloads_dir = None

        if downloads_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"truth_table_{timestamp}.csv"
            dest = downloads_dir / filename
            counter = 0
            while dest.exists():
                counter += 1
                dest = downloads_dir / f"truth_table_{timestamp}_{counter}.csv"
            path = str(dest)
            saved_in_downloads = True
        else:
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
            path = tf.name
            tf.close()
            saved_in_downloads = False

        # Chunked exporter (main-thread): iterate rows in small batches to avoid
        # touching Qt objects from worker threads (which can hang) and keep the UI
        # responsive without complex timer-based scheduling.
        total = model.rowCount()

        # Use an exact progress max from the start to prevent Qt from behaving oddly
        progress = QProgressDialog("Exporting CSV...", "Cancel", 0, total, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoReset(False)
        progress.setAutoClose(False)
        progress.show()

        # Increase the dialog width so content has enough room on wide tables
        try:
            progress.setMinimumWidth(420)
        except Exception:
            logging.exception("Failed to set progress dialog minimum width")
        # Center the progress dialog over the parent so it remains visually centered
        try:
            progress.adjustSize()
            parent_center = self.frameGeometry().center()
            pg = progress.frameGeometry()
            new_top_left = QPoint(
                parent_center.x() - (pg.width() // 2),
                parent_center.y() - (pg.height() // 2),
            )
            progress.move(new_top_left)
        except Exception:
            logging.exception("Failed to center progress dialog")
        # Make the Cancel button compact/small to reduce visual weight
        try:
            cancel_btn = progress.findChild(QPushButton)
            if cancel_btn:
                existing = cancel_btn.property("class") or ""
                classes = set(existing.split())
                classes.add("small")
                # Preserve danger if present (visual cue)
                if "danger" not in classes:
                    classes.add("danger")
                cancel_btn.setProperty("class", " ".join(classes))
                try:
                    cancel_btn.style().unpolish(cancel_btn)
                    cancel_btn.style().polish(cancel_btn)
                except Exception:
                    # fallback: set inline style to match slightly larger small size
                    cancel_btn.setStyleSheet(
                        "padding:3px 8px; font-size:12px; min-height:24px; border-radius:4px;"
                    )
                # Enforce compact geometry so the button is visually small but not too tiny
                try:
                    cancel_btn.setFixedHeight(32)
                    # Slightly larger min width so text doesn't truncate awkwardly
                    cancel_btn.setMinimumWidth(72)
                    cancel_btn.setContentsMargins(2, 2, 2, 2)
                except Exception:
                    logging.exception("Failed to set compact size on cancel button")
                cancel_btn.update()
        except Exception:
            logging.exception("Failed to style progress dialog cancel button")

        batch = max(256, min(4096, total // 64 or 256))
        idx = 0
        # No per-row cache statistics are shown to the user; keep export simple
        # (the model still exposes `get_row(idx)` which the dialog uses).

        # Export lifecycle flags stored on the dialog so _cleanup() can observe them
        self._export_in_progress = True
        self._export_cancel_requested = False
        self._export_file_handle = None
        self._exporting_path = path
        self._closing = False

        # Disable export button immediately to prevent double-starts
        try:
            self._btn_export.setEnabled(False)
        except Exception:
            logging.exception("Failed to disable export button")

        # Helper to centralize finalization/cleanup of export state
        def _finalize_export(remove_temp=False):
            try:
                if getattr(self, "_export_file_handle", None):
                    try:
                        self._export_file_handle.close()
                    except Exception:
                        logging.exception("Failed closing export file")
                    self._export_file_handle = None
            except Exception:
                logging.exception("Error during export file finalize")
            try:
                try:
                    progress.close()
                except Exception:
                    logging.exception("Failed to close progress dialog")
            finally:
                try:
                    self._btn_export.setEnabled(True)
                except Exception:
                    logging.exception("Failed to re-enable export button")
                try:
                    self._export_in_progress = False
                except Exception:
                    logging.exception(
                        "Failed to clear _export_in_progress flag in finalize"
                    )
            if remove_temp and not saved_in_downloads:
                try:
                    os.remove(path)
                except Exception:
                    logging.exception("Failed to remove temporary export file")

        try:
            f = open(path, "w", newline="")
            # expose open file for cleanup during dialog close
            self._export_file_handle = f
            writer = csv.writer(f)
            headers = [g.label or f"IN{i + 1}" for i, g in enumerate(model.inputs)] + [
                model.led.label or "LED"
            ]
            writer.writerow(headers)
        except Exception as e:
            msg = str(e)
            logging.exception("Failed to open export file %s", path)
            _finalize_export(remove_temp=not saved_in_downloads)
            QTimer.singleShot(
                0,
                lambda: QMessageBox.warning(
                    self, "Export Failed", f"Export failed: {msg}"
                ),
            )
            return

        def _on_cancel():
            # Ignore cancel requests if we're already closing or not exporting
            if self._closing or not getattr(self, "_export_in_progress", False):
                return
            self._export_cancel_requested = True

        progress.canceled.connect(_on_cancel)

        def process_chunk():
            nonlocal idx
            try:
                # If dialog is closing, abort processing promptly
                if getattr(self, "_closing", False):
                    try:
                        if getattr(self, "_export_file_handle", None):
                            self._export_file_handle.close()
                    except Exception:
                        logging.exception(
                            "Failed closing export_file_handle during dialog close"
                        )
                    try:
                        self._export_in_progress = False
                    except Exception:
                        logging.exception(
                            "Failed clearing _export_in_progress flag during dialog close"
                        )
                    return

                limit = min(batch, total - idx)
                for _ in range(limit):
                    if getattr(self, "_export_cancel_requested", False):
                        break
                    # Prefer public accessor; get_row returns (bits, out_val, was_cached)
                    try:
                        bits, out_val, _ = model.get_row(idx)
                    except Exception:
                        # Fallback (robust): try internal method
                        try:
                            bits, out_val = model._ensure_cached(idx)
                        except Exception:
                            bits, out_val = [], False

                    writer.writerow(
                        ["1" if b else "0" for b in bits] + ["1" if out_val else "0"]
                    )
                    idx += 1

                try:
                    progress.setValue(idx)
                    try:
                        progress.setLabelText(f"Exporting CSV... ({idx}/{total})")
                    except Exception:
                        pass
                except Exception:
                    logging.exception("Failed updating progress")

                if idx < total and not getattr(self, "_export_cancel_requested", False):
                    QTimer.singleShot(0, process_chunk)
                    return

                # Done or cancelled
                try:
                    progress.canceled.disconnect(_on_cancel)
                except Exception:
                    logging.exception("Failed disconnecting cancel handler")

                if getattr(self, "_export_cancel_requested", False):
                    _finalize_export(remove_temp=not saved_in_downloads)
                    QTimer.singleShot(
                        0,
                        lambda: QMessageBox.information(
                            self, "Cancelled", "CSV export cancelled"
                        ),
                    )
                    return

                # Success: finalize but keep file
                _finalize_export(remove_temp=False)

                # Success: save stats and ask to open file on next tick
                try:
                    model._last_export_stats = {"total": total}
                except Exception:
                    logging.exception("Failed to set last_export_stats on model")
                # mark export finished, let _cleanup know state
                try:
                    self._export_in_progress = False
                    self._export_file_handle = None
                    self._exporting_path = path
                except Exception:
                    logging.exception("Failed to clear export flags after success")

                def _ask_open():
                    resp = QMessageBox.question(
                        self, "Exported", f"CSV exported to\n{Path(path)}\n\nOpen file?"
                    )
                    if resp == QMessageBox.Yes:
                        # 1. Linux Specific robust fallbacks FIRST (prevents Qt console warnings)
                        if platform.system() == "Linux":
                            # Detect WSL2
                            is_wsl = False
                            try:
                                if os.path.exists("/proc/version"):
                                    with open("/proc/version", "r") as f:
                                        if "microsoft" in f.read().lower():
                                            is_wsl = True
                            except Exception:
                                pass

                            # Try wslview first (best for WSL2 users)
                            try:
                                if (
                                    subprocess.call(
                                        ["which", "wslview"],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL,
                                    )
                                    == 0
                                ):
                                    subprocess.Popen(
                                        ["wslview", path],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL,
                                    )
                                    return
                            except Exception:
                                pass

                            # If on WSL and wslview failed, try powershell bridge to Windows host
                            if is_wsl:
                                try:
                                    # Convert Linux path to Windows path and launch via PS
                                    win_path = (
                                        subprocess.check_output(["wslpath", "-w", path])
                                        .decode()
                                        .strip()
                                    )
                                    subprocess.Popen(
                                        [
                                            "powershell.exe",
                                            "-Command",
                                            f"Start-Process '{win_path}'",
                                        ],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL,
                                    )
                                    return
                                except Exception:
                                    pass

                            # Try explicit xdg-open (fallback for native Linux desktop)
                            try:
                                if (
                                    subprocess.call(
                                        ["which", "xdg-open"],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL,
                                    )
                                    == 0
                                ):
                                    subprocess.Popen(
                                        ["xdg-open", path],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL,
                                    )
                                    return
                            except Exception:
                                pass

                        # 2. Try standard Qt service (works on Windows/Native Desktop Linux)
                        try:
                            if QDesktopServices.openUrl(QUrl.fromLocalFile(path)):
                                return
                        except Exception:
                            pass

                        # 3. Windows Specific fallback
                        try:
                            if hasattr(os, "startfile"):
                                os.startfile(path)
                                return
                        except Exception:
                            pass

                        QMessageBox.warning(
                            self,
                            "Open Failed",
                            "Unable to open CSV file.\nPlease open it manually from:\n"
                            + path,
                        )
                    else:
                        if not saved_in_downloads:
                            self._temp_csv = path
                        else:
                            self._exported_path = path

                QTimer.singleShot(0, _ask_open)
            except Exception as e:
                msg = str(e)
                logging.exception("Exception during export: %s", msg)
                _finalize_export(remove_temp=not saved_in_downloads)
                QTimer.singleShot(
                    0,
                    lambda: QMessageBox.warning(
                        self, "Export Failed", f"Export failed: {msg}"
                    ),
                )

        # Kick off chunked processing
        QTimer.singleShot(0, process_chunk)

    def _cleanup(self):
        """Free large in-memory data and Qt widgets to release memory when dialog closes."""
        # No in-memory rows are stored; nothing to clear here.

        try:
            if hasattr(self, "table"):
                try:
                    # Detach model and delete the view (QTableView cleanup)
                    try:
                        self.table.setModel(None)
                    except Exception:
                        logging.exception("Failed to detach model from table")
                    try:
                        self.table.deleteLater()
                    except Exception:
                        logging.exception("Failed to delete table view")
                except Exception:
                    logging.exception("Error during table teardown")
                try:
                    del self.table
                except Exception:
                    logging.exception("Failed to delete table attribute")
        except Exception:
            logging.exception("Unexpected error while tearing down table")

        # If an export is active when the dialog is closing, request cancellation
        try:
            self._closing = True
            if getattr(self, "_export_in_progress", False):
                try:
                    self._export_cancel_requested = True
                except Exception:
                    logging.exception(
                        "Failed to set export_cancel_requested during cleanup"
                    )
                try:
                    if getattr(self, "_export_file_handle", None):
                        try:
                            self._export_file_handle.close()
                        except Exception:
                            logging.exception(
                                "Failed to close export file handle during cleanup"
                            )
                        self._export_file_handle = None
                except Exception:
                    logging.exception(
                        "Error while closing export file handle during cleanup"
                    )
                try:
                    # If exported path looks like a temp file (not in Downloads), remove it
                    p = Path(self._exporting_path) if self._exporting_path else None
                    if p and p.exists() and p.parent.name.lower() != "downloads":
                        try:
                            p.unlink()
                        except Exception:
                            logging.exception(
                                "Failed to unlink temporary exported file during cleanup"
                            )
                except Exception:
                    logging.exception(
                        "Error while removing temporary exported file during cleanup"
                    )
        except Exception:
            pass

        try:
            # Also delete any temporary CSV we created
            if getattr(self, "_temp_csv", None):
                try:
                    os.remove(self._temp_csv)
                except Exception:
                    logging.exception("Failed to remove temp_csv during cleanup")
                self._temp_csv = None
        except Exception:
            logging.exception("Error while cleaning up temp_csv")

        try:
            # Allow Qt to process any pending events/deferred deletions
            try:
                QCoreApplication.processEvents()
            except Exception:
                logging.exception("Failed during QCoreApplication.processEvents()")

            gc.collect()
        except Exception:
            logging.exception("Error during final GC in cleanup")

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
