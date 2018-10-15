from typing import Optional, Tuple

from cerulean.job_description import JobDescription
from cerulean.job_status import JobStatus
from cerulean.scheduler import Scheduler
from cerulean.terminal import Terminal
from defusedxml import ElementTree


class TorqueScheduler(Scheduler):
    def __init__(self, terminal: Terminal) -> None:
        self.__terminal = terminal

    def submit_job(self, job_description: JobDescription) -> str:
        if job_description.command is None:
            raise ValueError('Job description is missing a command')

        job_script = _job_desc_to_job_script(job_description)
        exit_code, output, error = self.__terminal.run(10, 'qsub', ['-'],
                                                       job_script)

        print('qsub output ({}): {}'.format(exit_code, output))
        print('qsub error ({}): {}'.format(exit_code, error))

        if exit_code != 0:
            raise RuntimeError('Torque qsub error: {}'.format(error))

        job_id = output.strip().split(' ')[-1]
        return job_id

    def get_status(self, job_id: str) -> JobStatus:
        exit_code, output, error = self.__terminal.run(10, 'qstat',
                                                       ['-x', job_id])
        print('qstat output ({}): {}'.format(exit_code, output))
        print('qstat error ({}): {}'.format(exit_code, error))

        xml_data = ElementTree.fromstring(output)
        if len(xml_data) == 0:
            return JobStatus.DONE

        status = _get_field_from_qstat_xml(xml_data, 'job_state')
        print('qstat status: {}'.format(status))

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

        print('get_status returning {}'.format(job_status.name))
        return job_status

    def get_exit_code(self, job_id: str) -> Optional[int]:
        if self.get_status(job_id) != JobStatus.DONE:
            return None

        exit_code, output, error = self.__terminal.run(10, 'qstat',
                                                       ['-x', job_id])
        print('qstat output ({}): {}'.format(exit_code, output))
        print('qstat error ({}): {}'.format(exit_code, error))

        xml_data = ElementTree.fromstring(output)
        job_exit_code = int(_get_field_from_qstat_xml(xml_data, 'exit_status'))
        return job_exit_code

    def cancel(self, job_id: str) -> None:
        err, output, error = self.__terminal.run(10, 'qdel', [job_id])


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

    for name, value in job_description.environment.items():
        job_script += "export {}='{}'\n".format(name, value)

    if job_description.working_directory is not None:
        job_script += 'cd {}\n'.format(job_description.working_directory)

    job_script += '{}'.format(job_description.command)

    args = map(lambda arg: "{}".format(arg), job_description.arguments)
    job_script += ' {}'.format(' '.join(args))

    if job_description.stdout_file is not None:
        job_script += ' >{}'.format(job_description.stdout_file)

    if job_description.stderr_file is not None:
        job_script += ' 2>{}'.format(job_description.stderr_file)

    print('job script: {}'.format(job_script))
    return job_script


def _get_field_from_qstat_xml(xml_data: ElementTree, field_name: str) -> str:
    value = None
    for job in xml_data:
        print('job: {}'.format(job.tag))
        for field in job:
            print('qstat xml field: {} {}'.format(field.tag, field.text))
            if field.tag == field_name:
                return field.text
    raise RuntimeError(
        'Expected field {} not returned by qstat'.format(field_name))


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
    return '{:02d}:{:02d}:{:02d}:{:02d}'.format(days, hours, minutes, seconds)
