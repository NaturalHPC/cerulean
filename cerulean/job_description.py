from typing import Dict, List, Optional

from pathlib import PurePath


class JobDescription:
    """Describes a job to submit to a scheduler.

    Attributes:
        name (str): The name of the job, with which it will show up in \
                the scheduler's queue. Cerulean does not use the name, \
                but it may be useful if you manually check the queue.
        working_directory (str): The working directory to execute in.
        environment (Dict[str, str]): A dictionary of environment \
                variables to define, and their values.
        command (str): The command to execute.
        arguments (list of str): A list of arguments to pass. If needed, \
                you need to add quotes yourself, the arguments will not \
                be escaped by cerulean.
        stdout_file (str): File to direct standard output to.
        stderr_file (str): File to direct standard error to.
        queue_name (str): Name of the queue to submit to.
        time_reserved (int): Time to reserve, in seconds.
        num_nodes (int): The number of nodes to reserve.
        mpi_processes_per_node (int): Number of MPI processes to start per \
                node.
        system_out_file (str): File to direct the standard output of \
                the scheduler to.
        system_err_file (str): File to direct the standard error of \
                the scheduler to.
        extra_scheduler_options (str): Additional options to add to the \
                scheduler command line on job submission. Note that these \
                are scheduler-specific!

        Note that stdout_file and stderr_file will receive the output \
        of the process you are starting, while system_out_file and \
        system_err_file will receive messages from the scheduler (e.g. \
        that the job ran out of its time limit and was killed). If \
        stdout_file and/or stderr_file are not specified but \
        system_out_file and/or system_err_file are, then the command \
        output/error will end up in the system output/error file \
        together with the scheduler output.
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
        self.system_out_file = None # type: Optional[str]
        self.system_err_file = None # type: Optional[str]
        self.extra_scheduler_options = None  # type: Optional[str]
