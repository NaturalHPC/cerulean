import pytest

from cerulean.terminal import Terminal


def test_terminal(terminal: Terminal) -> None:
    exit_code, output, error = terminal.run(
            10.0,
            'echo', ['hello', 'world'])
    assert exit_code == 0
    assert output == 'hello world\n'
    assert error == ''


def test_terminal_stdin(terminal: Terminal) -> None:
    exit_code, output, error = terminal.run(
            10.0,
            'cat', [],
            'hello world\n')
    assert exit_code == 0
    assert output == 'hello world\n'
    assert error == ''


def test_terminal_workdir(terminal: Terminal) -> None:
    exit_code, output, error = terminal.run(
            10.0,
            'bash', ['-c', 'pwd'],
            None,
            '/home/cerulean/test_files')
    assert exit_code == 0
    assert output == '/home/cerulean/test_files\n'
    assert error == ''
