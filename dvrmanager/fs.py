import re
import sys
from pathlib import Path
from typing import Tuple


class FSManager:
    def drive_exists(self, drive_name: str) -> bool:
        raise NotImplementedError()

    def drive_path(self, drive_name: str) -> bool:
        raise NotImplementedError()

    def find_matches(self, drive_name: str, drive_path: Path) -> Tuple[Path, ...]:
        raise NotImplementedError()

    def unmount(self, drive_name: str):
        raise NotImplementedError()


class WinFS(FSManager):
    def drive_path(self, drive_name: str) -> Path:
        if re.match(r'^[a-zA-Z]$', drive_name):
            return Path(f'{drive_name}:/')
        if re.match(r'^[a-zA-Z]:$', drive_name):
            return Path(f'{drive_name}/')
        return Path('/') / drive_name

    def drive_exists(self, drive_name: str) -> bool:
        return self.drive_path(drive_name).exists()

    def find_matches(self, drive_name: str, drive_path: Path) -> Tuple[Path, ...]:
        drive = self.drive_path(drive_name)
        return tuple(drive.rglob(str(drive_path)))

    def unmount(self, drive_name: str):
        pass


def get_fs_manager() -> FSManager:
    if sys.platform == 'win32':
        return WinFS()
