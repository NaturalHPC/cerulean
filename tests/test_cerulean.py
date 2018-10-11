import io
import os
import pytest
import sh
import tempfile


def test_cerulean():
    """Runs the integration tests."""
    workdir = os.path.dirname(__file__)

    # Build cerulean-test-base first, fixes dependency issue
    output_buffer = io.StringIO()
    sh.docker.build('-t', 'cerulean-test-base', 'container-base', _cwd=workdir, _out=output_buffer)
    print(output_buffer.getvalue())
    output_buffer.close()

    output_buffer = io.StringIO()
    sh.docker_compose.build(_cwd=workdir, _out=output_buffer)
    print(output_buffer.getvalue())
    output_buffer.close()

    # Run tests
    output_buffer = io.StringIO()
    sh.docker_compose.up('cerulean-test', _cwd=workdir, _out=output_buffer)
    print(output_buffer.getvalue())
    output_buffer.close()

    # Get results
    handle, path = tempfile.mkstemp()
    os.close(handle)
    sh.docker.cp('cerulean-test:/home/cerulean/pytest_exit_codes', path)
    with open(path, 'r') as exit_code_file:
        lines = exit_code_file.readlines()
        exit_code_1 = lines[0].strip()
        assert exit_code_1 == '0'

        exit_code_2 = lines[1].strip()
        assert exit_code_2 == '0'

    # Clean up target containers
    output_buffer = io.StringIO()
    sh.docker_compose.down(_cwd=workdir, _out=output_buffer)
    print(output_buffer.getvalue())
    output_buffer.close()
