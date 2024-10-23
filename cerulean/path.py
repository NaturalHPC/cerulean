import stat
from enum import Enum
import pathlib
from pathlib import PurePosixPath, PureWindowsPath
from typing import (Callable, Generator, Iterable, List, Optional, Tuple,
                    TYPE_CHECKING, Union)


if TYPE_CHECKING:
    from cerulean.file_system_impl import FileSystemImpl


class EntryType(Enum):
    """Type of a directory entry."""
    DIRECTORY = 1
    FILE = 2
    SYMBOLIC_LINK = 3
    CHARACTER_DEVICE = 4
    BLOCK_DEVICE = 5
    FIFO = 6
    SOCKET = 7


class Permission(Enum):
    """Readable constants for various file permissions."""
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


AbstractPath = Union[pathlib.Path, PurePosixPath, PureWindowsPath]


class Path:
    """A path on a file system.

    This class implements the pathlib.PurePosixPath interface fully, and a
    pathlib.PosixPath-like interface, although it has some omissions, additions, and
    improvements to make it more compatible with remote and non-standard file systems.

    To make a Path, create a FileSystem first, then use the / operator on it, e.g.
    ``fs / 'home' / 'user'``. Do not construct objects of this class directly.

    Paths can be compared for (non-)equality using == and !=. Paths that compare unequal
    could still refer to the same file, if it is accessible in multiple ways. For
    instance, a local path /tmp would compare unequal to a path /tmp on an
    SftpFileSystem, even if the SftpFileSystem is connected to localhost, and the paths
    do in fact refer to the same directory.

    Attributes:
        filesystem: The file system that this path is on.

    """
    def __init__(
            self, filesystem: 'FileSystemImpl', path: AbstractPath) -> None:
        """Create a Path object.

        Do not use this directly, instead do ``fs / 'path' / 'to' / 'file'`` to create
        a file.
        """
        if isinstance(path, Path):
            raise RuntimeError('AAAAAAARGH!')
        self.__path = path
        self.filesystem = filesystem

    def __str__(self) -> str:
        """Return string representation of this Path."""
        return str(self.__path)

    def __repr__(self) -> str:
        """Return an object-like representation of this Path."""
        return 'Path({}, {})'.format(self.filesystem, self)

    # PurePath operators
    def __eq__(self, other: object) -> bool:
        """Return True iff the paths are equal."""
        if not isinstance(other, Path):
            return NotImplemented
        return (self.filesystem == other.filesystem
                and self.__path == other.__path)

    def __neq__(self, other: object) -> bool:
        """Return True iff the paths are not equal."""
        if not isinstance(other, Path):
            return NotImplemented
        return not (self == other)

    def __lt__(self, other: object) -> bool:
        """Return True iff this path sorts before other."""
        if not isinstance(other, Path):
            return NotImplemented
        if self.filesystem != other.filesystem:
            raise TypeError('\'<\' not supported between different file systems')
        return self.__path < other.__path

    def __gt__(self, other: object) -> bool:
        """Return True iff this path sorts after other."""
        return other < self

    def __le__(self, other: object) -> bool:
        """Return True iff this path is equal to or sorts before other."""
        return self < other or self == other

    def __ge__(self, other: object) -> bool:
        """Return True iff this path is equal to or sorts after other."""
        return other < self or self == other

    def __truediv__(self, suffix: Union[str, 'Path']) -> 'Path':
        """Append a suffix to the path and return the result."""
        if isinstance(suffix, Path):
            path = self.__path / suffix.__path
        else:
            path = self.__path / suffix.strip('/')
        return Path(self.filesystem, path)

    # PurePath attributes and functions

    @property
    def parts(self) -> Tuple[str, ...]:
        """A tuple containing the path's components."""
        return self.__path.parts

    @property
    def drive(self) -> str:
        """The drive letter (including the colon), if any."""
        return self.__path.drive

    @property
    def root(self) -> str:
        """A string representing the root of the filesystem."""
        return self.__path.root

    @property
    def anchor(self) -> str:
        """The concatenation of the drive and the root."""
        return self.__path.anchor

    @property
    def parents(self) -> List['Path']:
        """A sequence containing the logical ancestors of the path."""
        def make_path(path: AbstractPath) -> 'Path':
            return Path(self.filesystem, path)

        return list(map(make_path, self.__path.parents))

    @property
    def parent(self) -> 'Path':
        """The logical parent of the path."""
        return Path(self.filesystem, self.__path.parent)

    @property
    def name(self) -> str:
        """The name of the file or directory.

        This excludes parents but includes the suffix.
        """
        return self.__path.name

    @property
    def suffix(self) -> str:
        """The file extension of the file or directory, if any."""
        return self.__path.suffix

    @property
    def suffixes(self) -> List[str]:
        """A list of all the extensions in the file name."""
        return self.__path.suffixes

    @property
    def stem(self) -> str:
        """The stem of this path.

        This is the name of the file or directory, excluding parents and
        excluding the suffix.
        """
        return self.__path.stem

    def as_posix(self) -> str:
        """Returns the path as a string with forward slashes."""
        return self.__path.as_posix()

    def as_uri(self) -> str:
        """Returns a URI representing the path.

        This is not yet implemented, please file an issue if you need it.
        """
        raise NotImplementedError('Not yet implemented, please file an issue')

    def is_absolute(self) -> bool:
        """Returns whether the path is absolute."""
        return self.__path.is_absolute()

    def is_reserved(self) -> bool:
        """Return whether the path is reserved.

        This can only happen on Windows on a LocalFileSystem.
        """
        return self.__path.is_reserved()

    def joinpath(self, *other: Union[str, 'Path']) -> 'Path':
        """Joins another path or string onto the back of this one.

        Args:
            other: The other path to append to this one.

        Returns:
            The combined path.
        """
        def get_path(segment: Union[str, 'Path']) -> str:
            if isinstance(segment, str):
                return segment
            else:
                return str(segment.__path)

        native_others = map(get_path, other)
        return Path(self.filesystem, self.__path.joinpath(*native_others))

    # TODO: match

    def relative_to(self, *other: Union[str, 'Path']) -> 'Path':
        """Returns a version of this path relative to another path.

        Both paths must be on the same file system.

        Args:
            other: The path to use as a reference.
        """
        def get_path(segment: Union[str, 'Path']) -> str:
            if isinstance(segment, str):
                return segment
            else:
                return str(segment.__path)

        native_others = map(get_path, other)
        return Path(self.filesystem, self.__path.relative_to(*native_others))

    def with_name(self, name: str) -> 'Path':
        """Return a new path with the last component set to `name`.

        Args:
            name: The new name to use.
        """
        return Path(self.filesystem, self.__path.with_name(name))

    def with_suffix(self, suffix: str) -> 'Path':
        """Return a new path with the suffix set to `suffix`.

        Args:
            suffix: The new suffix to use.
        """
        return Path(self.filesystem, self.__path.with_suffix(suffix))

    # Existence and contents

    def exists(self) -> bool:
        """Returns true iff a filesystem object exists at this path.

        If the path denotes a symlink, returns whether the symlink points to an
        existing filesystem object, recursively. If the symlink is part of a
        link loop, returns False.

        Returns:
            True iff the path exists on the filesystem.
        """
        return self.filesystem._exists(self.__path)

    def mkdir(
            self, mode: Optional[int] = None, parents: bool = False,
            exists_ok: bool = False) -> None:
        """Makes a directory with the given access rights.

        If mode is not set or None, assigns permissions according to the
        current umask. If parents is True, makes parent directories as needed.
        If exists_ok is True, silently ignores if the directory already exists.

        Args:
            mode: A numerical Posix access permissions mode.
            parents: Whether to make parent directories.
            exists_ok: Don't raise if target already exists.
        """
        self.filesystem._mkdir(self.__path, mode, parents, exists_ok)

    def iterdir(self) -> Generator['Path', None, None]:
        """Iterates through a directory's contents.

        Yields:
            Paths of entries in the directory.
        """
        for entry in self.filesystem._iterdir(self.__path):
            yield Path(self.filesystem, entry)

    def walk(
            self, topdown: bool = True,
            onerror: Optional[Callable[[OSError], None]] = None,
            followlinks: bool = False
            ) -> Generator[Tuple['Path', List[str], List[str]], None, None]:
        """Walks a directory hierarchy recursively.

        This is a version of Python's ``os.walk()`` function adapted to be a
        little bit more ``pathlib``-like. It walks the directory and its
        subdirectories, yielding a tuple (dirpath, dirnames, filenames) for
        each directory. These are the path of the directory, as a
        :class:`Path`, a list of strings containing the names of the
        subdirectories inside this directory, and a list of strings containing
        the names of the non-directories in this directory respectively.

        If ``topdown`` is True, the triple for a directory will be produced
        before the triples of its subdirectories; if it is False, it will be
        produced after (pre- and post-order traversal respectively).

        If ``onerror`` is set, the function it is set to will be called if an
        error occurs, and passed an instance of OSError. The callback can
        handle the error in some way, or raise it to end the traversal. The
        OSError object will have an attribute ``filename`` containing the name
        of the file that triggered the problem as a string.

        If ``followlinks`` is True, this function will recurse into symlinks
        that point to directories, if it is False, it will silently skip them.

        Yields:
            Tuples (dirpath, dirnames, filenames), as above.
        """
        dirnames = list()  # type: List[str]
        filenames = list()  # type: List[str]
        try:
            for entry in self.iterdir():
                if entry.is_dir():
                    dirnames.append(str(entry.relative_to(self)))
                else:
                    filenames.append(str(entry.relative_to(self)))
        except OSError as err:
            if onerror is not None:
                onerror(err)

        if topdown:
            yield self, dirnames, filenames

        for dirname in dirnames:
            subdir = self / dirname
            if not subdir.is_symlink() or followlinks:
                yield from subdir.walk(topdown, onerror, followlinks)

        if not topdown:
            yield self, dirnames, filenames

    def rmdir(self, recursive: bool = False) -> None:
        """Removes a directory.

        If recursive is True, remove all files and directories inside as well. If
        recursive is False, the directory must be empty.
        """
        self.filesystem._rmdir(self.__path, recursive)

    def touch(self) -> None:
        """Updates the access and modification times of file.

        If the file does not exist, it will be created, which is often what this
        function is used for.
        """
        self.filesystem._touch(self.__path)

    def streaming_read(self) -> Generator[bytes, None, None]:
        """Streams data from a file.

        This is a generator function that generates bytes objects containing consecutive
        chunks of the file.
        """
        return self.filesystem._streaming_read(self.__path)

    def streaming_write(self, data: Iterable[bytes]) -> None:
        """Streams data to a file.

        Creates a new file (overwriting any existing file) at the current path, and
        writes data to it from the given iterable.

        Args:
            data: An iterable of bytes containing data to be written.
        """
        self.filesystem._streaming_write(self.__path, data)

    def read_bytes(self) -> bytes:
        """Reads file contents as a bytes object.

        Returns:
            The contents of the file.
        """
        data = bytearray()
        for chunk in self.streaming_read():
            data.extend(chunk)
        return bytes(data)

    def read_text(self, encoding: str = 'utf-8') -> str:
        """Reads file contents as a string.

        Assumes UTF-8 encoding.

        Args:
            encoding: The encoding to assume.

        Returns:
            The contents of the file.
        """
        return self.read_bytes().decode(encoding)

    def write_bytes(self, data: bytes) -> None:
        """Writes bytes to the file.

        Overwrites the file if it exists.

        Args:
            data: The data to be written.
        """
        self.streaming_write([data])

    def write_text(self, text: str, encoding: str = 'utf-8') -> None:
        """Writes text to a file.

        Overwrites the file if it exists.

        Args:
            text: The text to be written.
            encoding: The encoding to use.
        """
        self.write_bytes(text.encode(encoding))

    def rename(self, target: 'Path') -> None:
        """Renames a file.

        The new path must be in the same filesystem. If the new path exists, then it
        will be overwritten.

        Args:
            target: The new path of the file.
        """
        if target.filesystem != self:
            raise RuntimeError('Cannot rename across file systems')
        self.filesystem._rename(self.__path, target.__path)

    def unlink(self) -> None:
        """Removes a file or device node.

        For removing directories, see rmdir().
        """
        self.filesystem._unlink(self.__path)

    def remove(self) -> None:
        """Removes a file, link, device or directory.

        Directories are removed recursively, links, devices and files are deleted.
        Link targets are left in place. Returns without error if there is nothing
        there already.

        Use this method to ensure that there is no entry at this path.
        """
        if self.exists() or self.is_symlink():
            if self.is_symlink():
                self.unlink()
            elif self.is_dir():
                self.rmdir(recursive=True)
            else:
                self.unlink()

    # File type and size

    def is_dir(self) -> bool:
        """Returns whether the path is a directory.

        Returns:
            True iff the path exists and is a directory, or a symbolic
            link pointing to a directory.
        """
        return self.filesystem._is_dir(self.__path)

    def is_file(self) -> bool:
        """Returns whether the path is a file.

        Returns:
            True iff the path exists and is a file, or a symbolic
            link pointing to a file.
        """
        return self.filesystem._is_file(self.__path)

    def is_symlink(self) -> bool:
        """Returns whether the path is a symlink.

        Returns:
            True iff the path exists and is a symbolic link.
        """
        return self.filesystem._is_symlink(self.__path)

    def entry_type(self) -> EntryType:
        """Returns the kind of directory entry type the path points to.

        Returns:
            An :class:`EntryType` enum value describing the filesystem entry.

        Raises:
            FileNotFoundError: If there is no file here.
        """
        return self.filesystem._entry_type(self.__path)

    def size(self) -> int:
        """Returns the size of the file.

        Returns:
            An integer with the number of bytes in the file.
        """
        return self.filesystem._size(self.__path)

    # Permissions

    def uid(self) -> Optional[int]:
        """Returns the user id of the owner of the object.

        Returns:
            An integer with the id, or None if not supported.
        """
        return self.filesystem._uid(self.__path)

    def gid(self) -> Optional[int]:
        """Returns the group id associated with the object.

        Returns:
            An integer with the id, or None of not supported.
        """
        return self.filesystem._gid(self.__path)

    def has_permission(self, permission: Permission) -> bool:
        """Checks permissions.

        Args:
            permission: A particular file permission, see Permission

        Returns:
            True iff the object exists and has the given permission.
        """
        return self.filesystem._has_permission(self.__path, permission)

    def set_permission(self, permission: Permission,
                       value: bool = True) -> None:
        """Sets permissions.

        Args:
            permission: The permission to set.
            value: Whether to enable or disable the permission.
        """
        self.filesystem._set_permission(self.__path, permission, value)

    def chmod(self, mode: int) -> None:
        """Sets permissions.

        Args:
            mode: The numerical mode describing the permissions to set. This uses
                    standard POSIX mode definitions, see man chmod.
        """
        self.filesystem._chmod(self.__path, mode)

    # Symlinks

    def symlink_to(self, target: 'Path') -> None:
        """Makes a symlink from the current path to the target.

        If this raises an OSError with the message Failed, then the problem may be that
        the target does not exist.

        Args:
            target: The path to symlink to.

        Raises:
            FileExistsError: if you try to overwrite an existing entry with a symlink.
        """
        if self.filesystem != target.filesystem:
            raise RuntimeError('Cannot symlink across filesystems')
        self.filesystem._symlink_to(self.__path, target.__path)

    def readlink(self, recursive: bool = False) -> 'Path':
        """Reads the target of a symbolic link.

        Note that the result may be a relative path, which should then be taken relative
        to the directory containing the link.

        If recursive is True, this function will follow a chain of symlinks until it
        reaches something that is not a symlink, or until the maximum recursion depth is
        reached and a RunTimeError is raised.

        Args:
            recursive: Whether to resolve recursively.

        Returns:
            The path that the symlink points to.

        Raises:
            RunTimeError: The recursion depth was reached, probably as a result of a
                    link loop.
        """
        return self.filesystem._readlink(self.__path, recursive)
