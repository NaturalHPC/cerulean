import logging
import stat
from pathlib import PurePosixPath
from types import TracebackType
from typing import cast, Generator, Iterable, Optional

import paramiko
from cerulean.file_system_impl import FileSystemImpl
from cerulean.path import AbstractPath, EntryType, Path, Permission
from cerulean.ssh_terminal import SshTerminal
from cerulean.util import BaseExceptionType


logger = logging.getLogger(__name__)


class SftpFileSystem(FileSystemImpl):
    """A FileSystem implementation that connects to an SFTP server.

    SftpFileSystem supports the / operation:

    .. code-block:: python

      fs / 'path'

    which produces a :class:`Path`, through which you can do things \
    with the remote files.

    It is also a context manager, so that you can (and should!) use it \
    with a ``with`` statement, which will ensure that the connection \
    is closed when you are done with the it. Alternatively, you can \
    call :meth:`close` to close the connection.

    If `own_term` is True, this class assumes that it owns the terminal \
    you gave it, and that it is responsible for closing it when it's \
    done with it. If you share an SshTerminal between an SftpFileSystem \
    and a scheduler, or use the terminal directly yourself, then you \
    want to use False here, and close the terminal yourself when you \
    don't need it any more.

    Args:
        terminal: The terminal to connect through.
        own_term: Whether to close the terminal when the file system \
                is closed.
    """
    def __init__(self, terminal: SshTerminal, own_term: bool = False) -> None:
        self.__terminal = terminal
        self.__own_term = own_term
        self.__ensure_sftp(True)
        self.__max_tries = 3

    def __enter__(self) -> 'SftpFileSystem':
        return self

    def __exit__(self, exc_type: Optional[BaseExceptionType],
                 exc_value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> None:
        if self.__own_term:
            self.close()

    def close(self) -> None:
        self.__sftp.close()
        logger.info('Disconnected from SFTP server')

    def __truediv__(self, segment: str) -> Path:
        return Path(self, PurePosixPath('/' + segment))

    def _exists(self, path: AbstractPath) -> bool:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        try:
            self.__sftp.stat(str(lpath))
            return True
        except IOError:
            return False

    def _mkdir(self,
              path: AbstractPath,
              mode: int = 0o777,
              parents: bool = False,
              exists_ok: bool = False) -> None:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        if parents:
            for parent in reversed(lpath.parents):
                if not self._exists(parent):
                    self.__sftp.mkdir(str(parent))
                    # The 0o777 is intentional and matches pathlib and
                    # POSIX mkdir
                    self.__sftp.chmod(str(parent), 0o777)
        if self._exists(lpath):
            if not exists_ok:
                raise FileExistsError(
                    'File {} exists and exists_ok was False'.format(lpath))
            else:
                return

        self.__sftp.mkdir(str(lpath))
        self.__sftp.chmod(str(lpath), mode)

    def _iterdir(self, path: AbstractPath) -> Generator[PurePosixPath, None, None]:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        # Note: we're not using listdir_iter here, because it hangs:
        # https://github.com/paramiko/paramiko/issues/1171
        for entry in self.__sftp.listdir(str(lpath)):
            yield lpath / entry

    def _rmdir(self, path: AbstractPath, recursive: bool = False) -> None:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        if not self._exists(lpath):
            return

        if not self._is_dir(lpath):
            raise RuntimeError("Path must refer to a directory")

        if recursive:
            for entry in self.__sftp.listdir_attr(str(lpath)):
                entry_path = lpath / entry.filename
                if self._is_symlink(entry_path):
                    self.__sftp.unlink(str(entry_path))
                elif self._is_dir(entry_path):
                    self._rmdir(entry_path, True)
                else:
                    self.__sftp.unlink(str(entry_path))

        self.__sftp.rmdir(str(lpath))

    def _touch(self, path: AbstractPath) -> None:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        with self.__sftp.file(str(lpath), 'a'):
            pass

    def _streaming_read(self, path: AbstractPath) -> Generator[bytes, None, None]:
        # Buffer size vs. speed (MB/s) against localhost
        #       up      down        local
        # 8k    33      56          159
        # 16k   52      56          145
        # 24k   66      57          150
        # 32k   24      57          149
        # 2M    24      48
        # scp   120     110
        # cp                        172
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        tries = 0
        while tries < self.__max_tries:
            try:
                size = self._size(path)
                with self.__sftp.file(str(lpath), 'rb') as f:
                    f.prefetch(size)
                    data = f.read(24576)
                    while len(data) > 0:
                        yield data
                        data = f.read(24576)
                return
            except paramiko.SSHException as e:
                if 'Server connection dropped' in str(e):
                    tries += 1
                else:
                    raise e
        raise ConnectionError('Too many connection errors.')

    def _streaming_write(self, path: AbstractPath, data: Iterable[bytes]) -> None:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        tries = 0
        while tries < self.__max_tries:
            try:
                with self.__sftp.file(str(lpath), 'wb') as f:
                    f.set_pipelined(True)
                    for chunk in data:
                        f.write(chunk)
                return
            except paramiko.SSHException as e:
                if 'Server connection dropped' in str(e):
                    tries += 1
                else:
                    raise e
        raise ConnectionError('Too many connection errors.')


    def _rename(self, path: AbstractPath, target: AbstractPath) -> None:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        ltarget = cast(PurePosixPath, target)
        self.__sftp.posix_rename(str(lpath), str(ltarget))

    def _unlink(self, path: AbstractPath) -> None:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        self.__sftp.unlink(str(lpath))

    def _is_dir(self, path: AbstractPath) -> bool:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        try:
            return bool(stat.S_ISDIR(self.__stat(lpath).st_mode))
        except FileNotFoundError:
            return False

    def _is_file(self, path: AbstractPath) -> bool:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        try:
            mode = self.__stat(lpath).st_mode
            return bool(stat.S_ISREG(mode))
        except FileNotFoundError:
            return False

    def _is_symlink(self, path: AbstractPath) -> bool:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        try:
            return bool(stat.S_ISLNK(self.__lstat(lpath).st_mode))
        except FileNotFoundError:
            return False

    def _entry_type(self, path: AbstractPath) -> EntryType:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        mode_to_type = [(stat.S_ISDIR, EntryType.DIRECTORY), (stat.S_ISREG,
                                                              EntryType.FILE),
                        (stat.S_ISLNK, EntryType.SYMBOLIC_LINK),
                        (stat.S_ISCHR,
                         EntryType.CHARACTER_DEVICE), (stat.S_ISBLK,
                                                       EntryType.BLOCK_DEVICE),
                        (stat.S_ISFIFO, EntryType.FIFO), (stat.S_ISSOCK,
                                                          EntryType.SOCKET)]

        mode = self.__lstat(lpath).st_mode
        for predicate, result in mode_to_type:
            if predicate(mode):
                return result
        raise RuntimeError('Object is of unknown type, please report a'
                           'Cerulean bug')

    def _size(self, path: AbstractPath) -> int:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        return self.__stat(lpath).st_size

    def _uid(self, path: AbstractPath) -> int:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        return self.__stat(lpath).st_uid

    def _gid(self, path: AbstractPath) -> int:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        return self.__stat(lpath).st_gid

    def _has_permission(self, path: AbstractPath, permission: Permission) -> bool:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        return bool(self.__stat(lpath).st_mode & permission.value)

    def _set_permission(self,
                       path: AbstractPath,
                       permission: Permission,
                       value: bool = True) -> None:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        mode = self.__stat(lpath).st_mode
        if value:
            mode = mode | permission.value
        else:
            mode = mode & ~permission.value
        self._chmod(lpath, mode)

    def _chmod(self, path: AbstractPath, mode: int) -> None:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        self.__sftp.chmod(str(lpath), mode)

    def _symlink_to(self, path: AbstractPath, target: AbstractPath) -> None:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        ltarget = cast(PurePosixPath, target)
        self.__sftp.symlink(str(ltarget), str(lpath))

    def _readlink(self, path: AbstractPath, recursive: bool) -> Path:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        if recursive:
            # SFTP's normalize() raises if there's a link loop or a \
            # non-existing target, which we don't want, so we use \
            # our own algorithm.
            max_iter = 32
            cur_path = lpath
            iter_count = 0
            while self._is_symlink(cur_path) and iter_count < max_iter:
                target = PurePosixPath(self.__sftp.readlink(str(cur_path)))
                if not target.is_absolute():
                    target = cur_path.parent / target
                cur_path = target
                iter_count += 1

            if iter_count == max_iter:
                raise RuntimeError('Too many symbolic links detected')

            target = PurePosixPath(self.__sftp.normalize(str(path)))
        else:
            target = PurePosixPath(self.__sftp.readlink(str(path)))
            if not target.is_absolute():
                target = lpath.parent / target

        return Path(self, target)

    def __lstat(self, path: PurePosixPath) -> paramiko.SFTPAttributes:
        return self.__sftp.lstat(str(path))

    def __stat(self, path: PurePosixPath) -> paramiko.SFTPAttributes:
        return self.__sftp.stat(str(path))

    def __ensure_sftp(self, first: bool = False) -> None:
        if first:
            logger.info('Connecting to SFTP server')
            self.__sftp = self.__terminal._get_sftp_client()
            logger.info('Connected to SFTP server')
        elif not self.__sftp.get_channel().get_transport().is_active():
            logger.info('Reconnecting to SFTP server')
            self.__sftp = self.__terminal._get_sftp_client()
            logger.info('Connected to SFTP server')
