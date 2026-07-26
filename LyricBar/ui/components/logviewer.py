"""In-app log viewer -- replaces the old OS-console "debug console" feature.

Why this exists instead of AllocConsole():
Windows' own docs are explicit that a registered console control handler
returning TRUE for CTRL_CLOSE_EVENT does NOT prevent the process from being
terminated -- it just skips any other handlers. There's no supported way to
survive your own console window being closed once your process is attached
to it. A normal Qt dialog has none of that baggage: closing it is a regular
widget event we fully control, so "closing the console shouldn't close the
bar" is true by construction instead of something we have to fight the OS
for.
"""
import logging

from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QIcon, QTextCursor
from PyQt5.QtWidgets import QDialog, QPlainTextEdit, QVBoxLayout

from LyricBar.config import resource_path

MAX_LOG_LINES = 2000  # cap so a long-running session doesn't grow this unbounded


class _QtLogSignal(QObject):
    # logging can be called from worker threads (QThread subclasses elsewhere
    # in the app); Qt widgets may only be touched from the GUI thread. Routing
    # through a signal/slot marshals the append back onto the main thread.
    new_line = pyqtSignal(str)


class QtLogHandler(logging.Handler):
    """A logging.Handler that forwards formatted records into a QPlainTextEdit."""

    def __init__(self, text_edit: QPlainTextEdit):
        super().__init__()
        self.text_edit = text_edit
        self._bridge = _QtLogSignal()
        self._bridge.new_line.connect(self._append, Qt.QueuedConnection)

    def emit(self, record):
        try:
            message = self.format(record)
        except Exception:
            message = record.getMessage()
        self._bridge.new_line.emit(message)

    def _append(self, message: str):
        self.text_edit.appendPlainText(message)
        if self.text_edit.blockCount() > MAX_LOG_LINES:
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(
                QTextCursor.Down, QTextCursor.KeepAnchor, self.text_edit.blockCount() - MAX_LOG_LINES
            )
            cursor.removeSelectedText()
        self.text_edit.moveCursor(QTextCursor.End)


class LogViewerDialog(QDialog):
    """A non-modal, hide-on-close log window. Created once and reused --
    closing it just hides it, it never tears down the QApplication."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LyricBar Debug Console")
        self.setWindowIcon(QIcon(resource_path("resources/icon.ico")))
        self.resize(800, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumBlockCount(MAX_LOG_LINES)
        self.text_edit.setStyleSheet(
            """
            QPlainTextEdit {
                background: #0b0b0e;
                color: #d8d8d8;
                font-family: "Cascadia Mono", "Consolas", monospace;
                font-size: 9.5pt;
                border: 1px solid #2d2d36;
                border-radius: 6px;
            }
            """
        )
        layout.addWidget(self.text_edit)

        self.handler = QtLogHandler(self.text_edit)
        self.handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))
        self.handler.setLevel(logging.DEBUG)

    def closeEvent(self, event):
        # Hide instead of closing/destroying -- this window's lifecycle is
        # independent of the console concept entirely; there's nothing here
        # that can take the rest of the app down with it.
        event.ignore()
        self.hide()

    def attach(self):
        logging.getLogger().addHandler(self.handler)

    def detach(self):
        logging.getLogger().removeHandler(self.handler)
