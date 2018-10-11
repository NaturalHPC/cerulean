import errno
import os
import pathlib
from pathlib import PurePath
from typing import Any, Generator, Iterator

from cerulean.file_system_impl import FileSystemImpl
from cerulean.path import EntryType, Path, Permission
from overrides import overrides


class LocalFileSystem(FileSystemImpl):
    @overrides
    def exists(self, path: PurePath) -> bool:
        try:
            return pathlib.Path(path).exists()
        except OSError as e:
            if e.errno == errno.ELOOP:
                return False
            raise

    @overrides
    def mkdir(self,
              path: PurePath,
              mode: int = 0o777,
              parents: bool = False,
              exists_ok: bool = False) -> None:
        pathlib.Path(path).mkdir(mode, parents, exists_ok)

    @overrides
    def iterdir(self, path: PurePath) -> Generator[PurePath, None, None]:
        for entry in pathlib.Path(path).iterdir():
            yield entry

    @overrides
    def rmdir(self, path: PurePath, recursive: bool = False) -> None:
        lpath = pathlib.Path(path)
        if not lpath.is_dir():
            raise RuntimeError('Path must refer to a directory')

        if recursive:
            for entry in lpath.iterdir():
                if entry.is_symlink():
                    entry.unlink()
                elif entry.is_dir():
                    self.rmdir(entry, True)
                else:
                    entry.unlink()

        lpath.rmdir()

    @overrides
    def touch(self, path: PurePath) -> None:
        pathlib.Path(path).touch()

    @overrides
    def streaming_read(self, path: PurePath) -> Generator[bytes, None, None]:
        with pathlib.Path(path).open('rb') as f:
            data = f.read(1024 * 1024)
            while len(data) > 0:
                yield data
                data = f.read(1024 * 1024)

    @overrides
    def streaming_write(self, path: PurePath, data: Iterator[bytes]) -> None:
        with pathlib.Path(path).open('wb') as f:
            for chunk in data:
                f.write(chunk)

    @overrides
    def rename(self, path: PurePath, target: PurePath) -> None:
        pathlib.Path(path).replace(pathlib.Path(target))

    @overrides
    def unlink(self, path: PurePath) -> None:
        pathlib.Path(path).unlink()

    @overrides
    def is_dir(self, path: PurePath) -> bool:
        return pathlib.Path(path).is_dir()

    @overrides
    def is_file(self, path: PurePath) -> bool:
        return pathlib.Path(path).is_file()

    @overrides
    def is_symlink(self, path: PurePath) -> bool:
        return pathlib.Path(path).is_symlink()

    @overrides
    def entry_type(self, path: PurePath) -> EntryType:
        # Note: symlink goes first, because is_dir() and is_file() will
        # dereference and return true, while we want to say it's a
        # symlink and leave it at that.
        pred_to_type = [(pathlib.Path.is_symlink,
                         EntryType.SYMBOLIC_LINK), (pathlib.Path.is_dir,
                                                    EntryType.DIRECTORY),
                        (pathlib.Path.is_file,
                         EntryType.FILE), (pathlib.Path.is_char_device,
                                           EntryType.CHARACTER_DEVICE),
                        (pathlib.Path.is_block_device, EntryType.BLOCK_DEVICE),
                        (pathlib.Path.is_fifo,
                         EntryType.FIFO), (pathlib.Path.is_socket,
                                           EntryType.SOCKET)]

        for pred, entry_type in pred_to_type:
            if pred(pathlib.Path(path)):
                return entry_type

    @overrides
    def size(self, path: PurePath) -> int:
        return self.__stat(path).st_size

    @overrides
    def uid(self, path: PurePath) -> int:
        return self.__stat(path).st_uid

    @overrides
    def gid(self, path: PurePath) -> int:
        return self.__stat(path).st_gid

    @overrides
    def has_permission(self, path: PurePath, permission: Permission) -> bool:
        return bool(self.__stat(path).st_mode & permission.value)

    @overrides
    def set_permission(self, path: PurePath, permission: Permission,
                       value: bool) -> bool:
        mode = self.__stat(path).st_mode
        if value:
            mode = mode | permission.value
        else:
            mode = mode & ~permission.value

        self.chmod(path, mode)

    @overrides
    def chmod(self, path: PurePath, mode: int) -> None:
        pathlib.Path(path).chmod(mode)

    @overrides
    def symlink_to(self, path: PurePath, target: PurePath) -> None:
        pathlib.Path(path).symlink_to(target)

    @overrides
    def readlink(self, path: PurePath, recursive: bool) -> Path:
        if recursive:
            # pathlib.Path.resolve() raises if the link is broken
            # we don't want that, so use our own implementation
            max_iter = 32
            cur_path = pathlib.Path(path)
            iter_count = 0
            while cur_path.is_symlink() and iter_count < max_iter:
                target = pathlib.Path(os.readlink(str(cur_path)))
                if not target.is_absolute():
                    target = cur_path.parent / target
                cur_path = target
                iter_count += 1

            if iter_count == max_iter:
                raise RuntimeError('Too many symbolic links detected')

            return cur_path
        else:
            return Path(self, pathlib.Path(
                os.readlink(str(pathlib.Path(path)))))

    def __stat(self, path: PurePath):
        return pathlib.Path(path).stat()
