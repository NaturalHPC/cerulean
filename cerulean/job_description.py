from typing import Dict, List, Optional

from pathlib import PurePath


class JobDescription:
    """Describes a job to submit to a scheduler.

    Attributes:
        working_directory: The working directory to execute in.
        command: The command to execute.
        arguments: A list of arguments to pass. If needed, you need to \
                add quotes yourself, the arguments will not be escaped \
                by cerulean.
        stdout_file: File to direct standard output to.
        stderr_file: File to direct standard error to.
        time_reserved: Time to reserve, in seconds.
        queue_name: Name of the queue to submit to.
        mpi_processes_per_node: Number of MPI processes to start per \
                node.
    """

    def __init__(self) -> None:
        self.name = 'cerulean'
        self.working_directory = None  # type: Optional[str]
        self.environment = dict()   # type: Dict[str, str]
        self.command = None # type: Optional[str]
        self.arguments = [] # type: List[str]
        self.stdout_file = None # type: Optional[str]
        self.stderr_file = None # type: Optional[str]
        self.queue_name = None  # type: Optional[str]
        self.time_reserved = None   # type: Optional[int]
        self.num_nodes = None   # type: Optional[int]
        self.mpi_processes_per_node = None  # type: Optional[int]
