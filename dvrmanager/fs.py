import sys


class FSManager:
    pass


def get_fs_manager() -> FSManager:
    if sys.platform == 'win32':
        return FSManager()
