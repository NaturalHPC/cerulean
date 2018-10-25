from abc import ABC, abstractmethod
from types import TracebackType
from typing import List, Optional, Tuple

from cerulean.util import BaseExceptionType


class Terminal(ABC):
    """Interface for Terminals.

    This is a generic interface class that all terminals inherit \
    from, so you can use it wherever any terminal will do.

    In order to do something useful, you'll want an actual terminal,
    like a :class:`LocalTerminal` or an :class:`SshTerminal`.

    Terminals may hold resources, so you should either use them \
    with a ``with`` statement, or call :meth:`close` on them \
    when you are done with them.
    """

    def __enter__(self) -> 'Terminal':
        return self

    def __exit__(self, exc_type: Optional[BaseExceptionType],
                 exc_value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> None:
        pass

    def close(self) -> None:
        """Close the terminal.

        This closes any connections and frees resources associated \
        with the terminal. :class:`LocalTerminal` does not require \
        this, but terminals that connect to remote machines do. You \
        may want to always either close a Terminal, or use it as a \
        context manager, to avoid problems if you ever change from \
        a local terminal to a remote one.
        """
        pass

    @abstractmethod
    def run(self,
            timeout: float,
            command: str,
            args: List[str],
            stdin_data: str = None,
            workdir: str = None) -> Tuple[Optional[int], str, str]:
        """Run a shell command.

        Args:
            timeout: How long to wait for the result(s)
            command: The command to run.
            args: A list of arguments to pass
            stdin_data: Data to pass to standard input
            workdir: Working directory to execute in

        Returns:
            A tuple containing the exit code, standard output, and \
            standard error output.
        """
        pass
