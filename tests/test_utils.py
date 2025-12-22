"""Tests for simulator/utils.py - Utilities, UID generation, resource paths, class maps."""

import logging
import sys
import tempfile
import uuid
from pathlib import Path

from simulator.utils import (
    ANNOTATION_CLASS_MAP,
    CLASS_MAP,
    ensure_uid,
    ensure_uids_for_all,
    get_resource_path,
    setup_logging,
)


class TestClassMaps:
    """Test that class maps contain all expected gate types."""

    def test_class_map_contains_basic_gates(self):
        """CLASS_MAP should contain all basic logic gates."""
        expected = [
            "ANDGate",
            "ORGate",
            "NOTGate",
            "XORGate",
            "NANDGate",
            "NORGate",
            "XNORGate",
        ]
        for name in expected:
            assert name in CLASS_MAP, f"Missing {name} in CLASS_MAP"

    def test_class_map_contains_advanced_gates(self):
        """CLASS_MAP should contain advanced components."""
        expected = ["Multiplexer", "Demultiplexer", "Encoder", "Decoder"]
        for name in expected:
            assert name in CLASS_MAP, f"Missing {name} in CLASS_MAP"

    def test_class_map_contains_io(self):
        """CLASS_MAP should contain I/O components."""
        assert "InputSwitch" in CLASS_MAP
        assert "OutputLED" in CLASS_MAP

    def test_annotation_class_map(self):
        """ANNOTATION_CLASS_MAP should contain all annotation types."""
        expected = ["TextAnnotation", "RectangleAnnotation", "CircleAnnotation"]
        for name in expected:
            assert name in ANNOTATION_CLASS_MAP, (
                f"Missing {name} in ANNOTATION_CLASS_MAP"
            )

    def test_class_map_values_are_classes(self):
        """All values in CLASS_MAP should be actual classes."""
        for name, cls in CLASS_MAP.items():
            assert isinstance(cls, type), f"{name} is not a class"

    def test_annotation_class_map_values_are_classes(self):
        """All values in ANNOTATION_CLASS_MAP should be actual classes."""
        for name, cls in ANNOTATION_CLASS_MAP.items():
            assert isinstance(cls, type), f"{name} is not a class"


class TestEnsureUid:
    """Test UID generation utilities."""

    def test_ensure_uid_creates_uid_if_missing(self):
        """ensure_uid should create a uid if object doesn't have one."""

        class MockObj:
            pass

        obj = MockObj()
        result = ensure_uid(obj)

        assert hasattr(obj, "uid")
        assert obj.uid is not None
        assert result == obj.uid
        # Should be a valid UUID string
        uuid.UUID(result)

    def test_ensure_uid_preserves_existing_uid(self):
        """ensure_uid should not overwrite existing uid."""

        class MockObj:
            uid = "existing-uid-12345"

        obj = MockObj()
        result = ensure_uid(obj)

        assert result == "existing-uid-12345"
        assert obj.uid == "existing-uid-12345"

    def test_ensure_uid_handles_none_uid(self):
        """ensure_uid should replace None uid with a new one."""

        class MockObj:
            uid = None

        obj = MockObj()
        result = ensure_uid(obj)

        assert result is not None
        assert obj.uid is not None


class TestEnsureUidsForAll:
    """Test bulk UID assignment."""

    def test_ensure_uids_for_all_assigns_to_gates_and_annotations(self):
        """Should assign uids to all gates and annotations."""

        class MockGate:
            pass

        class MockAnnotation:
            pass

        gates = [MockGate(), MockGate()]
        annotations = [MockAnnotation()]

        ensure_uids_for_all(gates, annotations)

        for g in gates:
            assert hasattr(g, "uid")
            assert g.uid is not None
        for a in annotations:
            assert hasattr(a, "uid")
            assert a.uid is not None

    def test_ensure_uids_for_all_empty_lists(self):
        """Should handle empty lists without error."""
        ensure_uids_for_all([], [])  # Should not raise


class TestGetResourcePath:
    """Test resource path resolution for different environments."""

    def test_get_resource_path_development(self):
        """In development, should resolve relative to project root."""
        # Clear any PyInstaller marker
        if hasattr(sys, "_MEIPASS"):
            delattr(sys, "_MEIPASS")

        result = get_resource_path("assets/icon.ico")

        # Should be a Path object
        assert isinstance(result, Path)
        # Should end with the relative path
        assert str(result).endswith("assets/icon.ico".replace("/", "\\")) or str(
            result
        ).endswith("assets/icon.ico")

    def test_get_resource_path_pyinstaller(self):
        """In PyInstaller bundle, should use _MEIPASS."""
        # Temporarily add _MEIPASS to sys
        sys._MEIPASS = "/tmp/pyinstaller_bundle"
        try:
            result = get_resource_path("assets/icon.ico")
            assert result == Path("/tmp/pyinstaller_bundle/assets/icon.ico")
        finally:
            # Clean up
            del sys._MEIPASS


class TestSetupLogging:
    """Test logging configuration."""

    def test_setup_logging_creates_file(self):
        """setup_logging should create a log file and log to it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_session.log"

            # Clear existing handlers
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
                handler.close()

            # Reset basicConfig state
            root_logger.setLevel(logging.NOTSET)

            setup_logging(log_file)

            # Force flush
            for handler in root_logger.handlers:
                handler.flush()

            # Verify file was created and has content
            assert log_file.exists(), "Log file should be created"
            content = log_file.read_text()
            assert len(content) > 0, "Log file should have content"

            # Cleanup
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
                handler.close()
