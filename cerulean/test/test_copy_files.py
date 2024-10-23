from typing import Dict, Generator

import pytest
from cerulean import copy
from cerulean.file_system_impl import FileSystemImpl
from cerulean import Path, Permission


def assert_dir_files_copied_correctly(copied_dir: Path) -> None:
    assert copied_dir.exists()
    assert copied_dir.is_dir()
    assert (copied_dir / 'file0').is_file()
    assert (copied_dir / 'file1').is_file()


def assert_dir_links_copied_correctly(copied_dir: Path) -> None:
    assert (copied_dir / 'link0').is_symlink()
    assert (copied_dir / 'link0').readlink().name == 'file0'
    assert (copied_dir / 'link1').is_symlink()
    assert (copied_dir / 'link1').readlink().name == 'link0'
    assert not (copied_dir / 'link2').exists()

    assert (copied_dir / 'link3').is_symlink()
    assert (copied_dir / 'link3').readlink().name == 'link4'
    assert (copied_dir / 'link4').is_symlink()
    assert (copied_dir / 'link4').readlink().name == 'link3'


def assert_dir_links_stubbed_correctly(copied_dir: Path) -> None:
    assert (copied_dir / 'link0').is_file()
    assert (copied_dir / 'link1').is_file()
    assert not (copied_dir / 'link2').exists()


def assert_dir_devices_copied_correctly(copied_dir: Path) -> None:
    assert not (copied_dir / 'fifo').exists()
    assert not (copied_dir / 'blockdev').exists()
    # We don't test chardevs, because putting them into a Docker container is
    # tricky these days.


def assert_dir_copied_correctly(copied_dir: Path, filesystem: FileSystemImpl,
                                filesystem2: FileSystemImpl) -> None:
    assert_dir_files_copied_correctly(copied_dir)
    if filesystem._supports('devices') and filesystem2._supports('devices'):
        assert_dir_devices_copied_correctly(copied_dir)
    if filesystem._supports('symlinks') and filesystem2._supports('symlinks'):
        assert_dir_links_copied_correctly(copied_dir)


def test_copy_file_args(filesystem: FileSystemImpl, paths: Dict[str, Path]) -> None:
    file0 = paths['file']
    with pytest.raises(ValueError):
        copy(file0, file0, overwrite='nonexistentoption')


def test_copy_into(filesystem: FileSystemImpl, paths: Dict[str, Path]) -> None:
    file0 = paths['file']
    newdir = paths['new_dir']
    newdir.mkdir()
    copy(file0, newdir)
    assert (newdir / file0.name).exists()
    newdir.rmdir(recursive=True)


def test_copy_dir_onto_nonexistent(
        filesystem: FileSystemImpl, paths: Dict[str, Path]) -> None:
    dir0 = paths['dir']
    newdir = paths['new_dir']
    copy(dir0, newdir, overwrite='always', copy_into=False)
    assert newdir.is_dir()
    newdir.rmdir(recursive=True)


def test_copy_file_onto_dir(
        filesystem: FileSystemImpl, paths: Dict[str, Path]) -> None:
    file1 = paths['file']
    newdir = paths['new_dir']

    newdir.mkdir()
    copy(file1, newdir, overwrite='always', copy_into=False)
    assert newdir.is_file()
    newdir.unlink()


def test_copy_file_single_fs(
        filesystem: FileSystemImpl, paths: Dict[str, Path]) -> None:
    file1 = paths['file']
    new_file = paths['new_file']

    assert not new_file.exists()
    copy(file1, new_file)
    assert new_file.exists()
    assert new_file.is_file()
    new_file.unlink()

    copy(file1, new_file, overwrite='raise')
    assert new_file.exists()
    new_file.unlink()

    copy(file1, new_file, overwrite='always')
    assert new_file.exists()
    new_file.unlink()

    other_file = paths['other_file']
    copy(file1, other_file)
    assert other_file.size() == 0

    with pytest.raises(FileExistsError):
        copy(file1, other_file, overwrite='raise')

    copy(file1, other_file, overwrite='always')
    assert other_file.size() == 12
    other_file.unlink()
    other_file.touch()

    with pytest.raises(FileNotFoundError):
        copy(paths['root'] / 'doesnotexist', new_file)


def test_copy_file_permissions(
        filesystem: FileSystemImpl, paths: Dict[str, Path]) -> None:
    if not filesystem._supports('permissions'):
        return

    file1 = paths['executable']
    file2 = paths['private']
    new_file = paths['new_file']

    assert file1.has_permission(Permission.OWNER_READ)
    assert file1.has_permission(Permission.OWNER_WRITE)
    assert file1.has_permission(Permission.OWNER_EXECUTE)
    assert file1.has_permission(Permission.GROUP_READ)
    assert not file1.has_permission(Permission.GROUP_WRITE)
    assert not file1.has_permission(Permission.GROUP_EXECUTE)
    assert file1.has_permission(Permission.OTHERS_READ)
    assert not file1.has_permission(Permission.OTHERS_WRITE)
    assert not file1.has_permission(Permission.OTHERS_EXECUTE)
    copy(file1, new_file, copy_permissions=True)
    assert new_file.has_permission(Permission.OWNER_READ)
    assert new_file.has_permission(Permission.OWNER_WRITE)
    assert new_file.has_permission(Permission.OWNER_EXECUTE)
    assert new_file.has_permission(Permission.GROUP_READ)
    assert not new_file.has_permission(Permission.GROUP_WRITE)
    assert not new_file.has_permission(Permission.GROUP_EXECUTE)
    assert new_file.has_permission(Permission.OTHERS_READ)
    assert not new_file.has_permission(Permission.OTHERS_WRITE)
    assert not new_file.has_permission(Permission.OTHERS_EXECUTE)

    new_file.unlink()

    for permission in Permission:
        assert file2.has_permission(permission) == (
                permission in [Permission.OWNER_READ, Permission.OWNER_WRITE])

    copy(file2, new_file, copy_permissions=True)
    for permission in Permission:
        assert file2.has_permission(permission) == (
                permission in [Permission.OWNER_READ, Permission.OWNER_WRITE])

    copy(file1, new_file, overwrite='always', copy_permissions=True)
    assert new_file.has_permission(Permission.OWNER_READ)
    assert new_file.has_permission(Permission.OWNER_WRITE)
    assert new_file.has_permission(Permission.OWNER_EXECUTE)
    assert new_file.has_permission(Permission.GROUP_READ)
    assert not new_file.has_permission(Permission.GROUP_WRITE)
    assert not new_file.has_permission(Permission.GROUP_EXECUTE)
    assert new_file.has_permission(Permission.OTHERS_READ)
    assert not new_file.has_permission(Permission.OTHERS_WRITE)
    assert not new_file.has_permission(Permission.OTHERS_EXECUTE)

    new_file.chmod(0o644)

    copy(file2, new_file, overwrite='always', copy_permissions=True)
    for permission in Permission:
        assert file2.has_permission(permission) == (
                permission in [Permission.OWNER_READ, Permission.OWNER_WRITE])

    new_file.unlink()


def test_no_copy_file_permissions(
        filesystem: FileSystemImpl, paths: Dict[str, Path]) -> None:
    if not filesystem._supports('permissions'):
        return

    file1 = paths['executable']
    file2 = paths['private']
    new_file = paths['new_file']

    copy(file1, new_file, copy_permissions=False)
    assert not new_file.has_permission(Permission.OWNER_EXECUTE)

    new_file.unlink()
    new_file.touch()
    new_file.chmod(0o660)
    copy(file1, new_file, overwrite='always', copy_permissions=False)
    assert new_file.has_permission(Permission.OWNER_READ)
    assert new_file.has_permission(Permission.OWNER_WRITE)
    assert not new_file.has_permission(Permission.OWNER_EXECUTE)
    assert not new_file.has_permission(Permission.GROUP_WRITE)
    assert new_file.has_permission(Permission.OTHERS_READ)

    new_file.unlink()
    copy(file2, new_file, overwrite='always', copy_permissions=False)
    for permission in Permission:
        assert file2.has_permission(permission) == (
                permission in [Permission.OWNER_READ, Permission.OWNER_WRITE])

    new_file.unlink()


def test_copy_callback(filesystem: FileSystemImpl, paths: Dict[str, Path]) -> None:
    def dummy_data() -> Generator[bytes, None, None]:
        for _ in range(20):
            yield bytes(1024 * 1024)

    newdir = paths['new_dir']
    test_source = newdir / 'source'
    test_target = newdir / 'target'

    newdir.mkdir()
    try:
        test_source.streaming_write(dummy_data())

        num_calls = 0

        def callback(count: int, total: int) -> None:
            nonlocal num_calls
            num_calls += 1

        copy(test_source, test_target, callback=callback)
        assert num_calls >= 2
    finally:
        newdir.rmdir(recursive=True)


def test_copy_callback_abort(
        filesystem: FileSystemImpl, paths: Dict[str, Path]) -> None:
    test_source = paths['file']
    test_target = paths['new_file']

    try:
        def callback(count: int, total: int) -> None:
            raise RuntimeError()

        with pytest.raises(RuntimeError):
            copy(test_source, test_target, callback=callback)

        assert not test_target.exists() or test_target.size() == 0
    finally:
        if test_target.exists():
            test_target.unlink()


def test_copy_symlink_single_fs(
        filesystem: FileSystemImpl, paths: Dict[str, Path]) -> None:
    if filesystem._supports('symlinks'):
        link = paths['multi_link']
        new_file = paths['new_file']

        assert not new_file.exists()
        copy(link, new_file)

        assert new_file.exists()
        assert new_file.is_file()
        assert new_file.size() == 12

        new_file.unlink()


def test_copy_dir_single_fs(
        filesystem: FileSystemImpl, paths: Dict[str, Path]) -> None:
    dir1 = paths['dir']
    new_dir = paths['new_dir']

    assert not new_dir.exists()
    copy(dir1, new_dir)

    assert_dir_copied_correctly(new_dir, filesystem, filesystem)

    new_dir.rmdir(recursive=True)


def test_copy_dir_single_fs2(
        filesystem: FileSystemImpl, paths: Dict[str, Path]) -> None:
    dir1 = paths['dir']
    new_dir = paths['new_dir']

    assert not new_dir.exists()
    copy(dir1, new_dir, overwrite='raise')
    assert_dir_copied_correctly(new_dir, filesystem, filesystem)

    with pytest.raises(FileExistsError):
        copy(dir1, new_dir, overwrite='raise', copy_into=False)

    new_dir.rmdir(recursive=True)


def test_copy_dir_single_fs3(
        filesystem: FileSystemImpl, paths: Dict[str, Path]) -> None:
    dir1 = paths['dir']
    new_dir = paths['new_dir']

    assert not new_dir.exists()
    copy(dir1, new_dir)
    assert_dir_copied_correctly(new_dir, filesystem, filesystem)

    (new_dir / 'file0').unlink()

    copy(dir1, new_dir, overwrite='always', copy_into=False)
    assert (new_dir / 'file0').exists()

    new_dir.rmdir(recursive=True)

    copy(dir1, new_dir, overwrite='always', copy_into=False)
    assert_dir_copied_correctly(new_dir, filesystem, filesystem)

    new_dir.rmdir(recursive=True)

    new_dir.mkdir()
    copy(dir1, new_dir, overwrite='always', copy_into=True)
    assert (new_dir / 'links' / 'file0').exists()

    new_dir.rmdir(recursive=True)


def test_copy_file_cross_fs(
        filesystem: FileSystemImpl, filesystem2: FileSystemImpl, paths: Dict[str, Path]
        ) -> None:
    file1 = paths['file']
    new_file = filesystem2 / str(paths['new_file'])

    assert not new_file.exists()
    copy(file1, new_file)
    assert new_file.exists()
    assert new_file.is_file()
    new_file.unlink()

    copy(file1, new_file, overwrite='raise')
    assert new_file.exists()
    new_file.unlink()

    copy(file1, new_file, overwrite='always')
    assert new_file.exists()
    new_file.unlink()

    other_file = paths['other_file']
    copy(file1, other_file)
    assert other_file.size() == 0

    with pytest.raises(FileExistsError):
        copy(file1, other_file, overwrite='raise')

    copy(file1, other_file, overwrite='always')
    assert other_file.size() == 12
    other_file.unlink()
    other_file.touch()


def test_copy_symlink_cross_fs(
        filesystem: FileSystemImpl, filesystem2: FileSystemImpl, paths: Dict[str, Path]
        ) -> None:
    if filesystem._supports('symlinks') and filesystem2._supports('symlinks'):
        link = paths['multi_link']
        new_file = filesystem2 / str(paths['new_file'])

        assert not new_file.exists()
        copy(link, new_file)

        assert new_file.exists()
        assert new_file.is_file()
        assert new_file.size() == 12

        new_file.unlink()


def test_copy_dir_cross_fs(
        filesystem: FileSystemImpl, filesystem2: FileSystemImpl, paths: Dict[str, Path]
        ) -> None:
    dir1 = paths['dir']
    new_dir = filesystem2 / str(paths['new_dir'])

    assert not new_dir.exists()
    copy(dir1, new_dir)

    assert_dir_copied_correctly(new_dir, filesystem, filesystem2)

    new_dir.rmdir(recursive=True)
