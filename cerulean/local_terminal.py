from subprocess import PIPE, Popen
from typing import List, Optional, Tuple

from cerulean.terminal import Terminal


class LocalTerminal(Terminal):

    def run(self,
            timeout: float,
            command: str,
            args: List[str],
            stdin_data: str = None,
            workdir: str = None) -> Tuple[Optional[int], str, str]:

        all_args = [command] + args
        if workdir is not None:
            workdir = str(workdir)
        print('LocalTerminal running {}'.format(all_args))
        with Popen(
                all_args,
                stdin=PIPE,
                stdout=PIPE,
                cwd=workdir,
                universal_newlines=True) as process:
            stdout_text, stderr_text = process.communicate(
                stdin_data, timeout=timeout)

        print('LocalTerminal output {}'.format(stdout_text))
        print('LocalTerminal error {}'.format(stderr_text))
        if stderr_text is None:
            stderr_text = ''
        return process.returncode, stdout_text, stderr_text
