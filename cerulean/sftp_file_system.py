import errno
import logging
import stat
from pathlib import PurePosixPath
from types import TracebackType
from typing import Any, cast, Generator, Iterable, Optional

import paramiko
from cerulean.file_system import FileSystem
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
        self.__sftp2 = None  # type: paramiko.SFTPClient
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

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, FileSystem):
            return NotImplemented
        if isinstance(other, SftpFileSystem):
            return self.__terminal == other.__terminal
        else:
            return False

    def root(self) -> Path:
        return Path(self, PurePosixPath('/'))

    def __truediv__(self, segment: str) -> Path:
        return Path(self, PurePosixPath('/' + segment.strip('/')))

    def _supports(self, feature: str) -> bool:
        if feature not in self._features:
            raise ValueError('Invalid argument for "feature"')
        return True

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
              mode: Optional[int] = None,
              parents: bool = False,
              exists_ok: bool = False) -> None:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        if parents:
            for parent in reversed(lpath.parents):
                if not self._exists(parent):
                    self.__sftp.mkdir(str(parent))
        if self._exists(lpath):
            if not exists_ok:
                raise FileExistsError(
                    'File {} exists and exists_ok was False'.format(lpath))
            else:
                return

        self.__sftp.mkdir(str(lpath), mode)

    def _iterdir(self, path: AbstractPath) -> Generator[PurePosixPath, None, None]:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        # Note: we're not using listdir_iter here, because it hangs:
        # https://github.com/paramiko/paramiko/issues/1171
        try:
            for entry in self.__sftp.listdir(str(lpath)):
                yield lpath / entry
        except OSError as e:
            # Paramiko omits the filename, which breaks Path.walk()
            # so add it back in here.
            raise OSError(e.errno, e.strerror, str(lpath))

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
        def ensure_sftp2(self: 'SftpFileSystem') -> None:
            if self.__sftp2 is None:
                self.__sftp2 = self.__terminal._get_downstream_sftp_client()
            else:
                try:
                    self.__sftp2.lstat('/')
                except OSError as e:
                    if 'Socket is closed' in str(e):
                        self.__sftp2 = self.__terminal._get_downstream_sftp_client()
                    else:
                        raise

                if not self.__sftp2.get_channel().get_transport().is_active():
                    self.__sftp2 = self.__terminal._get_downstream_sftp_client()

        lpath = cast(PurePosixPath, path)
        ensure_sftp2(self)
        try:
            size = self._size(path)
            with self.__sftp2.file(str(lpath), 'rb') as f:
                f.prefetch(size)
                data = f.read(24576)
                while len(data) > 0:
                    yield data
                    data = f.read(24576)
        except paramiko.SSHException as e:
            if 'Server connection dropped' in str(e):
                raise ConnectionError(e)
            else:
                raise e

    def _streaming_write(self, path: AbstractPath, data: Iterable[bytes]) -> None:
        self.__ensure_sftp()
        lpath = cast(PurePosixPath, path)
        try:
            with self.__sftp.file(str(lpath), 'wb') as f:
                f.set_pipelined(True)
                for chunk in data:
                    f.write(chunk)
        except paramiko.SSHException as e:
            if 'Server connection dropped' in str(e):
                raise ConnectionError(e)
            else:
                raise e

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

        try:
            mode = self.__lstat(lpath).st_mode
        except IOError:
            raise OSError(errno.ENOENT, 'No such file or directory',
                          str(lpath))

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
        else:
            try:
                self.__sftp.lstat('/')
            except OSError as e:
                if 'Socket is closed' in str(e):
                    logger.info('Reconnecting to SFTP server')
                    self.__sftp = self.__terminal._get_sftp_client()
                    logger.info('Connected to SFTP server')
                else:
                    raise

            if not self.__sftp.get_channel().get_transport().is_active():
                logger.info('Reconnecting to SFTP server')
                self.__sftp = self.__terminal._get_sftp_client()
                logger.info('Connected to SFTP server')
