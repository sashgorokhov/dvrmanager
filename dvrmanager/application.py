import contextlib

from PyQt6.QtWidgets import QApplication

from dvrmanager import config


@contextlib.contextmanager
def application() -> QApplication:
    app = QApplication([])
    app.setApplicationName(config.APP_NAME)
    yield app
    app.exec()
