import stat
import traceback
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import PurePath
from typing import Any, Generator, Iterator

from cerulean.file_system import FileSystem
from cerulean.path import EntryType, Path, Permission


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
    def exists(self, path: PurePath) -> bool:
        pass

    @abstractmethod
    def mkdir(self,
              path: PurePath,
              mode: int = 0o777,
              parents: bool = False,
              exists_ok: bool = False) -> None:
        pass

    @abstractmethod
    def iterdir(self, path: PurePath) -> Generator[PurePath, None, None]:
        pass

    @abstractmethod
    def rmdir(self, path: PurePath, recursive: bool = False) -> None:
        pass

    @abstractmethod
    def touch(self, path: PurePath) -> None:
        pass

    @abstractmethod
    def streaming_read(self, path: PurePath) -> Generator[bytes, None, None]:
        pass

    @abstractmethod
    def streaming_write(self, path: PurePath, data: Iterator[bytes]):
        pass

    # Convenience functions are implemented here, on top of the internal API
    def read_bytes(self, path: PurePath) -> bytes:
        data = bytearray()
        for chunk in self.streaming_read(path):
            data += chunk
        return bytes(data)

    def read_text(self, path: PurePath, encoding='utf-8',
                  errors='strict') -> str:
        return self.read_bytes(path).decode(encoding, errors)

    def write_bytes(self, path: PurePath, data: bytes) -> None:
        self.streaming_write(path, [data])

    def write_text(self,
                   path: PurePath,
                   data: str,
                   encoding='utf-8',
                   errors='strict') -> None:
        self.write_bytes(path, data.encode(encoding, errors))

    @abstractmethod
    def rename(self, path: PurePath, target: PurePath) -> None:
        pass

    @abstractmethod
    def unlink(self, path: PurePath) -> None:
        pass

    # File type and size

    @abstractmethod
    def is_dir(self, path: PurePath) -> bool:
        pass

    @abstractmethod
    def is_file(self, path: PurePath) -> bool:
        pass

    @abstractmethod
    def is_symlink(self, path: PurePath) -> bool:
        pass

    @abstractmethod
    def entry_type(self, path: PurePath) -> EntryType:
        pass

    @abstractmethod
    def size(self, path: PurePath) -> int:
        pass

    # Permissions

    @abstractmethod
    def uid(self, path: PurePath) -> int:
        pass

    @abstractmethod
    def gid(self, path: PurePath) -> int:
        pass

    @abstractmethod
    def has_permission(self, path: PurePath, permission: Permission) -> bool:
        pass

    @abstractmethod
    def set_permission(self,
                       path: PurePath,
                       permission: Permission,
                       value: bool = True) -> None:
        pass

    @abstractmethod
    def chmod(self, path: PurePath, mode: int) -> None:
        pass

    @abstractmethod
    def symlink_to(self, path: PurePath, target: PurePath) -> None:
        pass

    @abstractmethod
    def readlink(self, path: PurePath, recursive: bool) -> Path:
        pass
