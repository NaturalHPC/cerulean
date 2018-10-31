import logging
from typing import Optional

from cerulean.path import Path, Permission


def copy(source_path: Path,
         target_path: Path,
         overwrite: str = 'never',
         copy_into: bool = True,
         copy_permissions: bool = False) -> None:
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

    Args:
        source_path: The path to the source file.
        target_path: A path to copy it to.
        overwrite: Selects behaviour when the target exists.
        copy_into: Whether to copy into target directories.
        copy_permissions: Whether to copy permissions along.
    """
    if overwrite not in ['always', 'never', 'raise']:
        raise ValueError('Invalid value for overwrite. Valid values are' +
                         '"always", "never" and "raise".')

    if target_path.is_dir() and copy_into:
        target_path = target_path / source_path.name

    _copy(source_path, target_path, overwrite, copy_permissions,
            source_path)


def _copy(source_path: Path, target_path: Path, overwrite: str,
          copy_permissions: bool, context: Optional[Path]) -> None:
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
    """
    logging.debug('Copying {} to {}'.format(source_path, target_path))
    target_path_exists = target_path.exists() or target_path.is_symlink()
    if source_path.is_symlink():
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
                    return
            # fall through and copy as file or directory
        elif overwrite == 'raise':
            raise FileExistsError('Target path exists, not overwriting')
        else:
            return

    if source_path.is_file():
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

            target_path.chmod(0o600)
            target_path.streaming_write(source_path.streaming_read())

            for permission in Permission:
                if copy_permissions:
                    target_path.set_permission(
                            permission, source_path.has_permission(permission))
                else:
                    target_path.set_permission(
                            permission,
                            perms[permission]
                            and source_path.has_permission(permission))

        elif overwrite == 'raise':
            raise FileExistsError('Target path exists, not overwriting')
        else:
            pass

    elif source_path.is_dir():
        if target_path_exists:
            if overwrite == 'always':
                if not target_path.is_dir():
                    target_path.unlink()
            elif overwrite == 'raise':
                raise FileExistsError('Target path exists, not overwriting')
            elif overwrite == 'never':
                return

        if not target_path.exists():
            logging.debug('Making new dir {}'.format(target_path))
            target_path.mkdir()

        perms = dict()
        for permission in Permission:
            perms[permission] = target_path.has_permission(permission)

        target_path.chmod(0o700)

        for entry in source_path.iterdir():
            logging.debug('Recursively copying entry {}'.format(entry))
            _copy(entry, target_path / entry.name, overwrite, copy_permissions,
                  context)

        for permission in Permission:
            if copy_permissions:
                target_path.set_permission(
                        permission, source_path.has_permission(permission))
            else:
                target_path.set_permission(
                        permission,
                        perms[permission]
                        and source_path.has_permission(permission))
    else:
        # We don't copy special entries or broken links
        logging.debug(
            'Skipping special entry or broken link {}'.format(source_path))
        pass
