from abc import ABC
from pathlib import PurePath
from typing import cast, TYPE_CHECKING, Union

from cerulean.path import Path

if TYPE_CHECKING:
    from cerulean.file_system_impl import FileSystemImpl


class FileSystem(ABC):
    """Represents a file system.
    """
    def __truediv__(self, segment: str) -> Path:
        raise NotImplementedError()
