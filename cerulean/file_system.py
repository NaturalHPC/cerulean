from abc import ABC

from cerulean.path import Path


class FileSystem(ABC):
    """Represents a file system.
    """

    def __init__(self) -> None:
        pass

    @property
    def root(self) -> Path:
        return Path(self, '/')

    def __truediv__(self, path: Path) -> Path:
        return Path(self, self.root / path)
