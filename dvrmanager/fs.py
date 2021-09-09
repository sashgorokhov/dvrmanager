import re
import sys
from pathlib import Path


class FSManager:
    def drive_exists(self, drive_name: str) -> bool:
        raise NotImplementedError()

    def drive_path(self, drive_name: str) -> bool:
        raise NotImplementedError()


class WinFS(FSManager):
    def drive_path(self, drive_name: str) -> Path:
        if re.match('[a-zA-Z]', drive_name):
            return Path(f'{drive_name}:/')
        if re.match('[a-zA-Z]:', drive_name):
            return Path(f'{drive_name}/')
        return Path(drive_name)

    def drive_exists(self, drive_name: str) -> bool:
        return self.drive_path(drive_name).exists()


def get_fs_manager() -> FSManager:
    if sys.platform == 'win32':
        return WinFS()
