from abc import ABC
from pathlib import PurePath
from typing import cast, TYPE_CHECKING, Union

from cerulean.path import Path

if TYPE_CHECKING:
    from cerulean.file_system_impl import FileSystemImpl


class FileSystem(ABC):
    """Represents a file system.

    This is a generic interface class that all file systems inherit \
    from, so you can use it wherever any file system will do.

    In order to do something useful, you'll want an actual file system,
    like a :class:`LocalFileSystem` or an :class:`SftpFileSystem`.

    File systems support a single operation:

    .. code-block:: python

      fs / 'path'

    which produces a :class:`Path`, through which you can do things \
    with files.
    """
    def __truediv__(self, segment: str) -> Path:
        raise NotImplementedError()
