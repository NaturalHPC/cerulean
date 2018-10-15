import errno
import os
import pathlib
from typing import cast, Any, Generator, Iterable

from cerulean.file_system_impl import FileSystemImpl
from cerulean.path import AbstractPath, EntryType, Path, Permission


class LocalFileSystem(FileSystemImpl):
    def __truediv__(self, segment: str) -> Path:
        # TODO: segment: Union[str, pathlib.Path]?
        absseg = '/' + segment
        path = pathlib.Path(absseg)
        return Path(self, path)

    def exists(self, path: AbstractPath) -> bool:
        lpath = cast(pathlib.Path, path)
        try:
            return lpath.exists()
        except OSError as e:
            if e.errno == errno.ELOOP:
                return False
            raise

    def mkdir(self,
              path: AbstractPath,
              mode: int = 0o777,
              parents: bool = False,
              exists_ok: bool = False) -> None:
        lpath = cast(pathlib.Path, path)
        lpath.mkdir(mode, parents, exists_ok)

    def iterdir(self, path: AbstractPath) -> Generator[AbstractPath, None, None]:
        lpath = cast(pathlib.Path, path)
        for entry in lpath.iterdir():
            yield entry

    def rmdir(self, path: AbstractPath, recursive: bool = False) -> None:
        lpath = cast(pathlib.Path, path)
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

    def touch(self, path: AbstractPath) -> None:
        lpath = cast(pathlib.Path, path)
        lpath.touch()

    def streaming_read(self, path: AbstractPath) -> Generator[bytes, None, None]:
        lpath = cast(pathlib.Path, path)
        with lpath.open('rb') as f:
            data = f.read(1024 * 1024)
            while len(data) > 0:
                yield data
                data = f.read(1024 * 1024)

    def streaming_write(self, path: AbstractPath, data: Iterable[bytes]) -> None:
        lpath = cast(pathlib.Path, path)
        with lpath.open('wb') as f:
            for chunk in data:
                f.write(chunk)

    def rename(self, path: AbstractPath, target: AbstractPath) -> None:
        lpath = cast(pathlib.Path, path)
        ltarget = cast(pathlib.Path, target)
        lpath.replace(pathlib.Path(ltarget))

    def unlink(self, path: AbstractPath) -> None:
        lpath = cast(pathlib.Path, path)
        lpath.unlink()

    def is_dir(self, path: AbstractPath) -> bool:
        lpath = cast(pathlib.Path, path)
        return lpath.is_dir()

    def is_file(self, path: AbstractPath) -> bool:
        lpath = cast(pathlib.Path, path)
        return lpath.is_file()

    def is_symlink(self, path: AbstractPath) -> bool:
        lpath = cast(pathlib.Path, path)
        return lpath.is_symlink()

    def entry_type(self, path: AbstractPath) -> EntryType:
        lpath = cast(pathlib.Path, path)
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
            if pred(lpath):
                return entry_type
        raise RuntimeError('Object is of unknown type, please report a'
                           'Cerulean bug')

    def size(self, path: AbstractPath) -> int:
        lpath = cast(pathlib.Path, path)
        return lpath.stat().st_size

    def uid(self, path: AbstractPath) -> int:
        lpath = cast(pathlib.Path, path)
        return lpath.stat().st_uid

    def gid(self, path: AbstractPath) -> int:
        lpath = cast(pathlib.Path, path)
        return lpath.stat().st_gid

    def has_permission(self, path: AbstractPath, permission: Permission) -> bool:
        lpath = cast(pathlib.Path, path)
        return bool(lpath.stat().st_mode & permission.value)

    def set_permission(self, path: AbstractPath, permission: Permission,
                       value: bool = True) -> None:
        lpath = cast(pathlib.Path, path)
        mode = lpath.stat().st_mode
        if value:
            mode = mode | permission.value
        else:
            mode = mode & ~permission.value

        self.chmod(lpath, mode)

    def chmod(self, path: AbstractPath, mode: int) -> None:
        lpath = cast(pathlib.Path, path)
        lpath.chmod(mode)

    def symlink_to(self, path: AbstractPath, target: AbstractPath) -> None:
        lpath = cast(pathlib.Path, path)
        ltarget = cast(pathlib.Path, target)
        lpath.symlink_to(ltarget)

    def readlink(self, path: AbstractPath, recursive: bool) -> Path:
        lpath = cast(pathlib.Path, path)
        if recursive:
            # pathlib.Path.resolve() raises if the link is broken
            # we don't want that, so use our own implementation
            max_iter = 32
            cur_path = lpath
            iter_count = 0
            while cur_path.is_symlink() and iter_count < max_iter:
                target = pathlib.Path(os.readlink(str(cur_path)))
                if not target.is_absolute():
                    target = cur_path.parent / target
                cur_path = target
                iter_count += 1

            if iter_count == max_iter:
                raise RuntimeError('Too many symbolic links detected')

            return Path(self, cur_path)
        else:
            return Path(self, pathlib.Path(
                os.readlink(str(lpath))))
