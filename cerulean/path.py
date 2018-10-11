import stat
from abc import abstractmethod
from enum import Enum
from pathlib import PurePath, PurePosixPath
from typing import Generator, Iterable, List, Optional, Union

from overrides import overrides


class EntryType(Enum):
    DIRECTORY = 1
    FILE = 2
    SYMBOLIC_LINK = 3
    CHARACTER_DEVICE = 4
    BLOCK_DEVICE = 5
    FIFO = 6
    SOCKET = 7


class Permission(Enum):
    OWNER_READ = stat.S_IRUSR
    OWNER_WRITE = stat.S_IWUSR
    OWNER_EXECUTE = stat.S_IXUSR

    GROUP_READ = stat.S_IRGRP
    GROUP_WRITE = stat.S_IWGRP
    GROUP_EXECUTE = stat.S_IXGRP

    OTHERS_READ = stat.S_IROTH
    OTHERS_WRITE = stat.S_IWOTH
    OTHERS_EXECUTE = stat.S_IXOTH

    SUID = stat.S_ISUID
    SGID = stat.S_ISGID
    STICKY = stat.S_ISVTX


class Path(PurePosixPath):
    """A path on a file system.

    This class implements the pathlib.PurePosixPath interface \
    fully, and a pathlib.PosixPath-like interface, although it has \
    some omissions, additions, and improvements to make it more \
    compatible with remote and non-standard file systems.

    To make a Path, create a FileSystem first, then use the / operator \
    on it, e.g. fs / 'home' / 'user'. Do not construct objects of this \
    class directly.
    """

    def __new__(cls, fs_impl, path, *args, **kwargs) -> 'Path':
        return super().__new__(cls, path)

    def __init__(self, fs_impl: 'FileSystemImpl', path: str) -> None:
        super().__init__()
        self.__fs_impl = fs_impl

    # PurePath attributes and functions

    # equality check should include file system
    # less than check should include file system

    def __truediv__(self, suffix: Union[str, PurePath]) -> 'Path':
        return Path(self.__fs_impl, super().__truediv__(suffix))

    @property
    def parents(self) -> List['Path']:
        def make_path(path: PurePath) -> 'Path':
            return Path(self.__fs_impl, path)

        return list(map(make_path, super().parents))

    @property
    def parent(self) -> 'Path':
        return Path(self.__fs_impl, super().parent)

    def joinpath(self, *other) -> 'Path':
        return Path(self.__fs_impl, super().joinpath(*other))

    def relative_to(self, *other) -> 'Path':
        return Path(self.__fs_impl, super().relative_to(*other))

    def with_name(self, name: str) -> 'Path':
        return Path(self.__fs_impl, super().with_name(name))

    def with_suffix(self, suffix: str) -> 'Path':
        return Path(self.__fs_impl, super().with_suffix(suffix))

    # Existence and contents

    def exists(self) -> bool:
        """Returns true iff a filesystem object exists at this path.

        If the path denotes a symlink, returns whether the symlink \
        points to an existing filesystem object, recursively. If the \
        symlink is part of a link loop, returns False.

        Returns:
            True iff the path exists on the filesystem.
        """
        return self.__fs_impl.exists(self)

    def mkdir(self,
              mode: int = 0o777,
              parents: bool = False,
              exists_ok: bool = False) -> None:
        """Makes a directory with the given access rights.

        If parents is True, makes parent directories as needed. If \
        exists_ok is True, silently ignores if the directory already \
        exists.

        Args:
            mode: A numerical Posix access permissions mode.
            parents: Whether to make parent directories.
            exists_ok: Don't raise if target already exists.
        """
        self.__fs_impl.mkdir(self, mode, parents, exists_ok)

    def iterdir(self) -> Generator['Path', None, None]:
        """Iterates through a directory's contents.

        Yields:
            Paths of entries in the directory.
        """
        for entry in self.__fs_impl.iterdir(self):
            yield Path(self.__fs_impl, entry)

    def rmdir(self, recursive: bool = False) -> None:
        """Removes a directory.

        If recursive is True, remove all files and directories inside \
        as well. If recursive is False, the directory must be empty.
        """
        self.__fs_impl.rmdir(self, recursive)

    def touch(self) -> None:
        """Updates the access and modification times of file.

        If the file does not exist, it will be created, which is often \
        what this function is used for.
        """
        self.__fs_impl.touch(self)

    def streaming_read(self) -> Generator[bytes, None, None]:
        """Streams data from a file.

        This is a generator function that generates bytes objects \
        containing consecutive chunks of the file.
        """
        return self.__fs_impl.streaming_read(self)

    def streaming_write(self, data: Iterable[bytes]) -> None:
        """Streams data to a file.

        Creates a new file (overwriting any existing file) at the \
        current path, and writes data to it from the given iterable.

        Args:
            data: An iterable of bytes containing data to be written.
        """
        self.__fs_impl.streaming_write(self, data)

    def read_bytes(self) -> bytes:
        """Reads file contents as a bytes object.

        Returns:
            The contents of the file.
        """
        data = bytearray()
        for chunk in self.streaming_read():
            data.extend(chunk)
        return bytes(data)

    def read_text(self, encoding='utf-8') -> str:
        """Reads file contents as a string.

        Assumes UTF-8 encoding.

        Args:
            encoding: The encoding to assume.

        Returns:
            The contents of the file.
        """
        return self.read_bytes().decode(encoding)

    # TODO: write_text
    def write_bytes(self, data: bytes) -> None:
        """Writes bytes to the file.

        Overwrites the file if it exists.

        Args:
            data: The data to be written.
        """
        self.streaming_write([data])

    def rename(self, target: 'Path') -> None:
        """Renames a file.

        The new path must be in the same filesystem. If the new path \
        exists, then it will be overwritten.

        Args:
            target: The new path of the file.
        """
        self.__fs_impl.rename(self, target)

    def unlink(self) -> None:
        """Removes a file or device node.

        For removing directories, see rmdir().
        """
        self.__fs_impl.unlink(self)

    # File type and size

    def is_dir(self) -> bool:
        """Returns whether the path is a directory.

        Returns:
            True iff the path exists and is a directory, or a symbolic \
            link pointing to a directory.
        """
        return self.__fs_impl.is_dir(self)

    def is_file(self) -> bool:
        """Returns whether the path is a file.

        Returns:
            True iff the path exists and is a file, or a symbolic \
            link pointing to a file.
        """
        return self.__fs_impl.is_file(self)

    def is_symlink(self) -> bool:
        """Returns whether the path is a symlink.

        Returns:
            True iff the path exists and is a symbolic link.
        """
        return self.__fs_impl.is_symlink(self)

    def entry_type(self) -> EntryType:
        """Returns the kind of directory entry type the path points to.

        Returns:
            An EntryType enum value describing the filesystem entry.
        """
        return self.__fs_impl.entry_type(self)

    def size(self) -> int:
        """Returns the size of the file.

        Returns:
            An integer with the number of bytes in the file.
        """
        return self.__fs_impl.size(self)

    # Permissions

    def uid(self) -> Optional[int]:
        """Returns the user id of the owner of the object.

        Returns:
            An integer with the id, or None if not supported.
        """
        return self.__fs_impl.uid(self)

    def gid(self) -> Optional[int]:
        """Returns the group id associated with the object.

        Returns:
            An integer with the id, or None of not supported.
        """
        return self.__fs_impl.gid(self)

    def has_permission(self, permission: Permission) -> bool:
        """Checks permissions.

        Args:
            permission: A particular file permission, see Permission

        Returns:
            True iff the object exists and has the given permission.
        """
        return self.__fs_impl.has_permission(self, permission)

    def set_permission(self, permission: Permission,
                       value: bool = True) -> None:
        """Sets permissions.

        Args:
            permission: The permission to set.
            value: Whether to enable or disable the permission.
        """
        self.__fs_impl.set_permission(self, permission, value)

    def chmod(self, mode: int) -> None:
        """Sets permissions.

        Args:
            mode: The numerical mode describing the permissions to set. \
                  This uses standard POSIX mode definitions, see \
                  man chmod.
        """
        self.__fs_impl.chmod(self, mode)

    # Symlinks

    def symlink_to(self, target: 'Path') -> None:
        """Makes a symlink from the current path to the target.

        If this raises an OSError with the message Failed, then the \
        problem may be that the target does not exist.

        Args:
            target: The path to symlink to.
        """
        self.__fs_impl.symlink_to(self, target)

    def readlink(self, recursive: bool = False) -> 'Path':
        """Reads the target of a symbolic link.

        Note that the result may be a relative path, which should then \
        be taken relative to the directory containing the link.

        If recursive is True, this function will follow a chain of \
        symlinks until it reaches something that is not a symlink, or \
        until the maximum recursion depth is reached and a \
        RunTimeError is raised.

        Args:
            recursive: Whether to resolve recursively.

        Returns:
            The path that the symlink points to.

        Raises:
            RunTimeError: The recursion depth was reached, probably as a \
                    result of a link loop.
        """
        return self.__fs_impl.readlink(self, recursive)
