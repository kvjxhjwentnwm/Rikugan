"""Context bar: shows current address, function, model, and token count."""

from __future__ import annotations

import importlib

from .qt_compat import (
    QFrame, QHBoxLayout, QLabel, QWidget, QTimer,
)

try:
    ida_funcs = importlib.import_module("ida_funcs")
    ida_name = importlib.import_module("ida_name")
    idc = importlib.import_module("idc")
except ImportError:
    ida_funcs = ida_name = idc = None  # type: ignore[assignment]  # noqa: N816 — outside IDA


class ContextBar(QFrame):
    """Status bar showing current binary context and session info."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setObjectName("context_bar")
        self.setFixedHeight(28)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(16)

        self._address_label = self._make_pair("Addr:", "—")
        self._function_label = self._make_pair("Func:", "—")
        self._model_label = self._make_pair("Model:", "—")
        self._tokens_label = self._make_pair("Tokens:", "0")

        for label, value in (self._address_label, self._function_label,
                             self._model_label, self._tokens_label):
            layout.addWidget(label)
            layout.addWidget(value)

        layout.addStretch()

        self._stopped = False

        # Auto-update cursor position
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_cursor)
        self._timer.start(2000)

    def _make_pair(self, label_text: str, initial: str):
        label = QLabel(label_text)
        label.setObjectName("context_label")
        value = QLabel(initial)
        value.setObjectName("context_value")
        return label, value

    def stop(self) -> None:
        """Stop the auto-update timer. Call before destruction."""
        self._stopped = True
        try:
            self._timer.stop()
            self._timer.timeout.disconnect(self._update_cursor)
        except (RuntimeError, TypeError):
            pass  # timer already destroyed during Qt cleanup

    def set_address(self, addr: str) -> None:
        self._address_label[1].setText(addr)

    def set_function(self, name: str) -> None:
        self._function_label[1].setText(name if len(name) < 30 else name[:27] + "...")

    def set_model(self, model: str) -> None:
        self._model_label[1].setText(model)

    def set_tokens(self, count: int) -> None:
        if count >= 1000:
            self._tokens_label[1].setText(f"{count / 1000:.1f}k")
        else:
            self._tokens_label[1].setText(str(count))

    def _update_cursor(self) -> None:
        if self._stopped:
            return
        try:
            ea = idc.get_screen_ea()
            self.set_address(f"0x{ea:x}")

            func = ida_funcs.get_func(ea)
            if func:
                name = ida_name.get_name(func.start_ea)
                self.set_function(name)
            else:
                self.set_function("—")
        except Exception:
            pass  # IDA API not available or internal error; timer keeps ticking safely
