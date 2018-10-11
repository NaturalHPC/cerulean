import os
import pathlib
import stat
import time

import pytest
from cerulean.file_system import FileSystem
from cerulean.local_file_system import LocalFileSystem
from cerulean.path import EntryType, Path, Permission
from cerulean.sftp_file_system import SftpFileSystem


def test_exists(filesystem, paths):
    assert filesystem.exists(paths['root'])
    assert filesystem.exists(paths['dir'])
    assert filesystem.exists(paths['file'])
    assert filesystem.exists(paths['link'])
    assert not filesystem.exists(paths['broken_link'])
    assert not filesystem.exists(paths['link_loop'])


def test_touch(filesystem, paths):
    path = paths['new_file']
    filesystem.touch(path)
    assert filesystem.exists(path)
    # clean up, since we're reusing the file system
    filesystem.unlink(path)


def test_mkdir(filesystem, paths):
    filesystem.mkdir(paths['new_dir'])
    assert filesystem.is_dir(paths['new_dir'])
    filesystem.rmdir(paths['new_dir'])

    filesystem.mkdir(paths['deep_new_dir'], parents=True)
    assert filesystem.is_dir(paths['deep_new_dir'].parent)
    assert filesystem.is_dir(paths['deep_new_dir'])
    filesystem.rmdir(paths['deep_new_dir'])
    filesystem.rmdir(paths['deep_new_dir'].parent)

    filesystem.mkdir(paths['deep_new_dir'], mode=0o660, parents=True)
    assert filesystem.is_dir(paths['deep_new_dir'].parent)
    assert filesystem.has_permission(paths['deep_new_dir'].parent, Permission.OTHERS_READ)
    assert not filesystem.has_permission(paths['deep_new_dir'], Permission.OTHERS_READ)

    with pytest.raises(FileExistsError):
        filesystem.mkdir(paths['deep_new_dir'])

    filesystem.mkdir(paths['deep_new_dir'], exists_ok=True)
    filesystem.rmdir(paths['deep_new_dir'])
    filesystem.rmdir(paths['deep_new_dir'].parent)


def test_iterdir(filesystem, paths):
    for entry in filesystem.iterdir(paths['dir']):
        assert entry.name in [
                'file0', 'file1', 'link0', 'link1', 'link2', 'link3', 'link4']


def test_rmdir(filesystem, paths):
    filesystem.mkdir(paths['new_dir'])
    filesystem.rmdir(paths['new_dir'])
    assert not filesystem.exists(paths['new_dir'])

    with pytest.raises(OSError):
        filesystem.rmdir(paths['root'])

    filesystem.mkdir(paths['new_dir'])
    filesystem.touch(paths['new_dir'] / 'file.txt')
    filesystem.rmdir(paths['new_dir'], recursive=True)
    assert not filesystem.exists(paths['new_dir'])

    with pytest.raises(RuntimeError):
        filesystem.rmdir(paths['file'])


def test_streaming_read(filesystem, paths):
    content = bytearray()
    for chunk in filesystem.streaming_read(paths['file']):
        content += chunk
    assert content == bytes('Hello World\n', 'utf-8')


def test_streaming_write(filesystem, paths):
    testdata0 = bytes('Helo', 'utf-8')
    testdata1 = bytes(', world!', 'utf-8')
    filesystem.streaming_write(paths['new_file'], [testdata0, testdata1])

    content = bytearray()
    for chunk in filesystem.streaming_read(paths['new_file']):
        content += chunk
    assert content == bytes('Helo, world!', 'utf-8')

    filesystem.unlink(paths['new_file'])


def test_read_bytes(filesystem, paths):
    content = filesystem.read_bytes(paths['file'])
    assert content == bytes('Hello World\n', 'utf-8')


def test_read_text(filesystem, paths):
    content = filesystem.read_text(paths['file'], encoding='utf-8')
    assert content == 'Hello World\n'


def test_write_bytes(filesystem, paths):
    data = bytes('Hello, world!', 'utf-8')
    filesystem.write_bytes(paths['new_file'], data)

    content = filesystem.read_bytes(paths['new_file'])
    assert content == data
    filesystem.unlink(paths['new_file'])


def test_write_text(filesystem, paths):
    data = 'Hello, world!'
    filesystem.write_text(paths['new_file'], data)

    content = filesystem.read_text(paths['new_file'])
    assert content == data
    filesystem.unlink(paths['new_file'])


def test_unlink(filesystem, paths):
    filesystem.touch(paths['new_file'])
    assert filesystem.exists(paths['new_file'])
    filesystem.unlink(paths['new_file'])
    assert not filesystem.exists(paths['new_file'])


def test_entry_types(filesystem, paths):
    assert filesystem.is_dir(paths['root'])
    assert not filesystem.is_dir(paths['file'])
    assert not filesystem.is_dir(paths['new_dir'])

    assert filesystem.is_file(paths['file'])
    assert not filesystem.is_file(paths['root'])
    assert not filesystem.is_file(paths['new_file'])

    assert filesystem.is_symlink(paths['link'])
    assert filesystem.is_file(paths['link'])
    assert not filesystem.is_dir(paths['link'])
    assert not filesystem.is_symlink(paths['new_file'])

    assert filesystem.is_symlink(paths['broken_link'])
    assert not filesystem.is_file(paths['broken_link'])

    assert filesystem.entry_type(paths['root']) == EntryType.DIRECTORY
    assert filesystem.entry_type(paths['file']) == EntryType.FILE
    assert filesystem.entry_type(paths['link']) == EntryType.SYMBOLIC_LINK
    assert filesystem.entry_type(paths['chardev']) == EntryType.CHARACTER_DEVICE
    assert filesystem.entry_type(paths['blockdev']) == EntryType.BLOCK_DEVICE
    assert filesystem.entry_type(paths['fifo']) == EntryType.FIFO
    # TODO: socket?


def test_size(filesystem, paths):
    assert filesystem.size(paths['file']) == 12
    assert filesystem.size(paths['root'] / 'links' / 'file1') == 0
    assert filesystem.size(paths['link']) == 12


def test_owner(filesystem, paths):
    assert filesystem.uid(paths['root']) == 999
    assert filesystem.gid(paths['root']) == 999


def test_has_permission(filesystem, paths):
    assert filesystem.has_permission(paths['root'], Permission.OWNER_READ)
    assert filesystem.has_permission(paths['root'], Permission.OWNER_WRITE)
    assert filesystem.has_permission(paths['root'], Permission.OWNER_EXECUTE)
    assert filesystem.has_permission(paths['root'], Permission.GROUP_READ)
    assert not filesystem.has_permission(paths['root'], Permission.GROUP_WRITE)
    assert filesystem.has_permission(paths['root'], Permission.GROUP_EXECUTE)
    assert filesystem.has_permission(paths['root'], Permission.OTHERS_READ)
    assert not filesystem.has_permission(paths['root'], Permission.OTHERS_WRITE)
    assert filesystem.has_permission(paths['root'], Permission.OTHERS_EXECUTE)

    assert not filesystem.has_permission(paths['file'], Permission.OTHERS_WRITE)


def test_set_permission(filesystem, paths):
    for permission in Permission:
        filesystem.set_permission(paths['root'], permission, False)

    for permission in Permission:
        assert not filesystem.has_permission(paths['root'], permission)

    for permission in Permission:
        filesystem.set_permission(paths['root'], permission, True)
        for p2 in Permission:
            is_same = (permission == p2)
            assert filesystem.has_permission(paths['root'], p2) == is_same
        filesystem.set_permission(paths['root'], permission, False)

    filesystem.chmod(paths['root'], 0o0755)


def test_chmod(filesystem, paths):
    filesystem.chmod(paths['root'], 0o0000)
    for permission in Permission:
        assert not filesystem.has_permission(paths['root'], permission)
    filesystem.chmod(paths['root'], 0o0755)
    granted_permissions = [
            Permission.OWNER_READ, Permission.OWNER_WRITE, Permission.OWNER_EXECUTE,
            Permission.GROUP_READ, Permission.GROUP_EXECUTE,
            Permission.OTHERS_READ, Permission.OTHERS_EXECUTE]
    for permission in Permission:
        if permission in granted_permissions:
            assert filesystem.has_permission(paths['root'], permission)
        else:
            assert not filesystem.has_permission(paths['root'], permission)


def test_symlink_to(filesystem, paths):
    filesystem.symlink_to(paths['new_file'], paths['file'])
    assert filesystem.is_symlink(paths['new_file'])
    assert filesystem.is_file(paths['new_file'])
    filesystem.unlink(paths['new_file'])
    assert not filesystem.exists(paths['new_file'])
    assert filesystem.exists(paths['file'])


def test_readlink(filesystem, paths):
    target = filesystem.readlink(paths['link'], False)
    assert str(target) == '/home/cerulean/test_files/links/file0'

    target = filesystem.readlink(paths['multi_link'], False)
    assert str(target) == '/home/cerulean/test_files/links/link0'

    target = filesystem.readlink(paths['multi_link'], True)
    assert str(target) == '/home/cerulean/test_files/links/file0'

    target = filesystem.readlink(paths['broken_link'], False)
    assert str(target) == '/doesnotexist'

    target = filesystem.readlink(paths['broken_link'], True)
    assert str(target) == '/doesnotexist'

    target = filesystem.readlink(paths['broken_link'], True)
    assert str(target) == '/doesnotexist'

    target = filesystem.readlink(paths['link_loop'], False)
    assert str(target) == '/home/cerulean/test_files/links/link4'

    with pytest.raises(RuntimeError):
        filesystem.readlink(paths['link_loop'], True)
