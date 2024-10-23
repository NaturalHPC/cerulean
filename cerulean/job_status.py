from enum import Enum


class JobStatus(Enum):
    """States that a scheduler job can be in."""
    WAITING = 1
    RUNNING = 2
    DONE = 3
