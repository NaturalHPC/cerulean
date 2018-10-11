from abc import ABC, abstractmethod

from cerulean.job_description import JobDescription
from cerulean.job_status import JobStatus


class Scheduler(ABC):
    """Interface for job schedulers."""

    @abstractmethod
    def submit_job(self, job_description: JobDescription) -> str:
        pass

    @abstractmethod
    def get_status(self, job_id: str) -> JobStatus:
        pass

    @abstractmethod
    def get_exit_code(self, job_id: str) -> int:
        pass

    @abstractmethod
    def cancel(self, job_id: str) -> None:
        pass
