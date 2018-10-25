from typing import Dict, List, Optional

from pathlib import PurePath


class JobDescription:
    """Describes a job to submit to a scheduler.

    Attributes:
        working_directory (str): The working directory to execute in.
        command (str): The command to execute.
        arguments (list of str): A list of arguments to pass. If needed, \
                you need to add quotes yourself, the arguments will not \
                be escaped by cerulean.
        stdout_file (str): File to direct standard output to.
        stderr_file (str): File to direct standard error to.
        time_reserved (int): Time to reserve, in seconds.
        queue_name (str): Name of the queue to submit to.
        mpi_processes_per_node (int): Number of MPI processes to start per \
                node.
        extra_scheduler_options (str): Additional options to add to the \
                scheduler command line on job submission. Note that these \
                are scheduler-specific!
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
        self.extra_scheduler_options = None  # type: Optional[str]
