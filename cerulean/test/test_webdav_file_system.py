from typing import Dict

import pytest

from cerulean import (
        EntryType, PasswordCredential, Permission, UnsupportedOperationError,
        WebdavFileSystem)
from cerulean.path import AbstractPath


def test_creating_http() -> None:
    with WebdavFileSystem('http://cerulean-test-webdav/files') as f:
        assert (f / '').is_dir()


def test_creating_http_password() -> None:
    credential = PasswordCredential('cerulean', 'kingfisher')
    with WebdavFileSystem('http://cerulean-test-webdav/protected_files',
                          credential) as f:
        assert (f / '').is_dir()


def test_creating_https() -> None:
    with WebdavFileSystem('https://cerulean-test-webdav/files',
                          host_ca_cert_file='/home/cerulean/cerulean_webdav.crt'
                          ) as f:
        assert (f / '').is_dir()


def test_creating_https_password() -> None:
    credential = PasswordCredential('cerulean', 'kingfisher')
    with WebdavFileSystem('https://cerulean-test-webdav/protected_files',
                          credential,
                          host_ca_cert_file='/home/cerulean/cerulean_webdav.crt'
                          ) as f:
        assert (f / '').is_dir()


# Test handling of unsupported features


def test_entry_types(webdav_filesystem_raises: WebdavFileSystem,
                     lpaths_webdav_raises: Dict[str, AbstractPath]) -> None:
    filesystem = webdav_filesystem_raises
    lpaths = lpaths_webdav_raises
    assert filesystem._entry_type(lpaths['link']) == EntryType.FILE
    with pytest.raises(FileNotFoundError):
        filesystem._entry_type(lpaths['blockdev'])
    with pytest.raises(FileNotFoundError):
        filesystem._entry_type(lpaths['fifo'])

    assert filesystem._is_file(lpaths['link'])
    assert not filesystem._is_file(lpaths['blockdev'])
    assert not filesystem._is_file(lpaths['fifo'])

    assert not filesystem._is_dir(lpaths['link'])
    assert not filesystem._is_dir(lpaths['blockdev'])
    assert not filesystem._is_dir(lpaths['fifo'])


def test_owner(webdav_filesystem_raises: WebdavFileSystem,
               lpaths_webdav_raises: Dict[str, AbstractPath]) -> None:
    filesystem = webdav_filesystem_raises
    lpaths = lpaths_webdav_raises
    assert filesystem._uid(lpaths['root']) == 0
    assert filesystem._gid(lpaths['root']) == 0


def test_has_permission(webdav_filesystem_raises: WebdavFileSystem,
                        lpaths_webdav_raises: Dict[str, AbstractPath]) -> None:
    filesystem = webdav_filesystem_raises
    lpaths = lpaths_webdav_raises
    file_permissions = [Permission.OWNER_READ, Permission.OWNER_WRITE]
    dir_permissions = file_permissions + [Permission.OWNER_EXECUTE]
    for permission in dir_permissions:
        assert filesystem._has_permission(lpaths['root'], permission)
    for permission in file_permissions:
        assert filesystem._has_permission(lpaths['file'], permission)


def test_set_permission(webdav_filesystem_raises: WebdavFileSystem,
                        lpaths_webdav_raises: Dict[str, AbstractPath]) -> None:
    filesystem = webdav_filesystem_raises
    lpaths = lpaths_webdav_raises

    with pytest.raises(UnsupportedOperationError):
        filesystem._set_permission(lpaths['root'], Permission.OTHERS_READ,
                                   False)


def test_chmod(webdav_filesystem_raises: WebdavFileSystem,
               lpaths_webdav_raises: Dict[str, AbstractPath]) -> None:
    filesystem = webdav_filesystem_raises
    lpaths = lpaths_webdav_raises

    with pytest.raises(UnsupportedOperationError):
        filesystem._chmod(lpaths['root'], 0o0755)


def test_symlink_to(webdav_filesystem_raises: WebdavFileSystem,
                    lpaths_webdav_raises: Dict[str, AbstractPath]) -> None:
    filesystem = webdav_filesystem_raises
    lpaths = lpaths_webdav_raises

    with pytest.raises(UnsupportedOperationError):
        filesystem._symlink_to(lpaths['new_file'], lpaths['file'])


def test_readlink(webdav_filesystem_raises: WebdavFileSystem,
                  lpaths_webdav_raises: Dict[str, AbstractPath]) -> None:
    filesystem = webdav_filesystem_raises
    lpaths = lpaths_webdav_raises

    with pytest.raises(IOError):
        filesystem._readlink(lpaths['link'], False)

    with pytest.raises(IOError):
        filesystem._readlink(lpaths['link'], True)


def test_entry_types2(webdav_filesystem_quiet: WebdavFileSystem,
                      lpaths_webdav_raises: Dict[str, AbstractPath]) -> None:
    filesystem = webdav_filesystem_quiet
    lpaths = lpaths_webdav_raises
    assert filesystem._entry_type(lpaths['link']) == EntryType.FILE
    with pytest.raises(FileNotFoundError):
        filesystem._entry_type(lpaths['blockdev'])
    with pytest.raises(FileNotFoundError):
        filesystem._entry_type(lpaths['fifo'])

    assert not filesystem._exists(lpaths['blockdev'])

    assert filesystem._is_file(lpaths['link'])
    assert not filesystem._is_file(lpaths['blockdev'])
    assert not filesystem._is_file(lpaths['fifo'])

    assert not filesystem._is_dir(lpaths['link'])
    assert not filesystem._is_dir(lpaths['blockdev'])
    assert not filesystem._is_dir(lpaths['fifo'])


def test_owner2(webdav_filesystem_quiet: WebdavFileSystem,
                lpaths_webdav_raises: Dict[str, AbstractPath]) -> None:
    filesystem = webdav_filesystem_quiet
    lpaths = lpaths_webdav_raises
    assert filesystem._uid(lpaths['root']) == 0
    assert filesystem._gid(lpaths['root']) == 0


def test_has_permission2(webdav_filesystem_quiet: WebdavFileSystem,
                         lpaths_webdav_raises: Dict[str, AbstractPath]
                         ) -> None:
    filesystem = webdav_filesystem_quiet
    lpaths = lpaths_webdav_raises
    file_permissions = [Permission.OWNER_READ, Permission.OWNER_WRITE]
    dir_permissions = file_permissions + [Permission.OWNER_EXECUTE]
    for permission in dir_permissions:
        assert filesystem._has_permission(lpaths['root'], permission)
    for permission in file_permissions:
        assert filesystem._has_permission(lpaths['file'], permission)


def test_set_permission2(
        webdav_filesystem_quiet: WebdavFileSystem,
        lpaths_webdav_raises: Dict[str, AbstractPath]) -> None:
    filesystem = webdav_filesystem_quiet
    lpaths = lpaths_webdav_raises

    filesystem._set_permission(lpaths['root'], Permission.OTHERS_READ, True)
    file_permissions = [Permission.OWNER_READ, Permission.OWNER_WRITE]
    dir_permissions = file_permissions + [Permission.OWNER_EXECUTE]
    for permission in dir_permissions:
        assert filesystem._has_permission(lpaths['root'], permission)


def test_chmod2(webdav_filesystem_quiet: WebdavFileSystem,
                lpaths_webdav_raises: Dict[str, AbstractPath]) -> None:
    filesystem = webdav_filesystem_quiet
    lpaths = lpaths_webdav_raises

    filesystem._chmod(lpaths['root'], 0o0755)
    file_permissions = [Permission.OWNER_READ, Permission.OWNER_WRITE]
    dir_permissions = file_permissions + [Permission.OWNER_EXECUTE]
    for permission in dir_permissions:
        assert filesystem._has_permission(lpaths['root'], permission)


def test_symlink_to2(webdav_filesystem_quiet: WebdavFileSystem,
                     lpaths_webdav_raises: Dict[str, AbstractPath]) -> None:
    filesystem = webdav_filesystem_quiet
    lpaths = lpaths_webdav_raises

    filesystem._symlink_to(lpaths['new_file'], lpaths['file'])
    assert not filesystem._exists(lpaths['new_file'])


def test_readlink2(webdav_filesystem_quiet: WebdavFileSystem,
                   lpaths_webdav_raises: Dict[str, AbstractPath]) -> None:
    filesystem = webdav_filesystem_quiet
    lpaths = lpaths_webdav_raises

    # raises anyway, since the resource is not a symlink, those don't exist
    with pytest.raises(IOError):
        filesystem._readlink(lpaths['link'], False)

    with pytest.raises(IOError):
        filesystem._readlink(lpaths['link'], True)
