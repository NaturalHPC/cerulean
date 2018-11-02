from typing import Dict

import pytest
from cerulean import EntryType, Permission
from cerulean.file_system_impl import AbstractPath, FileSystemImpl


def test_exists(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    assert filesystem._exists(lpaths['root'])
    assert filesystem._exists(lpaths['dir'])
    assert filesystem._exists(lpaths['file'])
    assert filesystem._exists(lpaths['link'])
    assert not filesystem._exists(lpaths['broken_link'])
    assert not filesystem._exists(lpaths['link_loop'])


def test_touch(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    path = lpaths['new_file']
    filesystem._touch(path)
    assert filesystem._exists(path)
    # clean up, since we're reusing the file system
    filesystem._unlink(path)


def test_mkdir(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    filesystem._mkdir(lpaths['new_dir'])
    assert filesystem._is_dir(lpaths['new_dir'])
    filesystem._rmdir(lpaths['new_dir'])

    filesystem._mkdir(lpaths['deep_new_dir'], parents=True)
    assert filesystem._is_dir(lpaths['deep_new_dir'].parent)
    assert filesystem._is_dir(lpaths['deep_new_dir'])
    filesystem._rmdir(lpaths['deep_new_dir'])
    filesystem._rmdir(lpaths['deep_new_dir'].parent)

    filesystem._mkdir(lpaths['deep_new_dir'], mode=0o660, parents=True)
    assert filesystem._is_dir(lpaths['deep_new_dir'].parent)
    assert filesystem._has_permission(lpaths['deep_new_dir'].parent, Permission.OTHERS_READ)
    assert not filesystem._has_permission(lpaths['deep_new_dir'], Permission.OTHERS_READ)

    with pytest.raises(FileExistsError):
        filesystem._mkdir(lpaths['deep_new_dir'])

    filesystem._mkdir(lpaths['deep_new_dir'], exists_ok=True)
    filesystem._rmdir(lpaths['deep_new_dir'])
    filesystem._rmdir(lpaths['deep_new_dir'].parent)


def test_iterdir(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    for entry in filesystem._iterdir(lpaths['dir']):
        assert entry.name in ['executable', 'file0', 'file1', 'link0', 'link1',
                              'link2', 'link3', 'link4', 'private']


def test_rmdir(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    filesystem._mkdir(lpaths['new_dir'])
    filesystem._rmdir(lpaths['new_dir'])
    assert not filesystem._exists(lpaths['new_dir'])

    with pytest.raises(OSError):
        filesystem._rmdir(lpaths['root'])

    filesystem._mkdir(lpaths['new_dir'])
    filesystem._touch(lpaths['new_dir'] / 'file.txt')
    filesystem._rmdir(lpaths['new_dir'], recursive=True)
    assert not filesystem._exists(lpaths['new_dir'])

    with pytest.raises(RuntimeError):
        filesystem._rmdir(lpaths['file'])


def test_streaming_read(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    content = bytearray()
    for chunk in filesystem._streaming_read(lpaths['file']):
        content += chunk
    assert content == bytes('Hello World\n', 'utf-8')


def test_streaming_write(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    testdata0 = bytes('Helo', 'utf-8')
    testdata1 = bytes(', world!', 'utf-8')
    filesystem._streaming_write(lpaths['new_file'], [testdata0, testdata1])

    content = bytearray()
    for chunk in filesystem._streaming_read(lpaths['new_file']):
        content += chunk
    assert content == bytes('Helo, world!', 'utf-8')

    filesystem._unlink(lpaths['new_file'])


def test_read_bytes(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    content = filesystem._read_bytes(lpaths['file'])
    assert content == bytes('Hello World\n', 'utf-8')


def test_read_text(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    content = filesystem._read_text(lpaths['file'], encoding='utf-8')
    assert content == 'Hello World\n'


def test_write_bytes(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    data = bytes('Hello, world!', 'utf-8')
    filesystem._write_bytes(lpaths['new_file'], data)

    content = filesystem._read_bytes(lpaths['new_file'])
    assert content == data
    filesystem._unlink(lpaths['new_file'])


def test_write_text(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    data = 'Hello, world!'
    filesystem._write_text(lpaths['new_file'], data)

    content = filesystem._read_text(lpaths['new_file'])
    assert content == data
    filesystem._unlink(lpaths['new_file'])


def test_unlink(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    filesystem._touch(lpaths['new_file'])
    assert filesystem._exists(lpaths['new_file'])
    filesystem._unlink(lpaths['new_file'])
    assert not filesystem._exists(lpaths['new_file'])


def test_entry_types(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    assert filesystem._is_dir(lpaths['root'])
    assert not filesystem._is_dir(lpaths['file'])
    assert not filesystem._is_dir(lpaths['new_dir'])

    assert filesystem._is_file(lpaths['file'])
    assert not filesystem._is_file(lpaths['root'])
    assert not filesystem._is_file(lpaths['new_file'])

    assert filesystem._is_symlink(lpaths['link'])
    assert filesystem._is_file(lpaths['link'])
    assert not filesystem._is_dir(lpaths['link'])
    assert not filesystem._is_symlink(lpaths['new_file'])

    assert filesystem._is_symlink(lpaths['broken_link'])
    assert not filesystem._is_file(lpaths['broken_link'])

    assert filesystem._entry_type(lpaths['root']) == EntryType.DIRECTORY
    assert filesystem._entry_type(lpaths['file']) == EntryType.FILE
    assert filesystem._entry_type(lpaths['link']) == EntryType.SYMBOLIC_LINK
    # disable for now, doesn't work in a docker
    #assert filesystem._entry_type(lpaths['chardev']) == EntryType.CHARACTER_DEVICE
    assert filesystem._entry_type(lpaths['blockdev']) == EntryType.BLOCK_DEVICE
    assert filesystem._entry_type(lpaths['fifo']) == EntryType.FIFO
    # TODO: socket?


def test_size(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    assert filesystem._size(lpaths['file']) == 12
    assert filesystem._size(lpaths['root'] / 'links' / 'file1') == 0
    assert filesystem._size(lpaths['link']) == 12


def test_owner(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    assert filesystem._uid(lpaths['root']) == 999
    assert filesystem._gid(lpaths['root']) == 999


def test_has_permission(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    assert filesystem._has_permission(lpaths['root'], Permission.OWNER_READ)
    assert filesystem._has_permission(lpaths['root'], Permission.OWNER_WRITE)
    assert filesystem._has_permission(lpaths['root'], Permission.OWNER_EXECUTE)
    assert filesystem._has_permission(lpaths['root'], Permission.GROUP_READ)
    assert not filesystem._has_permission(lpaths['root'], Permission.GROUP_WRITE)
    assert filesystem._has_permission(lpaths['root'], Permission.GROUP_EXECUTE)
    assert filesystem._has_permission(lpaths['root'], Permission.OTHERS_READ)
    assert not filesystem._has_permission(lpaths['root'], Permission.OTHERS_WRITE)
    assert filesystem._has_permission(lpaths['root'], Permission.OTHERS_EXECUTE)

    assert not filesystem._has_permission(lpaths['file'], Permission.OTHERS_WRITE)


def test_set_permission(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    for permission in Permission:
        filesystem._set_permission(lpaths['root'], permission, False)

    for permission in Permission:
        assert not filesystem._has_permission(lpaths['root'], permission)

    for permission in Permission:
        filesystem._set_permission(lpaths['root'], permission, True)
        for p2 in Permission:
            is_same = (permission == p2)
            assert filesystem._has_permission(lpaths['root'], p2) == is_same
        filesystem._set_permission(lpaths['root'], permission, False)

    filesystem._chmod(lpaths['root'], 0o0755)


def test_chmod(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    filesystem._chmod(lpaths['root'], 0o0000)
    for permission in Permission:
        assert not filesystem._has_permission(lpaths['root'], permission)
    filesystem._chmod(lpaths['root'], 0o0755)
    granted_permissions = [
            Permission.OWNER_READ, Permission.OWNER_WRITE, Permission.OWNER_EXECUTE,
            Permission.GROUP_READ, Permission.GROUP_EXECUTE,
            Permission.OTHERS_READ, Permission.OTHERS_EXECUTE]
    for permission in Permission:
        if permission in granted_permissions:
            assert filesystem._has_permission(lpaths['root'], permission)
        else:
            assert not filesystem._has_permission(lpaths['root'], permission)


def test_symlink_to(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    filesystem._symlink_to(lpaths['new_file'], lpaths['file'])
    assert filesystem._is_symlink(lpaths['new_file'])
    assert filesystem._is_file(lpaths['new_file'])
    filesystem._unlink(lpaths['new_file'])
    assert not filesystem._exists(lpaths['new_file'])
    assert filesystem._exists(lpaths['file'])


def test_readlink(filesystem: FileSystemImpl, lpaths: Dict[str, AbstractPath]) -> None:
    target = filesystem._readlink(lpaths['link'], False)
    assert str(target) == '/home/cerulean/test_files/links/file0'

    target = filesystem._readlink(lpaths['multi_link'], False)
    assert str(target) == '/home/cerulean/test_files/links/link0'

    target = filesystem._readlink(lpaths['multi_link'], True)
    assert str(target) == '/home/cerulean/test_files/links/file0'

    target = filesystem._readlink(lpaths['broken_link'], False)
    assert str(target) == '/doesnotexist'

    target = filesystem._readlink(lpaths['broken_link'], True)
    assert str(target) == '/doesnotexist'

    target = filesystem._readlink(lpaths['broken_link'], True)
    assert str(target) == '/doesnotexist'

    target = filesystem._readlink(lpaths['link_loop'], False)
    assert str(target) == '/home/cerulean/test_files/links/link4'

    with pytest.raises(RuntimeError):
        filesystem._readlink(lpaths['link_loop'], True)
