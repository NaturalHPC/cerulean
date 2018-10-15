import logging
from typing import Dict

import pytest
from cerulean.copy_files import copy
from cerulean.file_system_impl import FileSystemImpl
from cerulean.path import EntryType, Path


def assert_dir_copied_correctly(copied_dir: Path) -> None:
    assert copied_dir.exists()
    assert copied_dir.is_dir()
    assert (copied_dir / 'file0').is_file()
    assert (copied_dir / 'file1').is_file()
    assert (copied_dir / 'link0').is_symlink()
    assert (copied_dir / 'link0').readlink().name == 'file0'
    assert (copied_dir / 'link1').is_symlink()
    assert (copied_dir / 'link1').readlink().name == 'link0'
    assert not (copied_dir / 'link2').exists()

    assert (copied_dir / 'link3').is_symlink()
    assert (copied_dir / 'link3').readlink().name == 'link4'
    assert (copied_dir / 'link4').is_symlink()
    assert (copied_dir / 'link4').readlink().name == 'link3'

    assert not (copied_dir / 'fifo').exists()
    assert not (copied_dir / 'chardev').exists()
    assert not (copied_dir / 'blockdev').exists()


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


def test_copy_file_single_fs(filesystem: FileSystemImpl, paths: Dict[str, Path]) -> None:
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


def test_copy_symlink_single_fs(filesystem: FileSystemImpl, paths: Dict[str, Path]) -> None:
    link = paths['multi_link']
    new_file = paths['new_file']

    assert not new_file.exists()
    copy(link, new_file)

    assert new_file.exists()
    assert new_file.is_file()
    assert new_file.size() == 12

    new_file.unlink()


def test_copy_dir_single_fs(filesystem: FileSystemImpl, paths: Dict[str, Path]) -> None:
    dir1 = paths['dir']
    new_dir = paths['new_dir']

    assert not new_dir.exists()
    copy(dir1, new_dir)

    assert_dir_copied_correctly(new_dir)

    new_dir.rmdir(recursive=True)


def test_copy_file_cross_fs(filesystem: FileSystemImpl,
                            filesystem2: FileSystemImpl,
                            paths: Dict[str, Path]) -> None:
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


def test_copy_symlink_cross_fs(filesystem: FileSystemImpl,
                               filesystem2: FileSystemImpl,
                               paths: Dict[str, Path]) -> None:
    link = paths['multi_link']
    new_file = filesystem2 / str(paths['new_file'])

    assert not new_file.exists()
    copy(link, new_file)

    assert new_file.exists()
    assert new_file.is_file()
    assert new_file.size() == 12

    new_file.unlink()


def test_copy_dir_cross_fs(filesystem: FileSystemImpl,
                           filesystem2: FileSystemImpl,
                           paths: Dict[str, Path]) -> None:
    dir1 = paths['dir']
    new_dir = filesystem2 / str(paths['new_dir'])

    assert not new_dir.exists()
    copy(dir1, new_dir)

    assert_dir_copied_correctly(new_dir)

    new_dir.rmdir(recursive=True)
