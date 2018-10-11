from enum import Enum


class JobStatus(Enum):
    WAITING = 1
    RUNNING = 2
    DONE = 3
