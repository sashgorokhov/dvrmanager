import logging
from pathlib import Path

from PyQt6 import QtCore
from PyQt6.QtCore import QThreadPool, QThread
from PyQt6.QtWidgets import QMainWindow, QApplication

from dvrmanager import logs
from dvrmanager.settings import ExportItem, Settings
from dvrmanager.ui.export_item_widget import ExportItemWidget
from dvrmanager.ui.main_window_form import Ui_MainWindow

logger = logging.getLogger(__name__)


class MainWindowBase(Ui_MainWindow, QMainWindow):
    settings_changed = QtCore.pyqtSignal()

    def __init__(self, app: QApplication, settings: Settings):
        self._settings = settings
        self._app = app

        super(MainWindowBase, self).__init__()

        self.setupUi()
        self.load_settings_export_items()
        self.setup_statusbar_logging()
        self.setup_threads()

    def setup_threads(self):
        self._thread_pool = QThreadPool.globalInstance()
        logger.debug(f'Thread pool size: {QThread.idealThreadCount()}')

    def load_settings_export_items(self):
        for export_item in self._settings.export_items:
            self.add_export_item(export_item)

    # noinspection PyMethodOverriding
    def setupUi(self):
        super(MainWindowBase, self).setupUi(self)
        self.add_export_item_button.clicked.connect(self.add_new_export_item)
        self.settings_changed.connect(self.on_settings_changed)

        # self.target_directory_edit.setReadOnly(True)
        self.target_directory_edit.setText(str(self._settings.target_directory))
        self.target_directory_edit.textChanged.connect(self._link_text_setting('target_directory', Path))

    @QtCore.pyqtSlot(str)
    def add_ui_log_entry(self, text):
        self.log_list_widget.insertItem(0, text)

    def _link_text_setting(self, key: str, ttype: type = str):
        def slot(value):
            setattr(self._settings, key, ttype(value))
            self.settings_changed.emit()

        return slot

    def on_settings_changed(self):
        logger.info('Settings saved')
        logger.debug(self._settings.json())
        self._settings.save()

    def remove_export_item(self, export_item_widget: ExportItemWidget, export_item: ExportItem):
        self.export_items_layout.removeWidget(export_item_widget)
        # noinspection PyTypeChecker
        export_item_widget.setParent(None)
        export_item_widget.deleteLater()
        self._settings.export_items = tuple(i for i in self._settings.export_items if i is not export_item)
        self.settings_changed.emit()

    def add_export_item(self, export_item: ExportItem = None):
        export_item_widget = ExportItemWidget(export_item)
        export_item_widget.setParent(self)
        export_item_widget.settings_changed.connect(self.settings_changed)
        export_item_widget.export_item_removed.connect(self.remove_export_item)

        i = self.export_items_layout.indexOf(self.add_export_item_button)
        self.export_items_layout.insertWidget(i - 1, export_item_widget)

    def add_new_export_item(self):
        new_export_item = ExportItem.create_default()
        self._settings.export_items = list(self._settings.export_items) + [new_export_item]
        self.settings_changed.emit()
        self.add_export_item(new_export_item)

    def closeEvent(self, *args, **kwargs):
        """Terminate application if main window closed"""
        self._app.quit()
        self._thread_pool.waitForDone()

    def setup_statusbar_logging(self):
        logger = logging.getLogger('dvrmanager')
        handler = logs.StatusBarHandler(self.statusBar())
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
