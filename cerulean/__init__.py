"""The :mod:`cerulean` module is the main API for Cerulean.

This module contains all the functions you need to use Cerulean.

Below, you will also find documentation for submodules. That is \
developer documentation, you do not need it to use Cerulean.
"""

__version__ = '0.1.0'

__author__ = 'Lourens Veen'
__email__ = 'l.veen@esciencecenter.nl'


from cerulean.copy_files import copy
from cerulean.credential import Credential, PasswordCredential, PubKeyCredential
from cerulean.direct_gnu_scheduler import DirectGnuScheduler
from cerulean.factory import make_file_system, make_terminal, make_scheduler
from cerulean.file_system import FileSystem
from cerulean.job_description import JobDescription
from cerulean.job_status import JobStatus
from cerulean.local_file_system import LocalFileSystem
from cerulean.local_terminal import LocalTerminal
from cerulean.path import Path
from cerulean.scheduler import Scheduler
from cerulean.sftp_file_system import SftpFileSystem
from cerulean.slurm_scheduler import SlurmScheduler
from cerulean.ssh_terminal import SshTerminal
from cerulean.terminal import Terminal
from cerulean.torque_scheduler import TorqueScheduler

import logging


logger = logging.getLogger('cerulean')
"""The Cerulean root logger. Use this to set Cerulean's log level.

In particular, if something goes wrong and you want more debug output, you \
can do::

    import logging

    cerulean.logger.setLevel(logging.INFO)

or for even more::

    cerulean.logger.setLevel(logging.DEBUG)
"""

__all__ = ['copy', 'logger', 'make_file_system', 'make_terminal',
           'make_scheduler', 'Credential', 'PasswordCredential',
           'PubKeyCredential', 'DirectGnuScheduler', 'FileSystem',
           'JobDescription', 'JobStatus', 'LocalFileSystem', 'LocalTerminal',
           'Path', 'Scheduler', 'SftpFileSystem', 'SlurmScheduler',
           'SshTerminal', 'Terminal', 'TorqueScheduler']
