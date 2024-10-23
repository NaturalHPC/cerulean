import logging
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Any, List, Optional, Tuple, Union

from cerulean.terminal import Terminal


logger = logging.getLogger(__name__)


class LocalTerminal(Terminal):
    """A Terminal for running commands on the local machine.

    To create one, just do ``term = LocalTerminal()``.
    """
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Terminal):
            return NotImplemented
        return isinstance(other, LocalTerminal)

    def run(
            self, timeout: float, command: Union[str, Path], args: List[str],
            stdin_data: Optional[str] = None, workdir: Optional[Union[str, Path]] = None
            ) -> Tuple[Optional[int], str, str]:

        whole_command = '{} {}'.format(command, ' '.join(args))
        logger.debug('LocalTerminal running %s', whole_command)
        with Popen(
                whole_command, stdin=PIPE, stdout=PIPE, cwd=workdir, shell=True,
                universal_newlines=True) as process:
            stdout_text, stderr_text = process.communicate(stdin_data, timeout=timeout)

        logger.debug('LocalTerminal output %s', stdout_text)
        logger.debug('LocalTerminal error %s', stderr_text)
        if stderr_text is None:
            stderr_text = ''
        return process.returncode, stdout_text, stderr_text
