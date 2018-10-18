import stat
import traceback
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Generator, Iterable

from cerulean.file_system import FileSystem
from cerulean.path import AbstractPath, EntryType, Path, Permission


class FileSystemImpl(FileSystem):
    """Abstract class for file system implementations.

    This class exists to document the (internal!) interface and to \
    help keep it consistent between the different kinds of file \
    systems, as well as to implement some shared convenience functions.

    You will want to use a  concrete file system, like LocalFileSystem \
    or SftpFileSystem.
    """

    # Existence and contents

    @abstractmethod
    def _exists(self, path: AbstractPath) -> bool:
        pass

    @abstractmethod
    def _mkdir(self,
              path: AbstractPath,
              mode: int = 0o777,
              parents: bool = False,
              exists_ok: bool = False) -> None:
        pass

    @abstractmethod
    def _iterdir(self, path: AbstractPath) -> Generator[AbstractPath, None, None]:
        pass

    @abstractmethod
    def _rmdir(self, path: AbstractPath, recursive: bool = False) -> None:
        pass

    @abstractmethod
    def _touch(self, path: AbstractPath) -> None:
        pass

    @abstractmethod
    def _streaming_read(self, path: AbstractPath) -> Generator[bytes, None, None]:
        pass

    @abstractmethod
    def _streaming_write(self, path: AbstractPath, data: Iterable[bytes]) -> None:
        pass

    # Convenience functions are implemented here, on top of the internal API
    def _read_bytes(self, path: AbstractPath) -> bytes:
        data = bytearray()
        for chunk in self._streaming_read(path):
            data += chunk
        return bytes(data)

    def _read_text(self, path: AbstractPath, encoding: str = 'utf-8',
                  errors: str = 'strict') -> str:
        return self._read_bytes(path).decode(encoding, errors)

    def _write_bytes(self, path: AbstractPath, data: bytes) -> None:
        self._streaming_write(path, [data])

    def _write_text(self,
                   path: AbstractPath,
                   data: str,
                   encoding: str = 'utf-8',
                   errors: str = 'strict') -> None:
        self._write_bytes(path, data.encode(encoding, errors))

    @abstractmethod
    def _rename(self, path: AbstractPath, target: AbstractPath) -> None:
        pass

    @abstractmethod
    def _unlink(self, path: AbstractPath) -> None:
        pass

    # File type and size

    @abstractmethod
    def _is_dir(self, path: AbstractPath) -> bool:
        pass

    @abstractmethod
    def _is_file(self, path: AbstractPath) -> bool:
        pass

    @abstractmethod
    def _is_symlink(self, path: AbstractPath) -> bool:
        pass

    @abstractmethod
    def _entry_type(self, path: AbstractPath) -> EntryType:
        pass

    @abstractmethod
    def _size(self, path: AbstractPath) -> int:
        pass

    # Permissions

    @abstractmethod
    def _uid(self, path: AbstractPath) -> int:
        pass

    @abstractmethod
    def _gid(self, path: AbstractPath) -> int:
        pass

    @abstractmethod
    def _has_permission(self, path: AbstractPath, permission: Permission) -> bool:
        pass

    @abstractmethod
    def _set_permission(self,
                       path: AbstractPath,
                       permission: Permission,
                       value: bool = True) -> None:
        pass

    @abstractmethod
    def _chmod(self, path: AbstractPath, mode: int) -> None:
        pass

    @abstractmethod
    def _symlink_to(self, path: AbstractPath, target: AbstractPath) -> None:
        pass

    @abstractmethod
    def _readlink(self, path: AbstractPath, recursive: bool) -> Path:
        pass
