import pathlib
from typing import Dict

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
