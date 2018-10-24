import logging
from typing import Optional

from cerulean.path import Path


def copy(source_path: Path,
         target_path: Path,
         overwrite: str = 'never',
         copy_into: bool = True) -> None:
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

    Args:
        source_path: The path to the source file.
        target_path: A path to copy it to.
        overwrite: Selects behaviour when the target exists.
        copy_into: Whether to copy into target directories.
    """
    if overwrite not in ['always', 'never', 'raise']:
        raise ValueError('Invalid value for overwrite. Valid values are' +
                         '"always", "never" and "raise".')

    if target_path.is_dir() and copy_into:
        target_path = target_path / source_path.name

    _copy(source_path, target_path, overwrite, source_path)


def _copy(source_path: Path, target_path: Path, overwrite: str,
          context: Optional[Path]) -> None:
    """Copy a file or directory from one path to another.

    See the documentation of copy() for the required behaviour.

    The context path is guaranteed to be a prefix of source_path, on \
    the same file system.

    Args:
        source_path: The path to the source file.
        target_path: A path to copy it to.
        overwrite: Selects behaviour when the target exists.
        context: Root of the tree we are copying, or None.
    """
    logging.debug('Copying {} to {}'.format(source_path, target_path))
    if source_path.is_symlink():
        if context is not None:
            linked_path = source_path.readlink(recursive=False)
            if context in linked_path.parents:
                rel_path = linked_path.relative_to(context)
                logging.debug('Making relative link from {} to {}'.format(
                    target_path, rel_path))
                target_fs = target_path.filesystem
                target_path.symlink_to(target_fs / str(rel_path))
                return

    if source_path.is_file():
        if not target_path.exists() or overwrite == 'always':
            # TODO: permissions
            # touch with correct mode
            try:
                logging.debug('Copying file from {} to {}'.format(
                    source_path, target_path))
                target_path.streaming_write(source_path.streaming_read())
            except PermissionError:
                target_path.unlink()
                # touch with correct mode
                target_path.streaming_write(source_path.streaming_read())
        elif overwrite == 'raise':
            raise FileExistsError('Target path exists, not overwriting')
        else:
            pass

    elif source_path.is_dir():
        if overwrite == 'always' and not target_path.is_dir():
            target_path.unlink()

        if not target_path.exists():
            mode = 0o777  # TODO: read original mode and use
            logging.debug('Making new dir {}'.format(target_path))
            target_path.mkdir(mode)

        for entry in source_path.iterdir():
            logging.debug('Recursively copying entry {}'.format(entry))
            _copy(entry, target_path / entry.name, overwrite, context)
    else:
        # We don't copy special entries or broken links
        logging.debug(
            'Skipping special entry or broken link {}'.format(source_path))
        pass
