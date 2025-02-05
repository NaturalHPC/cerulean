import logging
import time
from typing import Optional, Union

from cerulean.job_description import JobDescription
from cerulean.job_status import JobStatus
from cerulean.scheduler import Scheduler
from cerulean.terminal import Terminal


logger = logging.getLogger(__name__)


class SlurmScheduler(Scheduler):
    """Represents a Slurm scheduler.

    This class represents a Slurm scheduler, to which it talks through a
    :class:`Terminal`.

    On some machines, an additional command is needed to make Slurm available to the
    user, e.g. 'module load slurm'. If you specify a prefix, it will be prepended to any
    Slurm command run by this class. Note that this is a plain string concatenation, so
    you'll probably need something like 'module load slurm;', with a semicolon to
    separate the commands.
    """
    def __init__(self, terminal: Terminal, prefix: str = '') -> None:
        """Create ea SlurmScheduler.

        Arguments:
            terminal: The terminal to use to talk to the scheduler.
            prefix: A string to prefix the SLURM commands with.
        """
        self.__terminal = terminal
        self.__prefix = prefix

        command = self.__prefix + ' sbatch'
        exit_code, output, error = self.__terminal.run(
                10, command, ['--version'])
        logger.debug('sbatch --version exit code: %s', exit_code)
        logger.debug('sbatch --version output: %s', output)
        logger.debug('sbatch --version error: %s', error)

    def submit(self, job_description: JobDescription) -> str:
        if job_description.command is None:
            raise ValueError('Job description is missing a command')

        job_script = _job_desc_to_job_script(job_description)
        logger.debug('Submitting job script: %s', job_script)

        command = self.__prefix + ' sbatch'
        exit_code, output, error = self.__terminal.run(
                10, command, [], job_script, None)

        logger.debug('sbatch exit code: %s', exit_code)
        logger.debug('sbatch output: %s', output)
        logger.debug('sbatch error: %s', error)
        if exit_code != 0:
            raise RuntimeError('Error running sbatch: {}'.format(error))

        job_id = output.strip().split(' ')[-1]
        return job_id

    def get_status(self, job_id: str) -> JobStatus:
        logger.debug('Calling squeue -j %s -h -o %%T', job_id)
        command = self.__prefix + ' squeue'
        exit_code, output, error = self.__terminal.run(
            10, command, ['-j', job_id, '-h', '-o', '%T'], None, None)
        logger.debug('squeue exit code: %s', exit_code)
        logger.debug('squeue output: %s', output)
        logger.debug('squeue error: %s', error)

        status = output.strip()
        if status == '':
            # Seems like SLURM sometimes does not show the job, possibly
            # because it's transitioning to COMPLETING. So
            # if we don't find it, try again to be a bit more robust.
            time.sleep(2.0)
            logger.debug('No answer from Slurm, trying again...')
            exit_code, output, error = self.__terminal.run(
                10, command, ['-j', job_id, '-h', '-o', '%T'])
            status = output.strip()
            logger.debug('squeue output 2: %s', status)

        status_map = {
            'PENDING': JobStatus.WAITING,
            'CONFIGURING': JobStatus.WAITING,
            'RUNNING': JobStatus.RUNNING,
            'SUSPENDED': JobStatus.RUNNING,
            'COMPLETING': JobStatus.RUNNING,
            'BOOT_FAIL': JobStatus.DONE,
            'CANCELLED': JobStatus.DONE,
            'COMPLETED': JobStatus.DONE,
            'FAILED': JobStatus.DONE,
            'TIMEOUT': JobStatus.DONE,
            'PREEMPTED': JobStatus.DONE,
            'NODE_FAIL': JobStatus.DONE,
            'REVOKED': JobStatus.DONE,
            'SPECIAL_EXIT': JobStatus.DONE
        }
        try:
            job_status = status_map[status]
        except KeyError:
            job_status = JobStatus.DONE

        logger.debug('get_status returning %s', job_status.name)

        return job_status

    def get_exit_code(self, job_id: str) -> Optional[int]:
        if self.get_status(job_id) != JobStatus.DONE:
            return None

        logger.debug(
                'get_exit_code() running sacct -j %s --noheader --format=ExitCode',
                job_id)
        command = self.__prefix + ' sacct'
        err, output, error = self.__terminal.run(
            10, command, ['-j', job_id, '--noheader', '--format=ExitCode'])
        logger.debug('sacct exit code: %s', err)
        logger.debug('sacct output: %s', output)
        logger.debug('sacct error: %s', error)
        if err != 0:
            raise RuntimeError('Error running sacct: {}'.format(error))

        if output.lstrip() == '':
            return None
        exit_code = int(output.lstrip().split(':')[0])
        return exit_code

    def cancel(self, job_id: str) -> None:
        logger.debug('Running scancel %s', job_id)
        command = self.__prefix + ' scancel'
        self.__terminal.run(10, command, [job_id])


def _job_desc_to_job_script(job_description: JobDescription) -> str:
    job_script = '#!/bin/bash\n'
    job_script = _add_option(job_script, 'job-name', job_description.name)

    if job_description.time_reserved is not None:
        job_script += '#SBATCH --time={}\n'.format(
            _seconds_to_time(job_description.time_reserved))

    job_script = _add_option(
            job_script, 'partition', job_description.queue_name)
    job_script = _add_option(job_script, 'nodes', job_description.num_nodes)
    job_script = _add_option(
            job_script, 'ntasks-per-node', job_description.mpi_processes_per_node)
    if job_description.mpi_processes_per_node is not None:
        job_script = _add_option(job_script, 'overcommit', '')

    if job_description.system_out_file is not None:
        job_script += '#SBATCH -o {}\n'.format(job_description.system_out_file)

    if job_description.system_err_file is not None:
        job_script += '#SBATCH -e {}\n'.format(job_description.system_err_file)

    if job_description.extra_scheduler_options is not None:
        job_script += '#SBATCH {}\n'.format(job_description.extra_scheduler_options)

    for name, value in job_description.environment.items():
        job_script += "export {}='{}'\n".format(name, value)

    if job_description.working_directory is not None:
        job_script += 'cd {}\n'.format(job_description.working_directory)

    job_script += '{}'.format(job_description.command)
    job_script += ' {}'.format(' '.join(job_description.arguments))

    if job_description.stdout_file is not None:
        job_script += ' >{}'.format(job_description.stdout_file)

    if job_description.stderr_file is not None:
        job_script += ' 2>{}'.format(job_description.stderr_file)
    return job_script


def _add_option(
        job_script: str, option: str, value: Optional[Union[int, str]]) -> str:
    if value is not None:
        if value != '':
            return job_script + '#SBATCH --{}={}\n'.format(option, value)
        else:
            return job_script + '#SBATCH --{}\n'.format(option)
    else:
        return job_script


def _seconds_to_time(seconds: int) -> str:
    """Converts seconds to a SLURM allocation duration.

    Args:
        seconds: The number of seconds to reserve.

    Returns:
        A string of the form DD:HH:MM:SS.
    """
    seconds_per_day = 60 * 60 * 24
    seconds_per_hour = 60 * 60
    seconds_per_minute = 60

    days = seconds // seconds_per_day
    seconds -= days * seconds_per_day

    hours = seconds // seconds_per_hour
    seconds -= hours * seconds_per_hour

    minutes = seconds // seconds_per_minute
    seconds -= minutes * seconds_per_minute
    return '{:02d}-{:02d}:{:02d}:{:02d}'.format(days, hours, minutes, seconds)
