from pathlib import Path

from cerulean import Terminal


def test_terminal(terminal: Terminal) -> None:
    exit_code, output, error = terminal.run(
            10.0,
            'echo', ['hello', 'world'])
    assert exit_code == 0
    assert output == 'hello world\n'
    assert error == ''


def test_terminal_path(terminal: Terminal) -> None:
    exit_code, output, error = terminal.run(
            10.0,
            Path('/bin/echo'), ['hello', 'world'])
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


def test_terminal_workdir_path(terminal: Terminal) -> None:
    exit_code, output, error = terminal.run(
            10.0,
            'bash', ['-c', 'pwd'],
            None,
            Path('/home/cerulean/test_files'))
    assert exit_code == 0
    assert output == '/home/cerulean/test_files\n'
    assert error == ''


def test_running_in_shell(terminal: Terminal) -> None:
    exit_code, output, error = terminal.run(
            10.0,
            'export CERULEAN=cerulean ; echo $CERULEAN', [])
    assert exit_code == 0
    assert output == 'cerulean\n'
    assert error == ''
