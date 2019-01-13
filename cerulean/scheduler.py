from abc import ABC, abstractmethod
from time import perf_counter, sleep
from typing import Optional

from cerulean.job_description import JobDescription
from cerulean.job_status import JobStatus


class Scheduler(ABC):
    """Interface for job schedulers.

    To run jobs using a scheduler, you will want to use \
    :class:`SlurmScheduler` or :class:`TorqueScheduler`.
    """

    @abstractmethod
    def submit(self, job_description: JobDescription) -> str:
        """Submit a job for execution.

        Args:
            job_description: A description of the job to run.

        Returns:
            A job id that can be used to keep track of it.
        """
        pass

    @abstractmethod
    def get_status(self, job_id: str) -> JobStatus:
        """Look up the status of a job.

        This method is used to check if a job is still in the queue, \
        running, or done.

        Args:
            job_id: A job id string obtained from :meth:`submit`.

        Returns:
            The status of the job as a :class:`JobStatus`
        """
        pass

    @abstractmethod
    def get_exit_code(self, job_id: str) -> Optional[int]:
        """Get the exit code of a finished job.

        Once a job is done, its exit code may be requested using this \
        method. If the job is still running or failed to start, then \
        there is no exit code, and None will be returned.

        Args:
            job_id: A job id string obtained from :meth:`submit`.

        Returns:
            The exit code, or None if there is none.
        """
        pass

    @abstractmethod
    def cancel(self, job_id: str) -> None:
        """Cancel a running job.

        Submits a cancellation request for a job to the scheduler.

        Args:
            job_id: Id of the job to be cancelled.
        """
        pass

    def wait(self, job_id: str, time_out: float = -1.0, interval: float = None
             ) -> Optional[int]:
        """Wait until the job is done.

        Will wait approximately time_out seconds for the job to finish.
        Returns the exit code if the job finished, otherwise None.

        The state of the job will be checked every `interval` seconds.
        If `interval` is None, or not specified, then the interval will
        be 1s, or time_out / 50, whichever is larger. If time_out is
        not given, the interval will start at 1s, then increase
        gradually to about 30s.

        Args:
            job_id: The job to wait for.
            time_out: Time to wait in seconds. If negative, wait \
                    forever.
            interval: Time to wait between checks. See above.

        Returns:
            The exit code of the job.
        """
        if time_out < 0.0:
            time_end = None
            fixed_interval = False
        else:
            time_end = perf_counter() + time_out
            fixed_interval = True

        if interval is None:
            # this is correct for negative time-outs as well
            interval = max(1.0, time_out / 50.0)

        status = self.get_status(job_id)
        while status != JobStatus.DONE:
            sleep(interval)
            status = self.get_status(job_id)

            if not fixed_interval and interval < 30:
                interval += 2

            if time_end is not None and time_end < perf_counter():
                break

        return self.get_exit_code(job_id)
