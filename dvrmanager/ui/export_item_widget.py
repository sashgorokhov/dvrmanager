import logging
from pathlib import Path

from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget, QLineEdit, QCheckBox

from dvrmanager.settings import ExportItem
from dvrmanager.ui.export_item_widget_form import Ui_Form

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
