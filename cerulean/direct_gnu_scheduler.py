import logging
from typing import Optional

from cerulean.job_description import JobDescription
from cerulean.job_status import JobStatus
from cerulean.scheduler import Scheduler
from cerulean.terminal import Terminal


logger = logging.getLogger(__name__)


class DirectGnuScheduler(Scheduler):
    """A scheduler that runs processes directly on a GNU system.

    This scheduler does not have a queue, instead it launches each job
    immediately as a process, and uses ps and kill to manage it.

    This should work fine on any normal GNU/Linux system, but in some cases you
    may need an extra command to make bash, ps and/or kill available (e.g.
    setting a PATH). If so, you can specify prefix, and it will be prepended
    onto these commands. Note that this is a simple string concatenation, so
    you may need a semicolon at the end depending your exact prefix command.
    """
    def __init__(self, terminal: Terminal, prefix: str = '') -> None:
        """Create a DirectGnuScheduler.

        Args:
            terminal: The terminal to execute on.
            prefix: A string to prefix the shell commands with.
        """
        self.__terminal = terminal
        self.__prefix = prefix

    def submit(self, job_description: JobDescription) -> str:
        if job_description.command is None:
            raise ValueError('Job description is missing a command')

        if job_description.mpi_processes_per_node is not None:
            raise RuntimeError(
                'mpi_processes_per_node is not supported by DirectGnuScheduler,'
                ' because we cannot inject this into the MPI configuration in an'
                ' environment without a scheduler. You should call mpirun with an'
                ' appropriate parameter instead.')

        job_script = ''

        for name, value in job_description.environment.items():
            job_script += "export {}='{}'\n".format(name, value)

        if job_description.working_directory is not None:
            job_script += 'cd {}\n'.format(job_description.working_directory)

        job_script += 'exit_code_file=$(mktemp)\n'
        job_script += "(\n"

        escaped_command = job_description.command.replace(
                "'", "'\\\''")    # type: ignore
        escaped_args = map(lambda s: s.replace("'", "'\\\''"),
                           job_description.arguments)

        job_script += "bash -c '"

        if job_description.time_reserved is not None:
            job_script += "timeout {} ".format(job_description.time_reserved)

        job_script += '{}'.format(escaped_command)
        job_script += ' {}'.format(' '.join(escaped_args))

        if job_description.stdout_file is not None:
            job_script += ' >{}'.format(job_description.stdout_file)

        if job_description.stderr_file is not None:
            job_script += ' 2>{}'.format(job_description.stderr_file)

        job_script += "' ; "
        job_script += 'echo $? >$exit_code_file'
        job_script += ')'

        if job_description.system_out_file is not None:
            job_script += ' >{}'.format(job_description.system_out_file)
        else:
            job_script += ' >/dev/null'

        if job_description.system_err_file is not None:
            job_script += ' 2>{}'.format(job_description.system_err_file)
        else:
            job_script += ' 2>/dev/null'

        job_script += ' &\n'

        job_script += 'echo -n $! $exit_code_file\n'
        job_script += 'disown\n'

        logger.debug('Job script: %s', job_script)
        command = self.__prefix + ' bash'
        _, output, error = self.__terminal.run(
                10.0, command, [], job_script)

        return output

    def get_status(self, job_id: str) -> JobStatus:
        pid = job_id.split(' ')[0]
        logger.debug('Running ps -p %s', pid)
        command = self.__prefix + ' ps'
        exit_code, output, error = self.__terminal.run(10.0, command, ['-p', pid])

        logger.debug('ps exit code: %s', exit_code)
        logger.debug('ps output: %s', output)
        logger.debug('ps error: %s', error)

        if exit_code == 0:
            return JobStatus.RUNNING

        return JobStatus.DONE

    def get_exit_code(self, job_id: str) -> Optional[int]:
        exit_code_file = job_id.split(' ', maxsplit=1)[1]
        logger.debug('Running cat %s', exit_code_file)
        command = self.__prefix + ' cat'
        exit_code, output, error = self.__terminal.run(10.0, command,
                                                       [exit_code_file])
        logger.debug('cat exit code: %s', exit_code)
        logger.debug('cat output: %s', output)
        logger.debug('cat error: %s', error)
        # TODO: delete tempfile?
        try:
            return int(output)
        except ValueError:
            return None

    def cancel(self, job_id: str) -> None:
        pid = job_id.split(' ')[0]
        logger.debug('Running kill %s', pid)
        command = self.__prefix + ' kill'
        exit_code, output, error = self.__terminal.run(10.0, command, [pid])

        logger.debug('kill exit code: %s', exit_code)
        logger.debug('kill output: %s', output)
        logger.debug('kill error: %s', error)
        # TODO: Check exit code and return whether it was running?
        # TODO: Check if it's stopped, do a -9 if not?
