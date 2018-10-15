from abc import ABC, abstractmethod
from typing import List, Optional, Tuple


class Terminal(ABC):
    """Interface for Terminals."""

    @abstractmethod
    def run(self,
            timeout: float,
            command: str,
            args: List[str],
            stdin_data: str = None,
            workdir: str = None) -> Tuple[Optional[int], str, str]:
        """Run a shell command.

        Args:
            timeout: How long to wait for the result (s)
            command: The command to run.
            args: A list of arguments to pass
            stdin_data: Data to pass to standard input
            workdir: Working directory to execute in

        Returns:
            A tuple containing the exit code, standard output, and \
            standard error output.
        """
        pass
