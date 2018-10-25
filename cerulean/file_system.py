from abc import ABC
from pathlib import PurePath
from types import TracebackType
from typing import cast, TYPE_CHECKING, Optional, Union

from cerulean.path import Path
from cerulean.util import BaseExceptionType


if TYPE_CHECKING:
    from cerulean.file_system_impl import FileSystemImpl


class FileSystem(ABC):
    """Represents a file system.

    This is a generic interface class that all file systems inherit \
    from, so you can use it wherever any file system will do.

    In order to do something useful, you'll want an actual file system,
    like a :class:`LocalFileSystem` or an :class:`SftpFileSystem`.

    FileSystems may hold resources, so you should either use them \
    with a ``with`` statement, or call :meth:`close` on the returned \
    object when you are done with it.

    Beyond that, file systems support a single operation:

    .. code-block:: python

      fs / 'path'

    which produces a :class:`Path`, through which you can do things \
    with files.
    """
    def __enter__(self) -> 'FileSystem':
        return self

    def __exit__(self, exc_type: Optional[BaseExceptionType],
                 exc_value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> None:
        pass

    def close(self) -> None:
        """Close connections and free resources, if any.

        FileSystem objects may hold resources that need to be freed \
        when you are done with the object. You can free them by calling \
        this function, or you can use the FileSystem as a context \
        manager using a ``with`` statement.
        """
        pass

    def __truediv__(self, segment: str) -> Path:
        raise NotImplementedError()
