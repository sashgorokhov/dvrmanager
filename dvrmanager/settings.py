from pathlib import Path
from typing import Tuple, Optional

from pydantic import BaseModel

from dvrmanager import config


class ExportItem(BaseModel):
    drive_name: str
    drive_path: Optional[Path] = None

    delete: bool = True
    unmount: bool = True

    @classmethod
    def create_default(cls) -> 'ExportItem':
        return ExportItem(
            drive_name='DVR_FLASHDRIVE',
            drive_path=Path('DCIM/*.avi'),
            delete=True,
            unmount=True,
        )


class Settings(BaseModel):
    export_items: Tuple[ExportItem, ...]

    @classmethod
    def create_default(cls) -> 'Settings':
        return Settings(
            export_items=(ExportItem.create_default(),)
        )

    @classmethod
    def load(cls) -> 'Settings':
        if cls.path().exists():
            settings = cls.parse_file(cls.path())
        else:
            settings = cls.create_default()
            settings.save()

        return settings

    def save(self):
        self.path().parent.mkdir(parents=True, exist_ok=True)
        self.path().write_text(self.json())

    @staticmethod
    def path() -> Path:
        return config.SETTINGS_DIR / 'settings.json'
