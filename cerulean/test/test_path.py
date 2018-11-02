import pathlib
from typing import Dict, List

from cerulean import LocalFileSystem
from cerulean import Path


def test_create(local_filesystem: LocalFileSystem) -> None:
    new_path = Path(local_filesystem, pathlib.Path('/'))
    assert str(new_path) == '/'


def test_joinpath(paths: Dict[str, Path]) -> None:
    new_path = paths['root'].joinpath('links')
    assert paths['dir'] == new_path


def test_divides(paths: Dict[str, Path]) -> None:
    new_path = paths['dir'] / 'file0'
    assert new_path == paths['file']

    new_path = paths['dir']
    new_path /= 'file0'
    assert new_path == paths['file']


def test_with_name(local_filesystem: LocalFileSystem) -> None:
    new_path = (local_filesystem / 'home').with_name('usr')
    assert str(new_path) == '/usr'


def test_with_suffix(local_filesystem: LocalFileSystem) -> None:
    new_path = (local_filesystem / 'test.txt').with_suffix('.dat')
    assert str(new_path) == '/test.dat'


def test_read_bytes(paths: Dict[str, Path]) -> None:
    data = paths['file'].read_bytes()
    assert data.decode('utf-8') == 'Hello World\n'


def test_write_text(paths: Dict[str, Path]) -> None:
    text = 'Hello World\n'
    paths['new_file'].write_text(text)
    text2 = paths['new_file'].read_text()
    paths['new_file'].unlink()
    assert text2 == text


def _make_walk_dir(topdir: Path) -> None:
    topdir.mkdir()
    (topdir / 'dir1').mkdir()
    (topdir / 'dir1' / 'dir2').mkdir()
    (topdir / 'dir1' / 'file1').touch()
    (topdir / 'dir3').mkdir()
    (topdir / 'file2').touch()
    (topdir / 'file3').touch()
    (topdir / 'dir1' / 'dir_link').symlink_to(topdir / 'dir3')


def test_walk_top_down(paths: Dict[str, Path]) -> None:
    _make_walk_dir(paths['new_dir'])
    newdir = paths['new_dir']

    dirs = list()  # type: List[str]
    subdirs = list()  # type: List[str]
    files = list()  # type: List[str]
    for dirpath, dirnames, filenames in newdir.walk():
        dirs.append(str(dirpath))
        dirnames.sort()
        for dirname in dirnames:
            subdirs.append(str(dirpath / dirname))
        filenames.sort()
        for filename in filenames:
            files.append(str(dirpath / filename))

    assert dirs == [
            str(newdir),
            str(newdir) + '/dir1',
            str(newdir) + '/dir1/dir2',
            str(newdir) + '/dir3']

    assert subdirs == [
            str(newdir) + '/dir1',
            str(newdir) + '/dir3',
            str(newdir) + '/dir1/dir2',
            str(newdir) + '/dir1/dir_link']

    assert files == [
            str(newdir) + '/file2',
            str(newdir) + '/file3',
            str(newdir) + '/dir1/file1']

    paths['new_dir'].rmdir(recursive=True)


def test_walk_bottom_up(paths: Dict[str, Path]) -> None:
    _make_walk_dir(paths['new_dir'])
    newdir = paths['new_dir']

    dirs = list()  # type: List[str]
    subdirs = list()  # type: List[str]
    files = list()  # type: List[str]
    for dirpath, dirnames, filenames in newdir.walk(topdown=False):
        dirs.append(str(dirpath))
        dirnames.sort()
        for dirname in dirnames:
            subdirs.append(str(dirpath / dirname))
        filenames.sort()
        for filename in filenames:
            files.append(str(dirpath / filename))

    print('dirs: {}'.format(dirs))
    assert (dirs == [
                     str(newdir) + '/dir1/dir2',
                     str(newdir) + '/dir1',
                     str(newdir) + '/dir3',
                     str(newdir)]
            or dirs == [
                        str(newdir) + '/dir3',
                        str(newdir) + '/dir1/dir2',
                        str(newdir) + '/dir1',
                        str(newdir)])

    assert subdirs == [
            str(newdir) + '/dir1/dir2',
            str(newdir) + '/dir1/dir_link',
            str(newdir) + '/dir1',
            str(newdir) + '/dir3']

    assert files == [
            str(newdir) + '/dir1/file1',
            str(newdir) + '/file2',
            str(newdir) + '/file3']

    paths['new_dir'].rmdir(recursive=True)


def test_walk_follow_dir_links(paths: Dict[str, Path]) -> None:
    _make_walk_dir(paths['new_dir'])
    dir1 = paths['new_dir'] / 'dir1'

    dirs = list()  # type: List[str]
    subdirs = list()  # type: List[str]
    files = list()  # type: List[str]
    for dirpath, dirnames, filenames in dir1.walk(followlinks=True):
        dirs.append(str(dirpath))
        dirnames.sort()
        for dirname in dirnames:
            subdirs.append(str(dirpath / dirname))
        filenames.sort()
        for filename in filenames:
            files.append(str(dirpath / filename))

    assert dirs == [
            str(dir1),
            str(dir1) + '/dir2',
            str(dir1) + '/dir_link']    # or will that be dir3?

    assert subdirs == [
            str(dir1) + '/dir2',
            str(dir1) + '/dir_link']

    assert files == [
            str(dir1) + '/file1']

    paths['new_dir'].rmdir(recursive=True)


def test_walk_onerror(paths: Dict[str, Path]) -> None:
    _make_walk_dir(paths['new_dir'])
    newdir = paths['new_dir']

    handler_called = 0

    def handler(error: BaseException) -> None:
        nonlocal handler_called
        assert isinstance(error, OSError)
        assert error.filename == str(newdir / 'dir1')
        handler_called += 1

    (newdir / 'dir1').chmod(0o000)
    for dirpath, dirnames, filenames in newdir.walk(onerror=handler):
        pass

    assert handler_called == 1
