from pathlib import Path

from cerulean import Terminal

from cerulean.test.conftest import abort_on_network_error, NUM_TRIES
from paramiko.ssh_exception import SSHException


def test_terminal(terminal: Terminal) -> None:
    tries = 0
    while tries < NUM_TRIES:
        with abort_on_network_error():
            exit_code, output, error = terminal.run(
                    10.0,
                    'echo', ['hello', 'world'])
            assert exit_code == 0
            assert output == 'hello world\n'
            assert error == ''
            break
        tries += 1


def test_terminal_path(terminal: Terminal) -> None:
    tries = 0
    while tries < NUM_TRIES:
        with abort_on_network_error():
            exit_code, output, error = terminal.run(
                    10.0,
                    Path('/bin/echo'), ['hello', 'world'])
            assert exit_code == 0
            assert output == 'hello world\n'
            assert error == ''
            break
        tries += 1


def test_terminal_stdin(terminal: Terminal) -> None:
    tries = 0
    while tries < NUM_TRIES:
        with abort_on_network_error():
            exit_code, output, error = terminal.run(
                    10.0,
                    'cat', [],
                    'hello world\n')
            assert exit_code == 0
            assert output == 'hello world\n'
            assert error == ''
            break
        tries += 1


def test_terminal_workdir(terminal: Terminal) -> None:
    tries = 0
    while tries < NUM_TRIES:
        with abort_on_network_error():
            exit_code, output, error = terminal.run(
                    10.0,
                    'bash', ['-c', 'pwd'],
                    None,
                    '/home')
            assert exit_code == 0
            assert output == '/home\n'
            assert error == ''
            break
        tries += 1


def test_terminal_workdir_path(terminal: Terminal) -> None:
    tries = 0
    while tries < NUM_TRIES:
        with abort_on_network_error():
            exit_code, output, error = terminal.run(
                    10.0,
                    'bash', ['-c', 'pwd'],
                    None,
                    Path('/home'))
            assert exit_code == 0
            assert output == '/home\n'
            assert error == ''
            break
        tries += 1


def test_running_in_shell(terminal: Terminal) -> None:
    tries = 0
    while tries < NUM_TRIES:
        with abort_on_network_error():
            exit_code, output, error = terminal.run(
                    10.0,
                    'export CERULEAN=cerulean ; echo $CERULEAN', [])
            assert exit_code == 0
            assert output == 'cerulean\n'
            assert error == ''
            break
        tries += 1
