import cerulean
import pytest

from cerulean import make_file_system, make_terminal, make_scheduler


@pytest.mark.skip('not yet done')
def test_make_file_system() -> None:
    with make_file_system('local') as fs1:
        assert isinstance(fs1, cerulean.LocalFileSystem)

    cred = cerulean.PasswordCredential('cerulean', 'kingfisher')
    with make_file_system('sftp', 'cerulean-test-ssh', cred) as fs2:
        assert isinstance(fs2, cerulean.SftpFileSystem)

    with make_file_system('sftp', 'cerulean-test-ssh:22', cred) as fs3:
        assert isinstance(fs3, cerulean.SftpFileSystem)

    with pytest.raises(ValueError):
        fs4 = make_file_system('sftp')

    with pytest.raises(ValueError):
        fs5 = make_file_system('non-existent-protocol')


def test_make_terminal() -> None:
    with make_terminal('local') as t1:
        assert isinstance(t1, cerulean.LocalTerminal)

    cred = cerulean.PasswordCredential('cerulean', 'kingfisher')
    with make_terminal('ssh', 'cerulean-test-ssh', cred) as t2:
        assert isinstance(t2, cerulean.SshTerminal)

    with make_terminal('ssh', 'cerulean-test-ssh:22', cred) as t3:
        assert isinstance(t3, cerulean.SshTerminal)

    with pytest.raises(ValueError):
        t4 = make_terminal('ssh')

    with pytest.raises(ValueError):
        t5 = make_terminal('non-existent-protocol')


def test_make_scheduler() -> None:
    with make_terminal('local') as term:
        s1 = make_scheduler('directgnu', term)
        assert isinstance(s1, cerulean.DirectGnuScheduler)

    cred = cerulean.PasswordCredential('cerulean', 'kingfisher')
    with make_terminal('ssh', 'cerulean-test-slurm-17-11', cred) as term2:
        s2 = make_scheduler('directgnu', term2)
        assert isinstance(s2, cerulean.DirectGnuScheduler)

        s3 = make_scheduler('slurm', term2)
        assert isinstance(s3, cerulean.SlurmScheduler)

        with pytest.raises(ValueError):
            make_scheduler('non-existent-scheduler', term2)

    with make_terminal('ssh', 'cerulean-test-torque-6', cred) as term3:
        s4 = make_scheduler('torque', term3)
        assert isinstance(s4, cerulean.TorqueScheduler)
