from typing import Optional, Union

from cerulean.job_description import JobDescription
from cerulean.job_status import JobStatus
from cerulean.scheduler import Scheduler
from cerulean.terminal import Terminal


class SlurmScheduler(Scheduler):
    def __init__(self, terminal: Terminal) -> None:
        self.__terminal = terminal

    def submit_job(self, job_description: JobDescription) -> str:
        if job_description.command is None:
            raise ValueError('Job description is missing a command')

        job_script = _job_desc_to_job_script(job_description)
        print('job script: {}'.format(job_script))

        exit_code, output, error = self.__terminal.run(10, 'sbatch', [],
                                                       job_script, None)

        print('sbatch output ({}): {}'.format(exit_code, output))
        print('sbatch error ({}): {}'.format(exit_code, error))

        job_id = output.strip().split(' ')[-1]
        return job_id

    def get_status(self, job_id: str) -> JobStatus:
        exit_code, output, error = self.__terminal.run(
            10, 'squeue', ['-j', job_id, '-h', '-o', '%T'], None, None)
        print('squeue output ({}): {}'.format(exit_code, output))
        print('squeue error ({}): {}'.format(exit_code, error))

        status = output.strip()
        if status == '':
            # Seems like SLURM sometimes does not show the job, possibly
            # because it's transitioning to COMPLETING. So
            # if we don't find it, try again to be a bit more robust.
            exit_code, output, error = self.__terminal.run(
                10, 'squeue', ['-j', job_id, '-h', '-o', '%T'])
            status = output.strip()
            print('squeue output 2: {}'.format(status))

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

        print('get_status returning {}'.format(job_status.name))

        return job_status

    def get_exit_code(self, job_id: str) -> Optional[int]:
        if self.get_status(job_id) != JobStatus.DONE:
            return None

        err, output, error = self.__terminal.run(
            10, 'sacct', ['-j', job_id, '--noheader', '--format=ExitCode'])
        print('sacct output ({}): {} {}'.format(err, output, error))

        exit_code = int(output.lstrip().split(':')[0])
        return exit_code

    def cancel(self, job_id: str) -> None:
        self.__terminal.run(10, 'scancel', [job_id])


def _job_desc_to_job_script(job_description: JobDescription) -> str:
    job_script = '#!/bin/bash\n'
    job_script = _add_option(job_script, 'job-name', job_description.name)

    if job_description.time_reserved is not None:
        job_script += '#SBATCH --time={}\n'.format(
            _seconds_to_time(job_description.time_reserved))

    job_script = _add_option(job_script, 'partition',
                             job_description.queue_name)
    job_script = _add_option(job_script, 'nodes', job_description.num_nodes)
    job_script = _add_option(job_script, 'ntasks-per-node',
                             job_description.mpi_processes_per_node)
    if job_description.mpi_processes_per_node is not None:
        job_script = _add_option(job_script, 'overcommit', '')

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


def _add_option(job_script: str, option: str,
                value: Optional[Union[int, str]]) -> str:
    if value is not None:
        if value is not '':
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
