import os
from pathlib import Path
import pytest
import sh
import sys
import tempfile
from time import sleep


CLEAN_UP_CONTAINERS = True


@pytest.fixture
def container_prefix():
    # Use the top for local testing, bottom for getting images from GHCR
    # return 'naturalhpc/'
    return 'ghcr.io/naturalhpc/'


@pytest.fixture
def server_names():
    names = [
            'ssh', 'sftp', 'webdav', 'torque-6', 'slurm-17-02', 'slurm-17-11',
            'slurm-18-08', 'slurm-19-05', 'slurm-20-02', 'slurm-20-11',
            'slurm-21-08', 'slurm-22-05', 'slurm-23-02', 'slurm-23-11', 'slurm-24-05',
            'slurm-24-11', 'flaky']

    name_to_image = dict(zip(names, map(lambda n: 'cerulean-fake-' + n, names)))

    name_to_image['ssh'] = 'cerulean-fake-scheduler'
    name_to_image['sftp'] = 'cerulean-fake-fileserver'
    name_to_image['flaky'] = 'cerulean-fake-slurm-flaky'

    return name_to_image


@pytest.fixture
def cleanup_docker(server_names):
    # Clean up leftovers from previous crashed run
    sh.docker.rm('-f', 'cerulean-test')

    for name in server_names:
        sh.docker.rm('-f', 'cerulean-test-' + name)

    sh.docker.network.rm('-f', 'cerulean')


@pytest.fixture
def network(cleanup_docker):
    name = 'cerulean'
    sh.docker.network.create(name)
    yield name

    # We could sh.docker.network.rm(name) here, but we don't so we can leave the test
    # container and access the logs if needed, especially on the CI.


@pytest.fixture
def server_containers(cleanup_docker, container_prefix, server_names, network):
    for name, img in server_names.items():
        full_name = 'cerulean-test-' + name
        sh.docker.rm('-f', full_name)

        if name == 'torque-6':
            sh.docker.run(
                    '-d', '--name', full_name, '--network', network,
                    '--hostname', 'headnode', '--env', 'SELF_CONTAINED=1',
                    '--cap-add', 'CAP_SYS_RESOURCE', container_prefix + img)
        elif name.startswith('slurm') and (
                 int(name[6:8]) <= 19 or name[6:11] == '20-02'):
            slurm_version = name[6:]
            sh.docker.run(
                    '-d', '--name', full_name, '--network', network,
                    '--hostname', 'headnode', '--env', 'SELF_CONTAINED=1',
                    '--env', f'SLURM_VERSION={slurm_version}',
                    '--cap-add', 'CAP_SYS_NICE',
                    container_prefix + 'cerulean-fake-slurm-base-old')
        elif name.startswith('slurm') and (
                name[6:11] == '20-11' or int(name[6:8]) >= 21):
            slurm_version = name[6:]
            sh.docker.run(
                    '-d', '--name', full_name, '--network', network,
                    '--hostname', 'headnode', '--env', 'SELF_CONTAINED=1',
                    '--env', f'SLURM_VERSION={slurm_version}',
                    '--cap-add', 'CAP_SYS_NICE',
                    container_prefix + 'cerulean-fake-slurm-base')
        else:
            sh.docker.run(
                    '-d', '--name', full_name, '--network', network,
                    '--hostname', 'headnode', '--env', 'SELF_CONTAINED=1',
                    '--cap-add', 'CAP_SYS_NICE', container_prefix + img)

    healthy = [False]
    while not all(healthy):
        sleep(3)
        healthy = list()
        for name in server_names:
            full_name = 'cerulean-test-' + name
            try:
                result = sh.docker.inspect('--format={{.State.Health.Status}}', full_name)
                if result.strip() == 'unhealthy':
                    raise RuntimeError(f'Unhealthy container {full_name}')
                healthy.append(result.strip() == 'healthy')
            except sh.ErrorReturnCode_1:
                # no health data available, hope for the best
                pass

    yield

    if CLEAN_UP_CONTAINERS:
        for name in server_names:
            sh.docker.rm('-f', 'cerulean-test-' + name)


@pytest.fixture
def test_image():
    name = 'cerulean-test-container'
    topdir = Path(__file__).parents[1]
    sh.docker.build(
            '-f', 'tests/container-test/Dockerfile',
            '--tag', name, topdir)
    return name


def test_cerulean(cleanup_docker, network, server_containers, test_image, tmp_path):
    """Runs the integration tests."""
    try:
        sh.docker.run(
                '--name', 'cerulean-test', '--network', network,
                test_image)
    except Exception as e:
        print(e.stdout.decode('utf-8'))

    test_out_path = tmp_path / 'test_out.txt'
    sh.docker.cp('cerulean-test:/home/cerulean/test_out.txt', test_out_path)

    ec_path = tmp_path / 'pytest_exit_codes'
    sh.docker.cp('cerulean-test:/home/cerulean/pytest_exit_codes', ec_path)
    with open(ec_path, 'r') as exit_code_file:
        lines = exit_code_file.readlines()

    cov_path = Path(__file__).parent / 'coverage.xml'
    sh.docker.cp('cerulean-test:/home/cerulean/cerulean/coverage.xml', cov_path)

    # We could sh.docker.rm('cerulean-test') here, but we don't so that we can always
    # debug, and so that we can print the logs on the CI and have a chance of finding
    # out what went wrong there.

    for line in lines:
        exit_code = line.strip()
        assert exit_code == '0'
