"""Tests for rikugan.ui.qt_compat — Qt compatibility shim."""

from __future__ import annotations

from pathlib import Path
import unittest

from tests.qt_stubs import ensure_pyside6_stubs

ensure_pyside6_stubs()
import rikugan.ui.qt_compat as qt_compat  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[1]
_UI_FILES_WITHOUT_SHIMS = {
    "rikugan/ui/agent_tree.py",
    "rikugan/ui/bulk_renamer.py",
    "rikugan/ui/message_widgets.py",
    "rikugan/ui/panel_core.py",
    "rikugan/ui/settings_dialog.py",
    "rikugan/ui/tool_widgets.py",
}


class TestQtCompat(unittest.TestCase):
    def test_is_pyside6_returns_true(self):
        self.assertTrue(qt_compat.is_pyside6())

    def test_qt_binding_constant(self):
        self.assertEqual(qt_compat.QT_BINDING, "PySide6")

    def test_qt_core_symbols_exported(self):
        for name in ("Signal", "Qt", "QObject", "QTimer"):
            self.assertTrue(hasattr(qt_compat, name), f"missing {name}")
        self.assertTrue(qt_compat.is_pyside6())

    def test_qt_widget_symbols_exported(self):
        for name in (
            "QApplication", "QWidget", "QVBoxLayout", "QHBoxLayout",
            "QLabel", "QPushButton", "QPlainTextEdit", "QScrollArea",
            "QDialog", "QComboBox", "QLineEdit", "QCheckBox",
            "QMenu", "QMessageBox",
        ):
            self.assertTrue(hasattr(qt_compat, name), f"missing {name}")

    def test_target_ui_files_do_not_use_exec_legacy_or_qt_flag_bitwise_or(self):
        offenders: list[str] = []
        for relative_path in sorted(_UI_FILES_WITHOUT_SHIMS):
            text = (_REPO_ROOT / relative_path).read_text()
            for line_no, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                if "exec_(" in stripped or ("Qt." in stripped and "|" in stripped):
                    offenders.append(f"{relative_path}:{line_no}:{stripped}")
        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()
