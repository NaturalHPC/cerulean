import logging

import pytest
from cerulean.copy_files import copy
from cerulean.path import EntryType


def assert_dir_copied_correctly(copied_dir):
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


def test_copy_file_args(filesystem, paths):
    file0 = paths['file']
    with pytest.raises(ValueError):
        copy(file0, file0, overwrite='nonexistentoption')


def test_copy_into(filesystem, paths):
    file0 = paths['file']
    newdir = paths['new_dir']
    newdir.mkdir()
    copy(file0, newdir)
    assert (newdir / file0.name).exists()
    newdir.rmdir(recursive=True)


def test_copy_file_single_fs(filesystem, paths):
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


def test_copy_symlink_single_fs(filesystem, paths):
    link = paths['multi_link']
    new_file = paths['new_file']

    assert not new_file.exists()
    copy(link, new_file)

    assert new_file.exists()
    assert new_file.is_file()
    assert new_file.size() == 12

    new_file.unlink()


def test_copy_dir_single_fs(filesystem, paths):
    dir1 = paths['dir']
    new_dir = paths['new_dir']

    assert not new_dir.exists()
    copy(dir1, new_dir)

    assert_dir_copied_correctly(new_dir)

    new_dir.rmdir(recursive=True)


def test_copy_file_cross_fs(filesystem, filesystem2, paths):
    file1 = paths['file']
    new_file = filesystem2 / paths['new_file']

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


def test_copy_symlink_cross_fs(filesystem, filesystem2, paths):
    link = paths['multi_link']
    new_file = filesystem2 / paths['new_file']

    assert not new_file.exists()
    copy(link, new_file)

    assert new_file.exists()
    assert new_file.is_file()
    assert new_file.size() == 12

    new_file.unlink()


def test_copy_dir_cross_fs(filesystem, filesystem2, paths):
    dir1 = paths['dir']
    new_dir = filesystem2 / paths['new_dir']

    assert not new_dir.exists()
    copy(dir1, new_dir)

    assert_dir_copied_correctly(new_dir)

    new_dir.rmdir(recursive=True)
