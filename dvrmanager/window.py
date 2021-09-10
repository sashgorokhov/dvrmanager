import datetime
import logging
import shutil
import time
from pathlib import Path
from typing import Dict, Iterable, Tuple

import pydantic
from PyQt6 import QtCore
from PyQt6.QtCore import QTimer, QObject, QRunnable, QThread

from dvrmanager.fs import get_fs_manager
from dvrmanager.ui.main_window import MainWindowBase

logger = logging.getLogger(__name__)


class BaseJob(QObject):
    finished = QtCore.pyqtSignal()

    def run(self):
        raise NotImplementedError()


class MoveFilesJob(BaseJob):
    file_done = QtCore.pyqtSignal(Path)
    progress_str = QtCore.pyqtSignal(str)

    def __init__(self, files: Tuple[Tuple[Path, Path], ...]):
        self._files = files
        super(MoveFilesJob, self).__init__()

    def run(self):
        """Long-running task."""
        try:
            fs = get_fs_manager()

            for file_from, file_to in self._files:
                file_to.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src=file_from, dst=file_to)
                self.progress_str.emit(f'{file_from} -> {file_to}')
                self.file_done.emit(file_from)

            self.finished.emit()
        except:
            logger.exception('run')


class MainWindow(MainWindowBase):
    drive_attached = QtCore.pyqtSignal(str)
    drive_detached = QtCore.pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self._drive_scan_timer = QTimer(self)
        self._drive_scan_timer.timeout.connect(self.scan_drives)
        self._drive_scan_timer.start(1000)

        self._drive_state: Dict[str, bool] = {}

        self.drive_attached.connect(self.find_matches)

        self._fs = get_fs_manager()

    def find_matches(self, drive_name: str):
        try:
            for export_item in self._settings.export_items:
                if export_item.drive_name == drive_name:
                    drive_path = export_item.drive_path
                    break
            else:
                return

            matches = self._fs.find_matches(drive_name, drive_path)
            self.add_ui_log_entry(f'Drive {drive_name} has {len(matches)} matched files by {drive_path}')

            file_move = []
            for file_from in matches:
                file_move.append((file_from, Path(self._settings.target_directory) / datetime.date.today().isoformat() / (self.export_label_edit.text().strip() or 'default') / drive_name / file_from.name))

            job = MoveFilesJob(tuple(file_move))
            job.progress_str.connect(self.add_ui_log_entry)
            job.finished.connect(lambda: self._fs.unmount(drive_name))
            self._thread_pool.start(job.run)
        except:
            logger.exception('find_matches')

    def scan_drives(self):
        try:
            new_state = {}
            for export_item in self._settings.export_items:
                if not export_item.automatic:
                    continue
                new_state[export_item.drive_name] = self._fs.drive_exists(export_item.drive_name)

            for drive, attached in new_state.items():
                if attached and not self._drive_state.get(drive, False):
                    self.drive_attached.emit(drive)
                    logger.info(f'Detected drive attach: {drive}')
                    self.add_ui_log_entry(f'Drive attached: {drive}')
                elif not attached and self._drive_state.get(drive, False):
                    self.drive_detached.emit(drive)
                    logger.info(f'Detected drive detach: {drive}')
                    self.add_ui_log_entry(f'Drive detached: {drive}')

            self._drive_state.update(new_state)
        except:
            logger.exception('scan_drives')
