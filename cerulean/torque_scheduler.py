import logging
from typing import Optional

from cerulean.job_description import JobDescription
from cerulean.job_status import JobStatus
from cerulean.scheduler import Scheduler
from cerulean.terminal import Terminal
from defusedxml import ElementTree


logger = logging.getLogger(__name__)


class TorqueScheduler(Scheduler):
    """Represents a Torque scheduler.

    This class represents a Torque scheduler, to which it talks through a
    :class:`Terminal`.
    """
    def __init__(self, terminal: Terminal, prefix: str = '') -> None:
        """Create a TorqueScheduler.

        On some machines, an additional command is needed to make Torque available to
        the user, e.g. 'module load torque'. If you specify a prefix, it will be
        prepended to any Torque command run by this class. Note that this is a plain
        string concatenation, so you'll probably need something like 'module load
        torque;', with a semicolon to separate the commands.

        Arguments:
            terminal: The terminal to use to talk to the scheduler.
            prefix: A string to prefix the Torque commands with.
        """
        self.__terminal = terminal
        self.__prefix = prefix
        logger.debug('Running qsub --version')

        command = self.__prefix + ' qsub'
        exit_code, output, error = self.__terminal.run(
                10, 'qsub', ['--version'])
        logger.debug('qsub --version exit_code: %s', exit_code)
        logger.debug('qsub --version std output: %s', output)
        logger.debug('qsub --version std error: %s', error)

    def submit(self, job_description: JobDescription) -> str:
        if job_description.command is None:
            raise ValueError('Job description is missing a command')

        job_script = _job_desc_to_job_script(job_description)
        logger.debug('Running qsub with job script:\n%s', job_script)
        command = self.__prefix + ' qsub'
        exit_code, output, error = self.__terminal.run(
                10, command, ['-'], job_script)

        logger.debug('qsub exit code: %s', exit_code)
        logger.debug('qsub std output: %s', output)
        logger.debug('qsub std error: %s', error)

        if exit_code != 0:
            raise RuntimeError('Torque qsub error: {}'.format(error))

        job_id = output.strip().split(' ')[-1]
        return job_id

    def get_status(self, job_id: str) -> JobStatus:
        logger.debug('Running qstat with job id %s', job_id)
        command = self.__prefix + ' qstat'
        exit_code, output, error = self.__terminal.run(10, command,
                                                       ['-x', job_id])
        logger.debug('qstat exit code: %s', exit_code)
        logger.debug('qstat output: %s', output)
        logger.debug('qstat error: %s', error)

        if output == '':
            raise RuntimeError(
                    'No output from qstat, could not determine job status.')
        xml_data = ElementTree.fromstring(output)
        if len(xml_data) == 0:
            return JobStatus.DONE

        status = _get_field_from_qstat_xml(xml_data, 'job_state')
        logger.debug('qstat status: %s', status)

        status_map = {
            'W': JobStatus.WAITING,  # waiting for start time
            'Q': JobStatus.WAITING,  # queued
            'H': JobStatus.RUNNING,  # held
            'S': JobStatus.RUNNING,  # suspended
            'R': JobStatus.RUNNING,  # running
            'T': JobStatus.RUNNING,  # being moved
            'E': JobStatus.RUNNING,  # exiting
            'C': JobStatus.DONE  # completed
        }
        try:
            job_status = status_map[status]
        except KeyError:
            raise RuntimeError(
                'Received an unexpected job status {} from qstat'.format(
                    status))

        logger.debug('get_status returning %s', job_status.name)
        return job_status

    def get_exit_code(self, job_id: str) -> Optional[int]:
        if self.get_status(job_id) != JobStatus.DONE:
            return None

        logger.debug('get_exit_code() running qstat -x %s', job_id)
        command = self.__prefix + ' qstat'
        exit_code, output, error = self.__terminal.run(10, command,
                                                       ['-x', job_id])
        logger.debug('qstat exit code: %s', exit_code)
        logger.debug('qstat output: %s', output)
        logger.debug('qstat error: %s', error)

        xml_data = ElementTree.fromstring(output)
        job_exit_code = int(_get_field_from_qstat_xml(xml_data, 'exit_status'))
        return job_exit_code

    def cancel(self, job_id: str) -> None:
        logger.debug('cancel() running qdel %s', job_id)
        command = self.__prefix + ' qdel'
        exit_code, output, error = self.__terminal.run(10, command, [job_id])
        logger.debug('qdel exit code: %s', exit_code)
        logger.debug('qdel output: %s', output)
        logger.debug('qdel error: %s', error)


def _job_desc_to_job_script(job_description: JobDescription) -> str:
    job_script = '#!/bin/bash\n'
    job_script += '#PBS -N {}\n'.format(job_description.name)

    resources = []
    if job_description.time_reserved is not None:
        resources.append('walltime={}'.format(
            _seconds_to_time(job_description.time_reserved)))

    if job_description.num_nodes is not None:
        resources.append('nodes={}'.format(job_description.num_nodes))

    if job_description.mpi_processes_per_node is not None:
        resources.append('ppn={}'.format(
            job_description.mpi_processes_per_node))

    if len(resources) > 0:
        job_script += '#PBS -l {}\n'.format(':'.join(resources))

    if job_description.queue_name is not None:
        job_script += '#PBS -q {}\n'.format(job_description.queue_name)

    if job_description.system_out_file is not None:
        job_script += '#PBS -o {}\n'.format(job_description.system_out_file)

    if job_description.system_err_file is not None:
        job_script += '#PBS -e {}\n'.format(job_description.system_err_file)

    if job_description.extra_scheduler_options is not None:
        job_script += '#PBS {}\n'.format(
                job_description.extra_scheduler_options)

    for name, value in job_description.environment.items():
        job_script += "export {}='{}'\n".format(name, value)

    if job_description.working_directory is not None:
        job_script += 'cd {}\n'.format(job_description.working_directory)

    job_script += '{}'.format(job_description.command)

    args = map(str, job_description.arguments)
    job_script += ' {}'.format(' '.join(args))

    if job_description.stdout_file is not None:
        job_script += ' >{}'.format(job_description.stdout_file)

    if job_description.stderr_file is not None:
        job_script += ' 2>{}'.format(job_description.stderr_file)

    return job_script


def _get_field_from_qstat_xml(xml_data: ElementTree, field_name: str) -> str:
    for job in xml_data:
        for field in job:
            if field.tag == field_name:
                return field.text
    raise RuntimeError(
        'Expected field {} not returned by qstat'.format(field_name))


def _seconds_to_time(seconds: int) -> str:
    """Converts seconds to a Torque allocation duration.

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
    return '{:02d}:{:02d}:{:02d}:{:02d}'.format(days, hours, minutes, seconds)
