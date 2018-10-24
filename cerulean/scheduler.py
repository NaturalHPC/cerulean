from abc import ABC, abstractmethod
from typing import Optional

from cerulean.job_description import JobDescription
from cerulean.job_status import JobStatus


class Scheduler(ABC):
    """Interface for job schedulers.

    To run jobs using a scheduler, you will want to use \
    :class:`SlurmScheduler` or :class:`TorqueScheduler`.
    """

    @abstractmethod
    def submit_job(self, job_description: JobDescription) -> str:
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
            job_id: A job id string obtained from :meth:`submit_job`.

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
            job_id: A job id string obtained from :meth:`submit_job`.

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
