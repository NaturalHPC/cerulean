import stat
from pathlib import PurePath
from typing import Generator, Iterator

import paramiko
from cerulean.file_system_impl import FileSystemImpl
from cerulean.path import EntryType, Path, Permission
from cerulean.ssh_terminal import SshTerminal
from overrides import overrides


class SftpFileSystem(FileSystemImpl):
    def __init__(self, terminal: SshTerminal):
        self.__sftp = terminal._get_sftp_client()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.__sftp.close()

    @overrides
    def exists(self, path: PurePath) -> bool:
        try:
            self.__sftp.stat(str(path))
            return True
        except IOError:
            return False

    @overrides
    def mkdir(self,
              path: PurePath,
              mode: int = 0o777,
              parents: bool = False,
              exists_ok: bool = False) -> None:
        if parents:
            for parent in reversed(path.parents):
                if not self.exists(parent):
                    self.__sftp.mkdir(str(parent))
                    self.__sftp.chmod(str(parent), 0o777)
        if self.exists(path):
            if not exists_ok:
                raise FileExistsError(
                    'File {} exists and exists_ok was False'.format(path))
            else:
                return

        self.__sftp.mkdir(str(path))
        self.__sftp.chmod(str(path), mode)

    @overrides
    def iterdir(self, path: PurePath) -> Generator[Path, None, None]:
        # Note: we're not using listdir_iter here, because it hangs:
        # https://github.com/paramiko/paramiko/issues/1171
        for entry in self.__sftp.listdir(str(path)):
            yield path / entry

    @overrides
    def rmdir(self, path: PurePath, recursive: bool = False) -> None:
        if not self.exists(path):
            return

        if not self.is_dir(path):
            raise RuntimeError("Path must refer to a directory")

        if recursive:
            for entry in self.__sftp.listdir_attr(str(path)):
                entry_path = path / entry.filename
                if self.is_symlink(entry_path):
                    self.__sftp.unlink(str(entry_path))
                elif self.is_dir(entry_path):
                    self.rmdir(entry_path, True)
                else:
                    self.__sftp.unlink(str(entry_path))

        self.__sftp.rmdir(str(path))

    @overrides
    def touch(self, path: PurePath) -> None:
        with self.__sftp.file(str(path), 'a') as f:
            pass

    @overrides
    def streaming_read(self, path: PurePath) -> Generator[bytes, None, None]:
        with self.__sftp.file(str(path), 'rb') as f:
            data = f.read(1024 * 1024)
            while len(data) > 0:
                yield data
                data = f.read(1024 * 1024)

    @overrides
    def streaming_write(self, path: PurePath, data: Iterator[bytes]) -> None:
        with self.__sftp.file(str(path), 'wb') as f:
            for chunk in data:
                f.write(chunk)

    @overrides
    def rename(self, path: PurePath, target: PurePath) -> None:
        self.__sftp.posix_rename(str(path), str(target))

    @overrides
    def unlink(self, path: PurePath) -> bool:
        self.__sftp.unlink(str(path))

    @overrides
    def is_dir(self, path: PurePath) -> bool:
        try:
            return bool(stat.S_ISDIR(self.__stat(path).st_mode))
        except FileNotFoundError:
            return False

    @overrides
    def is_file(self, path: PurePath) -> bool:
        try:
            mode = self.__stat(path).st_mode
            return bool(stat.S_ISREG(mode))
        except FileNotFoundError:
            return False

    @overrides
    def is_symlink(self, path: PurePath) -> bool:
        try:
            return bool(stat.S_ISLNK(self.__lstat(path).st_mode))
        except FileNotFoundError:
            return False

    @overrides
    def entry_type(self, path: PurePath) -> EntryType:
        mode_to_type = [(stat.S_ISDIR, EntryType.DIRECTORY), (stat.S_ISREG,
                                                              EntryType.FILE),
                        (stat.S_ISLNK, EntryType.SYMBOLIC_LINK),
                        (stat.S_ISCHR,
                         EntryType.CHARACTER_DEVICE), (stat.S_ISBLK,
                                                       EntryType.BLOCK_DEVICE),
                        (stat.S_ISFIFO, EntryType.FIFO), (stat.S_ISSOCK,
                                                          EntryType.SOCKET)]

        mode = self.__lstat(path).st_mode
        for predicate, result in mode_to_type:
            if predicate(mode):
                return result
        return None

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
    def set_permission(self,
                       path: PurePath,
                       permission: Permission,
                       value: bool = True) -> None:
        mode = self.__stat(path).st_mode
        if value:
            mode = mode | permission.value
        else:
            mode = mode & ~permission.value
        self.chmod(path, mode)

    @overrides
    def chmod(self, path: PurePath, mode: int) -> None:
        self.__sftp.chmod(str(path), mode)

    @overrides
    def symlink_to(self, path: PurePath, target: PurePath) -> None:
        self.__sftp.symlink(str(target), str(path))

    @overrides
    def readlink(self, path: PurePath, recursive: bool) -> Path:
        if recursive:
            # SFTP's normalize() raises if there's a link loop or a \
            # non-existing target, which we don't want, so we use \
            # our own algorithm.
            max_iter = 32
            cur_path = path
            iter_count = 0
            while self.is_symlink(cur_path) and iter_count < max_iter:
                target = PurePath(self.__sftp.readlink(str(cur_path)))
                if not target.is_absolute():
                    target = cur_path.parent / target
                cur_path = target
                iter_count += 1

            if iter_count == max_iter:
                raise RuntimeError('Too many symbolic links detected')

            target = Path(self, self.__sftp.normalize(str(path)))
        else:
            target = PurePath(self.__sftp.readlink(str(path)))
            if not target.is_absolute():
                target = path.parent / target

        return Path(self, target)

    def __lstat(self, path: PurePath):
        return self.__sftp.lstat(str(path))

    def __stat(self, path: PurePath):
        return self.__sftp.stat(str(path))
