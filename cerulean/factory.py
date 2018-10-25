from typing import cast, Generator, Optional

from cerulean.credential import Credential
from cerulean.direct_gnu_scheduler import DirectGnuScheduler
from cerulean.file_system import FileSystem
from cerulean.local_file_system import LocalFileSystem
from cerulean.local_terminal import LocalTerminal
from cerulean.scheduler import Scheduler
from cerulean.sftp_file_system import SftpFileSystem
from cerulean.slurm_scheduler import SlurmScheduler
from cerulean.ssh_terminal import SshTerminal
from cerulean.terminal import Terminal
from cerulean.torque_scheduler import TorqueScheduler


def make_file_system(protocol: str, location: Optional[str] = None,
                     credential: Optional[Credential] = None
                     ) -> FileSystem:
    """Make a file system object.

    This is a factory function for FileSystem objects. It will \
    instantiate a FileSystem implementation according to the parameters \
    you give it.

    FileSystems may hold resources, so you should either use this \
    function with a ``with`` statement, or call :meth:`close` on the \
    returned object when you are done with it.

    Args:
        protocol: The protocol to use to connect to the file system. \
                Can be `local` or `sftp`. For `local`, location and \
                credential can be omitted.
        location: The location in the form `hostname` or \
                `hostname:port` to connect to.
        credential: The :class:`Credential` to use to connect with.

    Returns:
        An instance of a FileSystem representing the described file \
                system.
    """
    if protocol == 'local':
        return LocalFileSystem()
    elif protocol == 'sftp':
        term = cast(SshTerminal, make_terminal('ssh', location, credential))
        return SftpFileSystem(term, True)
    else:
        raise ValueError('Unknown protocol, use either local or sftp')


def make_terminal(protocol: str, location: Optional[str] = None,
                  credential: Optional[Credential] = None
                  ) -> Terminal:
    """Make a terminal object.

    This is a factory function for Terminal objects. It will \
    instantiate a Terminal implementation according to the parameters \
    you give it.

    Terminals may hold resources, so you should either use this \
    function with a ``with`` statement, or call :meth:`close` on the \
    returned object when you are done with it.

    Args:
        protocol: The protocol to use to connect to the file system. \
                Can be `local` or `sftp`. For `local`, location and \
                credential can be omitted.
        location: The location in the form `hostname` or \
                `hostname:port` to connect to.
        credential: The :class:`Credential` to use to connect with.

    Returns:
        An instance of a FileSystem representing the described file \
                system.
    """
    if protocol == 'local':
        return LocalTerminal()
    elif protocol == 'ssh':
        if location is None:
            raise ValueError(
                    'The ssh protocol requires a location to connect to')
        if credential is None:
            raise ValueError(
                    'The ssh protocol requires a credential to connect with')

        if ':' in location:
            host = location.split(':')[0]
            port = int(location.split(':')[1])
        else:
            host = location
            port = 22
        return SshTerminal(host, port, credential)
    else:
        raise ValueError('Unknown protocol, use either local or ssh')


def make_scheduler(name: str, terminal: Terminal) -> Scheduler:
    """Make a scheduler object.

    This is a factory function for Scheduler objects. It will \
    instantiate a Scheduler implementation according to the parameters \
    you give it, which talks to the supplied Terminal.

    Args:
        name: The name of the scheduler. One of ``directgnu``,
                ``slurm``, or ``torque``.
        terminal: The terminal this Scheduler will communicate on.

    Returns:
        The Scheduler.
    """
    if name == 'directgnu':
        return DirectGnuScheduler(terminal)
    elif name == 'slurm':
        return SlurmScheduler(terminal)
    elif name == 'torque':
        return TorqueScheduler(terminal)
    else:
        raise ValueError('Unknown scheduler type {} specified, expected one of'
                         ' directgnu, slurm, or torque.'.format(name))
