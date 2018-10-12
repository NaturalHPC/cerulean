import io
import os
import pytest
import sh
import sys
import tempfile


@pytest.fixture
def target_images():
    workdir = os.path.dirname(__file__)

    # Build cerulean-test-base first, fixes dependency issue
    sh.docker.build('-t', 'cerulean-test-base', 'container-base', _cwd=workdir, _out=sys.stdout)

    sh.docker_compose.build(_cwd=workdir, _out=sys.stdout)


def test_cerulean(target_images):
    """Runs the integration tests."""
    workdir = os.path.dirname(__file__)

    # Run tests
    sh.docker_compose.up('cerulean-test', _cwd=workdir, _out=sys.stdout)

    # Get results
    handle, path = tempfile.mkstemp()
    os.close(handle)
    sh.docker.cp('cerulean-test:/home/cerulean/pytest_exit_codes', path)
    with open(path, 'r') as exit_code_file:
        lines = exit_code_file.readlines()

    # Clean up target containers
    sh.docker_compose.down(_cwd=workdir, _out=sys.stdout)

    exit_code_1 = lines[0].strip()
    assert exit_code_1 == '0'

    exit_code_2 = lines[1].strip()
    assert exit_code_2 == '0'
