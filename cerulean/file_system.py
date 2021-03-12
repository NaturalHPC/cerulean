from abc import ABC
from types import TracebackType
from typing import Any, Optional, Union

from cerulean.path import Path
from cerulean.util import BaseExceptionType


class UnsupportedOperationError(RuntimeError):
    """Raised when an unsupported method is called.

    See :class:`WebdavFileSystem`.
    """
    pass


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
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Optional[BaseExceptionType],
                 exc_value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> None:
        """Exit context manager."""
        pass

    def __eq__(self, other: Any) -> bool:
        """Returns True iff this filesystem and other are equal.

        FileSystem objects compare equal if they access the same
        file system on the same host via the same protocol.
        """
        return NotImplemented

    def close(self) -> None:
        """Close connections and free resources, if any.

        FileSystem objects may hold resources that need to be freed \
        when you are done with the object. You can free them by calling \
        this function, or you can use the FileSystem as a context \
        manager using a ``with`` statement.
        """
        pass

    def root(self) -> Path:
        """Returns a Path representing the root of the file system.
        """
        raise NotImplementedError()

    def __truediv__(self, segment: str) -> Path:
        """Returns a Path anchored at this file system's root."""
        raise NotImplementedError()
