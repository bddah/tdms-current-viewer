from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QProgressDialog


def show_error(parent, title, message):
    QMessageBox.critical(parent, title, message)


def show_info(parent, title, message):
    QMessageBox.information(parent, title, message)


class ProgressDialog(QProgressDialog):
    def __init__(self, parent=None, title="Working", label_text="Please wait...", minimum=0, maximum=100):
        super().__init__(label_text, None, minimum, maximum, parent)
        self.setWindowTitle(title)
        self.setWindowModality(Qt.WindowModal)
        self.setAutoClose(False)
        self.setAutoReset(False)
        self.setMinimumDuration(0)
        self.setCancelButton(None)

    def __enter__(self):
        self.show()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False
