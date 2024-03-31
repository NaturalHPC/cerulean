import pytest
from typing import Any, Dict, Generator, Tuple

from cerulean.credential import PasswordCredential
from cerulean.direct_gnu_scheduler import DirectGnuScheduler
from cerulean.file_system import FileSystem
from cerulean.file_system_impl import FileSystemImpl
from cerulean.local_file_system import LocalFileSystem
from cerulean.local_terminal import LocalTerminal
from cerulean.path import AbstractPath, Path
from cerulean.scheduler import Scheduler
from cerulean.sftp_file_system import SftpFileSystem
from cerulean.slurm_scheduler import SlurmScheduler
from cerulean.ssh_terminal import SshTerminal
from cerulean.terminal import Terminal
from cerulean.torque_scheduler import TorqueScheduler
from cerulean.webdav_file_system import WebdavFileSystem


# PyTest does not export FixtureRequest, the type of the request attribute.
# So they're annotated as Any.

@pytest.fixture(scope='module')
def password_credential() -> PasswordCredential:
    return PasswordCredential('cerulean', 'kingfisher')


@pytest.fixture(scope='module')
def ssh_terminal(
        password_credential: PasswordCredential
        ) -> Generator[SshTerminal, None, None]:
    with SshTerminal('cerulean-test-ssh', 22, password_credential) as term:
        yield term


@pytest.fixture(scope='module')
def flaky_ssh_terminal(
        password_credential: PasswordCredential
        ) -> Generator[SshTerminal, None, None]:
    with SshTerminal('cerulean-test-flaky', 22, password_credential) as term:
        yield term


@pytest.fixture(scope='module')
def local_filesystem() -> Generator[LocalFileSystem, None, None]:
    yield LocalFileSystem()


@pytest.fixture(scope='module')
def webdav_filesystem_raises() -> Generator[WebdavFileSystem, None, None]:
    yield WebdavFileSystem('http://cerulean-test-webdav/files')


@pytest.fixture(scope='module')
def webdav_filesystem_quiet() -> Generator[WebdavFileSystem, None, None]:
    yield WebdavFileSystem(
            'http://cerulean-test-webdav/files', unsupported_methods_raise=False)


@pytest.fixture(scope='module', params=['local', 'sftp', 'webdav'])
def filesystem(
        request: Any, ssh_terminal: SshTerminal
        ) -> Generator[FileSystemImpl, None, None]:
    if request.param == 'local':
        yield LocalFileSystem()
    elif request.param == 'sftp':
        with SftpFileSystem(ssh_terminal) as fs:
            yield fs
    elif request.param == 'webdav':
        with WebdavFileSystem('http://cerulean-test-webdav/files') as wfs:
            yield wfs


@pytest.fixture(scope='module', params=['local', 'sftp'])
def filesystem2(
        request: Any, password_credential: PasswordCredential
        ) -> Generator[FileSystemImpl, None, None]:
    if request.param == 'local':
        yield LocalFileSystem()
    elif request.param == 'sftp':
        # don't use the ssh_terminal fixture, we want a separate connection
        with SshTerminal('cerulean-test-ssh', 22, password_credential) as term:
            with SftpFileSystem(term) as fs:
                yield fs
    elif request.param == 'webdav':
        with WebdavFileSystem('http://cerulean-test-webdav/files') as wfs:
            yield wfs


def make_paths(filesystem: FileSystem) -> Dict[str, Path]:
    root = filesystem / 'home' / 'cerulean' / 'test_files'

    return {
            'root': root,
            'dir': root / 'links',
            'new_dir': root / 'testdir',
            'deep_new_dir': root / 'testdir2' / 'testdeepdir',
            'file': root / 'links' / 'file0',
            'other_file': root / 'links' / 'file1',
            'new_file': root / 'test.txt',
            'executable': root / 'links' / 'executable',
            'private': root / 'links' / 'private',
            'link': root / 'links' / 'link0',
            'multi_link': root / 'links' / 'link1',
            'broken_link': root / 'links' / 'link2',
            'link_loop': root / 'links' / 'link3',
            'fifo': root / 'fifo',
            'blockdev': root / 'blockdev',
        }


def paths_to_lpaths(paths: Dict[str, Path]) -> Dict[str, AbstractPath]:
    lpaths = dict()
    for name, path in paths.items():
        lpaths[name] = getattr(path, '_Path__path')
    return lpaths


@pytest.fixture(scope='module')
def paths(filesystem: FileSystem) -> Dict[str, Path]:
    return make_paths(filesystem)


@pytest.fixture(scope='module')
def paths_local(local_filesystem: FileSystem) -> Dict[str, Path]:
    # We test some of the Path methods only on the local fs, to avoid issues
    # with WebDAV not supporting everything.
    return make_paths(local_filesystem)


@pytest.fixture(scope='module')
def lpaths_webdav_raises(
        webdav_filesystem_raises: FileSystem) -> Dict[str, AbstractPath]:
    # And then we need some WebDAV paths to specifically test that.
    paths = make_paths(webdav_filesystem_raises)
    return paths_to_lpaths(paths)


@pytest.fixture(scope='module')
def lpaths_webdav_quiet(
        webdav_filesystem_quiet: FileSystem) -> Dict[str, AbstractPath]:
    # And then we need some WebDAV paths to specifically test that.
    paths = make_paths(webdav_filesystem_quiet)
    return paths_to_lpaths(paths)


@pytest.fixture(scope='module')
def lpaths(paths: Dict[str, Path]) -> Dict[str, AbstractPath]:
    return paths_to_lpaths(paths)


@pytest.fixture(scope='module', params=['local', 'ssh', 'flakyssh'])
def terminal(
        request: Any, ssh_terminal: SshTerminal,
        flaky_ssh_terminal: SshTerminal
        ) -> Generator[Terminal, None, None]:
    if request.param == 'local':
        yield LocalTerminal()
    elif request.param == 'ssh':
        yield ssh_terminal
    elif request.param == 'flakyssh':
        yield flaky_ssh_terminal


@pytest.fixture(scope='module', params=[
    'local_direct',
    'ssh_direct',
    'ssh_torque-6',
    'ssh_slurm-16-05',
    'ssh_slurm-17-02',
    'ssh_slurm-17-11',
    'ssh_slurm-18-08',
    'ssh_slurm-19-05',
    'ssh_slurm-20-02',
    'flakyssh_direct',
    'flakyssh_slurm-17-11'])
def scheduler_and_fs(
        request: Any, ssh_terminal: SshTerminal,
        password_credential: PasswordCredential
        ) -> Generator[Tuple[Scheduler, FileSystem, str], None, None]:
    term = None
    if request.param == 'local_direct':
        yield DirectGnuScheduler(LocalTerminal()), LocalFileSystem(), request.param
    elif request.param == 'ssh_direct':
        with SftpFileSystem(ssh_terminal) as fs:
            yield DirectGnuScheduler(ssh_terminal), fs, request.param
    elif request.param == 'ssh_torque-6':
        term = SshTerminal('cerulean-test-torque-6', 22, password_credential)
        with SftpFileSystem(term) as fs:
            yield TorqueScheduler(term), fs, request.param
    elif request.param == 'flakyssh_direct':
        term = SshTerminal('cerulean-test-flaky', 22, password_credential)
        with SftpFileSystem(term) as fs:
            yield DirectGnuScheduler(term), fs, request.param
    elif request.param == 'flakyssh_slurm-17-11':
        term = SshTerminal('cerulean-test-flaky', 22, password_credential)
        with SftpFileSystem(term) as fs:
            yield SlurmScheduler(term), fs, request.param
    else:
        host = 'cerulean-test-slurm-{}'.format(request.param[-5:])
        term = SshTerminal(host, 22, password_credential)
        with SftpFileSystem(term) as fs:
            yield SlurmScheduler(term), fs, request.param

    if term:
        term.close()


@pytest.fixture(scope='module', params=[1, 2])
def procs_per_node(request: Any) -> int:
    return request.param
