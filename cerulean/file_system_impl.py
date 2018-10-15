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
    def exists(self, path: AbstractPath) -> bool:
        pass

    @abstractmethod
    def mkdir(self,
              path: AbstractPath,
              mode: int = 0o777,
              parents: bool = False,
              exists_ok: bool = False) -> None:
        pass

    @abstractmethod
    def iterdir(self, path: AbstractPath) -> Generator[AbstractPath, None, None]:
        pass

    @abstractmethod
    def rmdir(self, path: AbstractPath, recursive: bool = False) -> None:
        pass

    @abstractmethod
    def touch(self, path: AbstractPath) -> None:
        pass

    @abstractmethod
    def streaming_read(self, path: AbstractPath) -> Generator[bytes, None, None]:
        pass

    @abstractmethod
    def streaming_write(self, path: AbstractPath, data: Iterable[bytes]) -> None:
        pass

    # Convenience functions are implemented here, on top of the internal API
    def read_bytes(self, path: AbstractPath) -> bytes:
        data = bytearray()
        for chunk in self.streaming_read(path):
            data += chunk
        return bytes(data)

    def read_text(self, path: AbstractPath, encoding: str = 'utf-8',
                  errors: str = 'strict') -> str:
        return self.read_bytes(path).decode(encoding, errors)

    def write_bytes(self, path: AbstractPath, data: bytes) -> None:
        self.streaming_write(path, [data])

    def write_text(self,
                   path: AbstractPath,
                   data: str,
                   encoding: str = 'utf-8',
                   errors: str = 'strict') -> None:
        self.write_bytes(path, data.encode(encoding, errors))

    @abstractmethod
    def rename(self, path: AbstractPath, target: AbstractPath) -> None:
        pass

    @abstractmethod
    def unlink(self, path: AbstractPath) -> None:
        pass

    # File type and size

    @abstractmethod
    def is_dir(self, path: AbstractPath) -> bool:
        pass

    @abstractmethod
    def is_file(self, path: AbstractPath) -> bool:
        pass

    @abstractmethod
    def is_symlink(self, path: AbstractPath) -> bool:
        pass

    @abstractmethod
    def entry_type(self, path: AbstractPath) -> EntryType:
        pass

    @abstractmethod
    def size(self, path: AbstractPath) -> int:
        pass

    # Permissions

    @abstractmethod
    def uid(self, path: AbstractPath) -> int:
        pass

    @abstractmethod
    def gid(self, path: AbstractPath) -> int:
        pass

    @abstractmethod
    def has_permission(self, path: AbstractPath, permission: Permission) -> bool:
        pass

    @abstractmethod
    def set_permission(self,
                       path: AbstractPath,
                       permission: Permission,
                       value: bool = True) -> None:
        pass

    @abstractmethod
    def chmod(self, path: AbstractPath, mode: int) -> None:
        pass

    @abstractmethod
    def symlink_to(self, path: AbstractPath, target: AbstractPath) -> None:
        pass

    @abstractmethod
    def readlink(self, path: AbstractPath, recursive: bool) -> Path:
        pass
