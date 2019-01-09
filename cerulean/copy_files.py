import logging
from time import perf_counter
from typing import Callable, Generator, Iterable, Optional

from cerulean.path import Path, Permission
from cerulean.file_system import UnsupportedOperationError


CopyCallback = Callable[[int, int], None]
"""The type of a callback function for the copy() function.

A callback function takes two arguments, the number of bytes copied \
thus far, and the approximate total number of bytes to copy. To \
interrupt the copy operation, raise an exception.
"""


def copy(source_path: Path,
         target_path: Path,
         overwrite: str = 'never',
         copy_into: bool = True,
         copy_permissions: bool = False,
         callback: Optional[CopyCallback] = None) -> None:
    """Copy a file or directory from one path to another.

    Note that source_path and target_path may be paths on different \
    file systems.

    The overwrite parameter decides what to do if a file is encountered \
    on the target side that would be overwritten. If overwrite equals \
    'raise', then a FileExistsError is raised. If overwrite equals \
    'always', then the file is overwritten (removed and replaced \
    if needed). If overwrite equals 'never', then the existing \
    file is kept, and the source file not copied.

    If the target is a directory and copy_into is True (the default), \
    the source will be copied into the \
    target directory. If an entry with the same name already exists \
    within the target directory, then the overwrite parameter decides \
    what happens. If copy_into is False, the source will \
    be copied on top of the directory, subject to the setting for \
    overwrite.

    If copy_permissions is True, this function will make the target's \
    permissions match those of the source, `including` SETUID, SETGID \
    and sticky bits. If copy_permissions is False, the target's \
    permissions are left at their default values (according to the \
    umask, on Unix-like systems), less any permissions that the source \
    file does not have.

    If callback is provided, it should be a function taking two \
    arguments, the current count of bytes copied and the total number \
    of bytes to be copied. It will be called once at the beginning of \
    the copy operation (with count == 0), once at the end (with count \
    == total), and in between about once per second, if the copy takes \
    long enough. Note that the total number of bytes passed to the \
    callback is approximate, and that the count may be larger than \
    the total if the estimate was off. To abort the copy, raise an \
    exception from the callback function.

    Args:
        source_path: The path to the source file.
        target_path: A path to copy it to.
        overwrite: Selects behaviour when the target exists.
        copy_into: Whether to copy into target directories.
        copy_permissions: Whether to copy permissions along.
        callback: A callback function to call regularly with progress \
                reports.
    """
    if overwrite not in ['always', 'never', 'raise']:
        raise ValueError('Invalid value for overwrite. Valid values are' +
                         '"always", "never" and "raise".')

    if target_path.is_dir() and copy_into:
        target_path = target_path / source_path.name

    size = _get_approx_size(source_path)

    if callback is not None:
        callback(0, size)

    total_written = _copy(source_path, target_path, overwrite,
                          copy_permissions, source_path, callback, 0, size)

    if callback is not None:
        callback(total_written, size)


def _copy(source_path: Path, target_path: Path, overwrite: str,
          copy_permissions: bool, context: Optional[Path],
          callback: Optional[CopyCallback], already_written: int, size: int
          ) -> int:
    """Copy a file or directory from one path to another.

    See the documentation of copy() for the required behaviour.

    The context path is guaranteed to be a prefix of source_path, on \
    the same file system.

    Args:
        source_path: The path to the source file.
        target_path: A path to copy it to.
        overwrite: Selects behaviour when the target exists.
        copy_permissions: Whether to copy permissions along.
        context: Root of the tree we are copying, or None.
        callback: A callback function to call.
        already_written: Starting count of bytes written.
        size: Approximate total size of data to copy.

    Returns:
        The approximate total number of bytes written.
    """
    logging.debug('Copying {} to {}'.format(source_path, target_path))
    target_path_exists = target_path.exists() or target_path.is_symlink()
    if source_path.is_symlink():
        if _copy_symlink(source_path, target_path, overwrite, context):
            return already_written
    if source_path.is_file():
        already_written = _copy_file(source_path, target_path, overwrite,
                                     copy_permissions, callback,
                                     already_written, size)
    elif source_path.is_dir():
        already_written = _copy_dir(source_path, target_path, overwrite,
                                    copy_permissions, context, callback,
                                    already_written, size)
    elif source_path.exists() or source_path.is_symlink():
        # We don't copy special entries or broken links
        logging.debug(
            'Skipping special entry or broken link {}'.format(source_path))
    else:
        raise FileNotFoundError(('Source path {} does not exist, cannot'
                                 ' copy').format(source_path))
    return already_written


def _copy_symlink(source_path: Path, target_path: Path, overwrite: str,
                  context: Optional[Path]) -> bool:
    """Copy a symlink.

    Copies links to an existing file within the context as links and
    returns True, otherwise returns False. If overwrite is True,
    overwrites the target.
    """
    target_path_exists = target_path.exists() or target_path.is_symlink()
    if not target_path_exists or overwrite == 'always':
        if context is not None:
            linked_path = source_path.readlink(recursive=False)
            if context in linked_path.parents:
                rel_path = linked_path.relative_to(context)
                logging.debug('Making relative link from {} to {}'.format(
                    target_path, rel_path))
                target_fs = target_path.filesystem
                if target_path.exists() or target_path.is_symlink():
                    if target_path.is_dir():
                        target_path.rmdir(recursive=True)
                    else:
                        target_path.unlink()
                target_path.symlink_to(target_fs / str(rel_path))
                return True
        return False  # fall through and copy as file or directory
    elif overwrite == 'raise':
        raise FileExistsError('Target path exists, not overwriting')
    return True  # target path exists and overwrite is never, fail silently


def _copy_file(source_path: Path, target_path: Path, overwrite: str,
               copy_permissions: bool, callback: Optional[CopyCallback],
               already_written: int, size: int) -> int:
    """Copy a file.

    Returns the number of bytes written.
    """
    target_path_exists = target_path.exists() or target_path.is_symlink()

    if not target_path_exists or overwrite == 'always':
        logging.debug('Copying file from {} to {}'.format(
                source_path, target_path))

        if not target_path.is_symlink() and target_path.is_dir():
            target_path.rmdir(recursive=True)
        elif target_path.exists():
            target_path.unlink()
        target_path.touch()

        perms = dict()
        for permission in Permission:
            perms[permission] = target_path.has_permission(permission)

        try:
            target_path.chmod(0o600)
        except UnsupportedOperationError:
            pass

        target_path.streaming_write(
                _call_back(callback, perf_counter() + 1.0, already_written,
                           size, source_path.streaming_read()))

        already_written += source_path.size()

        try:
            for permission in Permission:
                if copy_permissions:
                    target_path.set_permission(
                            permission, source_path.has_permission(permission))
                else:
                    target_path.set_permission(
                            permission,
                            perms[permission]
                            and source_path.has_permission(permission))
        except UnsupportedOperationError:
            pass

    elif overwrite == 'raise':
        raise FileExistsError('Target path exists, not overwriting')

    return already_written


def _call_back(callback: Optional[CopyCallback], next_callback: float,
               already_written: int, total_size: int, stream: Iterable[bytes]
               ) -> Generator[bytes, None, None]:
    """Calls the callback every second or so.
    """
    written_here = 0
    for chunk in stream:
        yield chunk
        written_here += len(chunk)
        if perf_counter() >= next_callback:
            if callback is not None:
                callback(already_written + written_here, total_size)
            next_callback = perf_counter() + 1.0


def _copy_dir(source_path: Path, target_path: Path, overwrite: str,
              copy_permissions: bool, context: Optional[Path],
              callback: Optional[CopyCallback], already_written: int, size: int
              ) -> int:
    """Copy a directory recursively.
    """
    target_path_exists = target_path.exists() or target_path.is_symlink()

    if target_path_exists:
        if overwrite == 'always':
            if not target_path.is_dir():
                target_path.unlink()
        elif overwrite == 'raise':
            raise FileExistsError('Target path exists, not overwriting')
        elif overwrite == 'never':
            return already_written

    if not target_path.exists():
        logging.debug('Making new dir {}'.format(target_path))
        target_path.mkdir()

    perms = dict()
    for permission in Permission:
        perms[permission] = target_path.has_permission(permission)

    try:
        target_path.chmod(0o700)
    except UnsupportedOperationError:
        pass

    for entry in source_path.iterdir():
        logging.debug('Recursively copying entry {}'.format(entry))
        already_written = _copy(entry, target_path / entry.name, overwrite,
                                copy_permissions, context, callback,
                                already_written, size)

    try:
        for permission in Permission:
            if copy_permissions:
                target_path.set_permission(
                        permission, source_path.has_permission(permission))
            else:
                target_path.set_permission(
                        permission,
                        perms[permission]
                        and source_path.has_permission(permission))
    except UnsupportedOperationError:
        pass

    return already_written


def _get_approx_size(path: Path) -> int:
    count = 0
    if not path.is_symlink() and path.is_file():
        count += path.size()
    elif not path.is_symlink() and path.is_dir():
        for subdir in path.iterdir():
            count += _get_approx_size(subdir)
    return count
