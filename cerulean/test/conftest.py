import pytest
from cerulean.credential import PasswordCredential
from cerulean.direct_gnu_scheduler import DirectGnuScheduler
from cerulean.file_system import FileSystem
from cerulean.local_file_system import LocalFileSystem
from cerulean.local_terminal import LocalTerminal
from cerulean.sftp_file_system import SftpFileSystem
from cerulean.slurm_scheduler import SlurmScheduler
from cerulean.ssh_terminal import SshTerminal
from cerulean.torque_scheduler import TorqueScheduler


@pytest.fixture(scope='module')
def password_credential():
    return PasswordCredential('cerulean', 'kingfisher')


@pytest.fixture(scope='module')
def ssh_terminal(password_credential):
    with SshTerminal('cerulean-test-ssh', 22, password_credential) as term:
        yield term


@pytest.fixture(scope='module')
def local_filesystem():
    yield LocalFileSystem()


@pytest.fixture(scope='module', params=['local', 'sftp'])
def filesystem(request, ssh_terminal):
    if request.param == 'local':
        yield LocalFileSystem()
    elif request.param == 'sftp':
        with SftpFileSystem(ssh_terminal) as fs:
            yield fs


@pytest.fixture(scope='module', params=['local', 'sftp'])
def filesystem2(request, password_credential):
    if request.param == 'local':
        yield LocalFileSystem()
    elif request.param == 'sftp':
        # don't use the ssh_terminal fixture, we want a separate connection
        with SshTerminal('cerulean-test-ssh', 22, password_credential) as term:
            with SftpFileSystem(term) as fs:
                yield fs


@pytest.fixture(scope='module')
def paths(filesystem):
    root = filesystem / 'home' / 'cerulean' / 'test_files'

    return {
            'root': root,
            'dir': root / 'links',
            'new_dir': root / 'testdir',
            'deep_new_dir': root / 'testdir2' / 'testdeepdir',
            'file': root / 'links' / 'file0',
            'other_file': root / 'links' / 'file1',
            'new_file': root / 'test.txt',
            'link': root / 'links' / 'link0',
            'multi_link': root / 'links' / 'link1',
            'broken_link': root / 'links' / 'link2',
            'link_loop': root / 'links' / 'link3',
            'fifo': root / 'fifo',
            'chardev': root / 'chardev',
            'blockdev': root / 'blockdev',
        }


@pytest.fixture(scope='module', params=['local', 'ssh'])
def terminal(request, ssh_terminal):
    if request.param == 'local':
        yield LocalTerminal()
    elif request.param == 'ssh':
        yield ssh_terminal


@pytest.fixture(scope='module', params=[
    'local_direct',
    'ssh_direct',
    'ssh_torque-6',
    'ssh_slurm-14-11',
    'ssh_slurm-15-08',
    'ssh_slurm-16-05',
    'ssh_slurm-17-02',
    'ssh_slurm-17-11'])
def scheduler_and_fs(request, ssh_terminal, password_credential):
    if request.param == 'local_direct':
        yield DirectGnuScheduler(LocalTerminal()), LocalFileSystem()
    elif request.param == 'ssh_direct':
        with SftpFileSystem(ssh_terminal) as fs:
            yield DirectGnuScheduler(ssh_terminal), fs
    elif request.param == 'ssh_torque-6':
        term = SshTerminal('cerulean-test-torque-6', 22, password_credential)
        with SftpFileSystem(term) as fs:
            yield TorqueScheduler(term), fs
    elif request.param == 'ssh_slurm-14-11':
        term = SshTerminal('cerulean-test-slurm-14-11', 22, password_credential)
        with SftpFileSystem(term) as fs:
            yield SlurmScheduler(term), fs
    elif request.param == 'ssh_slurm-15-08':
        term = SshTerminal('cerulean-test-slurm-15-08', 22, password_credential)
        with SftpFileSystem(term) as fs:
            yield SlurmScheduler(term), fs
    elif request.param == 'ssh_slurm-16-05':
        term = SshTerminal('cerulean-test-slurm-16-05', 22, password_credential)
        with SftpFileSystem(term) as fs:
            yield SlurmScheduler(term), fs
    elif request.param == 'ssh_slurm-17-02':
        term = SshTerminal('cerulean-test-slurm-17-02', 22, password_credential)
        with SftpFileSystem(term) as fs:
            yield SlurmScheduler(term), fs
    elif request.param == 'ssh_slurm-17-11':
        term = SshTerminal('cerulean-test-slurm-17-11', 22, password_credential)
        with SftpFileSystem(term) as fs:
            yield SlurmScheduler(term), fs


@pytest.fixture(scope='module', params=[1, 2])
def procs_per_node(request):
    return request.param
