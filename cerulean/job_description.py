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

    def __init__(self):
        self.name = 'cerulean'
        self.working_directory = None  # Type(str)
        self.environment = dict()
        self.command = None
        self.arguments = []
        self.stdout_file = None
        self.stderr_file = None
        self.queue_name = None
        self.time_reserved = None
        self.num_nodes = None
        self.mpi_processes_per_node = None
