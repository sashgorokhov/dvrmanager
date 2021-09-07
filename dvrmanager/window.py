from pathlib import Path
from typing import Callable

from PyQt6 import QtCore
from PyQt6.QtWidgets import QMainWindow, QApplication, QVBoxLayout, QWidget, QLabel, QLineEdit, QHBoxLayout, \
    QSpacerItem, QSizePolicy, QCheckBox, QPushButton

from dvrmanager.settings import Settings, ExportItem


class ExportItemWidget(QWidget):
    on_settings_changed = QtCore.pyqtSignal()
    on_export_item_removed = QtCore.pyqtSignal('QObject', ExportItem)

    def __init__(self, export_item: ExportItem):
        self._export_item = export_item

        super(ExportItemWidget, self).__init__()

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self.add_drive_name()
        self.add_drive_path()
        self.add_delete()
        self.add_unmount()

        self.remove_button = QPushButton('Remove', self)
        self.remove_button.clicked.connect(self.on_removed)
        self._layout.addWidget(self.remove_button)

    @QtCore.pyqtSlot()
    def on_removed(self):
        self.on_export_item_removed.emit(self, self._export_item)

    def add_drive_name(self):
        def on_change(text: str):
            self._export_item.drive_name = text
            self.on_settings_changed.emit()

        self.add_edit_item('Drive name:', self._export_item.drive_name, on_change)

    def add_drive_path(self):
        def on_change(text: str):
            self._export_item.drive_path = Path(text)
            self.on_settings_changed.emit()

        self.add_edit_item('Drive path:', str(self._export_item.drive_path or ''), on_change)

    def add_delete(self):
        def on_change(flag: bool):
            self._export_item.delete = flag
            self.on_settings_changed.emit()

        self.add_toggle_item('Delete copied files', self._export_item.delete, on_change)

    def add_unmount(self):
        def on_change(flag: bool):
            self._export_item.unmount = flag
            self.on_settings_changed.emit()

        self.add_toggle_item('Unmount drive', self._export_item.unmount, on_change)

    def add_edit_item(self, label: str, edit_text: str, on_change: Callable[[str], None]):
        layout = QHBoxLayout()
        edit = QLineEdit(edit_text, self)
        edit.textChanged.connect(on_change)
        label = QLabel(label, self)
        layout.addWidget(label)
        layout.addSpacerItem(QSpacerItem(10, 0))
        layout.addWidget(edit)
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self._layout.addItem(layout)

    def add_toggle_item(self, label: str, flag: bool, on_change: Callable[[bool], None]):
        layout = QHBoxLayout()
        toggle = QCheckBox(self)
        toggle.setChecked(flag)
        toggle.toggled.connect(on_change)
        toggle.setText(label)
        layout.addWidget(toggle)
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self._layout.addItem(layout)


class MainWindow(QMainWindow):
    on_settings_changed = QtCore.pyqtSignal()

    def __init__(self, app: QApplication, settings: Settings):
        self._app = app
        self.settings = settings

        super(MainWindow, self).__init__()

        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)

        self.export_items_list_layout = QVBoxLayout(self.centralwidget)
        # self.export_items_list_layout.addStretch(1)
        self.centralwidget.setLayout(self.export_items_list_layout)

        self.add_export_item_button = QPushButton('Add', self)
        self.add_export_item_button.clicked.connect(self.add_new_export_item)
        self.export_items_list_layout.addStretch(1)
        self.export_items_list_layout.addWidget(self.add_export_item_button)
        self.export_items_list_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        for export_item in self.settings.export_items:
            self.add_export_item(export_item)

        self.on_settings_changed.connect(self.settings_changed)

    @QtCore.pyqtSlot()
    def settings_changed(self):
        self.settings.save()

    @QtCore.pyqtSlot('QObject', ExportItem)
    def on_export_item_removed(self, export_item_widget: ExportItemWidget, export_item: ExportItem):
        self.export_items_list_layout.removeWidget(export_item_widget)
        export_item_widget.setParent(None)
        export_item_widget.deleteLater()
        # export_item_widget.setVisible(False)
        self.settings.export_items = tuple(i for i in self.settings.export_items if i is not export_item)
        self.on_settings_changed.emit()

    @QtCore.pyqtSlot()
    def add_new_export_item(self):
        new_export_item = ExportItem.create_default()
        self.settings.export_items = list(self.settings.export_items) + [new_export_item]
        self.on_settings_changed.emit()
        self.add_export_item(new_export_item)

    def add_export_item(self, export_item: ExportItem):
        export_item_widget = ExportItemWidget(export_item)
        export_item_widget.on_settings_changed.connect(self.on_settings_changed)
        export_item_widget.on_export_item_removed.connect(self.on_export_item_removed)
        i = self.export_items_list_layout.indexOf(self.add_export_item_button)
        self.export_items_list_layout.insertWidget(i - 1, export_item_widget)

    def closeEvent(self, *args, **kwargs):
        """Terminate application if main window closed"""
        self._app.quit()
