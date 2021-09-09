import logging
from pathlib import Path
from typing import Dict

from PyQt6 import QtCore
from PyQt6.QtCore import QThread, QThreadPool, QTimer
from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget, QLineEdit, QCheckBox

from dvrmanager import logs
from dvrmanager.fs import get_fs_manager
from dvrmanager.settings import Settings, ExportItem
from dvrmanager.ui.export_item_widget import Ui_Form
from dvrmanager.ui.window import Ui_MainWindow

logger = logging.getLogger(__name__)


class ExportItemWidget(Ui_Form, QWidget):
    settings_changed = QtCore.pyqtSignal()
    export_item_removed = QtCore.pyqtSignal('QObject', ExportItem)

    def __init__(self, export_item: ExportItem):
        self._export_item = export_item

        super(ExportItemWidget, self).__init__()

        self.setupUi()

    # noinspection PyMethodOverriding
    def setupUi(self):
        super(ExportItemWidget, self).setupUi(self)

        self.export_item_group_box.toggled.connect(lambda state: self.export_item_removed.emit(self, self._export_item))

        self._link_text_setting(self.drive_name_edit, 'drive_name')
        self._link_text_setting(self.drive_path_edit, 'drive_path', Path)
        self._link_bool_setting(self.delete_checkbox, 'delete')
        self._link_bool_setting(self.unmount_checkbox, 'unmount')
        self._link_bool_setting(self.automatic_checkbox, 'automatic')

        self.automatic_checkbox.toggled.connect(self.run_button.setDisabled)
        self.run_button.setDisabled(self.automatic_checkbox.isChecked())

    def _link_text_setting(self, edit_widget: QLineEdit, key: str, ttype: type = str):
        def slot(value):
            try:
                setattr(self._export_item, key, ttype(value))
                self.settings_changed.emit()
            except:
                logger.exception(f'Error saving setting {edit_widget.objectName()} {key} {ttype} {value}')

        edit_widget.setText(str(getattr(self._export_item, key)))
        edit_widget.textChanged.connect(slot)

    def _link_bool_setting(self, checkbox_widget: QCheckBox, key: str):
        def slot(value):
            try:
                setattr(self._export_item, key, value)
                self.settings_changed.emit()
            except:
                logger.exception(f'Error saving setting {checkbox_widget.objectName()} {key} {value}')

        checkbox_widget.setChecked(getattr(self._export_item, key))
        checkbox_widget.toggled.connect(slot)


class MainWindow(Ui_MainWindow, QMainWindow):
    settings_changed = QtCore.pyqtSignal()
    drive_attached = QtCore.pyqtSignal(str)
    drive_detached = QtCore.pyqtSignal(str)

    def __init__(self, app: QApplication, settings: Settings):
        self._app = app
        self._settings = settings
        self._fs = get_fs_manager()
        logger.debug(f'Using {self._fs.__class__.__name__}')

        super(MainWindow, self).__init__()

        self.setupUi()
        self.load_settings_export_items()
        self.setup_statusbar_logging()
        self.setup_threads()

        self._drive_scan_timer = QTimer(self)
        self._drive_scan_timer.timeout.connect(self.scan_drives)
        self._drive_scan_timer.start(1000)

        self._drive_state: Dict[str, bool] = {}

    def scan_drives(self):
        new_state = {}
        for export_item in self._settings.export_items:
            if not export_item.automatic:
                continue
            new_state[export_item.drive_name] = self._fs.drive_exists(export_item.drive_name)

        for drive, attached in new_state.items():
            if attached and not self._drive_state.get(drive, False):
                self.drive_attached.emit(drive)
                self.add_ui_log_entry(f'Drive attached: {drive}')
            elif not attached and self._drive_state.get(drive, False):
                self.drive_detached.emit(drive)
                self.add_ui_log_entry(f'Drive detached: {drive}')

        self._drive_state.update(new_state)

    def setup_threads(self):
        self._thread_pool = QThreadPool.globalInstance()
        logger.debug(f'Thread pool size: {QThread.idealThreadCount()}')

    def load_settings_export_items(self):
        for export_item in self._settings.export_items:
            self.add_export_item(export_item)

    # noinspection PyMethodOverriding
    def setupUi(self):
        super(MainWindow, self).setupUi(self)
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

    def add_new_export_item(self):
        new_export_item = ExportItem.create_default()
        self._settings.export_items = list(self._settings.export_items) + [new_export_item]
        self.settings_changed.emit()
        self.add_export_item(new_export_item)

    def add_export_item(self, export_item: ExportItem = None):
        export_item_widget = ExportItemWidget(export_item)
        export_item_widget.setParent(self)
        export_item_widget.settings_changed.connect(self.settings_changed)
        export_item_widget.export_item_removed.connect(self.remove_export_item)

        i = self.export_items_layout.indexOf(self.add_export_item_button)
        self.export_items_layout.insertWidget(i - 1, export_item_widget)

    def remove_export_item(self, export_item_widget: ExportItemWidget, export_item: ExportItem):
        self.export_items_layout.removeWidget(export_item_widget)
        # noinspection PyTypeChecker
        export_item_widget.setParent(None)
        export_item_widget.deleteLater()
        self._settings.export_items = tuple(i for i in self._settings.export_items if i is not export_item)
        self.settings_changed.emit()

    def closeEvent(self, *args, **kwargs):
        """Terminate application if main window closed"""
        self._app.quit()
        self._thread_pool.waitForDone()

    def setup_statusbar_logging(self):
        logger = logging.getLogger('dvrmanager')
        handler = logs.StatusBarHandler(self.statusBar())
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
