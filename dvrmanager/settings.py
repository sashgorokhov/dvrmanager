import logging
from pathlib import Path
from typing import Tuple, Optional

from pydantic import BaseModel, ValidationError

from dvrmanager import config

logger = logging.getLogger(__name__)


class ExportItem(BaseModel):
    drive_name: str
    drive_path: Optional[Path] = None

    delete: bool = True
    unmount: bool = True
    automatic: bool = True

    @classmethod
    def create_default(cls) -> 'ExportItem':
        return ExportItem(
            drive_name='DVR_FLASHDRIVE',
            drive_path=Path('DCIM/*.avi'),
            delete=True,
            unmount=True,
            automatic=True
        )


class Settings(BaseModel):
    target_directory: Path

    export_items: Tuple[ExportItem, ...]

    @classmethod
    def create_default(cls) -> 'Settings':
        return Settings(
            target_directory=config.BASE_DIR / 'flight logs',
            export_items=(ExportItem.create_default(),)
        )

    @classmethod
    def load(cls) -> 'Settings':
        settings: Optional[Settings] = None

        if cls.path().exists():
            try:
                settings = cls.parse_file(cls.path())
            except ValidationError:
                logger.exception(f'Error loading settings from {cls.path()}')

        if not settings:
            settings = cls.create_default()
            settings.save()

        return settings

    def save(self):
        self.path().parent.mkdir(parents=True, exist_ok=True)
        self.path().write_text(self.json())

    @staticmethod
    def path() -> Path:
        return config.SETTINGS_DIR / 'settings.json'
