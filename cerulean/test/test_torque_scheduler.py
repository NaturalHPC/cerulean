from cerulean import JobDescription
from cerulean.torque_scheduler import (
        _job_desc_to_job_script, _seconds_to_time)


def test_job_script_name() -> None:
    job_desc = JobDescription()
    job_desc.name = 'test_name'

    script = _job_desc_to_job_script(job_desc)

    assert '#PBS -N test_name' in script


def test_job_script_working_directory() -> None:
    # Note: doesn't test that it works, that's what test_scheduler is for
    job_desc = JobDescription()
    job_desc.working_directory = '/home/user/workdir'

    script = _job_desc_to_job_script(job_desc)

    assert '/home/user/workdir' in script


def test_job_script_command_args() -> None:
    # Note: doesn't test that it works, that's what test_scheduler is for
    job_desc = JobDescription()
    job_desc.command = 'echo'
    job_desc.arguments = ['-n', 'Hello world', 'testing']

    script = _job_desc_to_job_script(job_desc)

    assert "echo -n Hello world testing" in script


def test_job_script_stdout_file() -> None:
    # Note: doesn't test that it works, that's what test_scheduler is for
    job_desc = JobDescription()
    job_desc.stdout_file = '/home/user/test.out'

    script = _job_desc_to_job_script(job_desc)

    assert '/home/user/test.out' in script


def test_job_script_stderr_file() -> None:
    # Note: doesn't test that it works, that's what test_scheduler is for
    job_desc = JobDescription()
    job_desc.stderr_file = '/home/user/test.err'

    script = _job_desc_to_job_script(job_desc)

    assert '/home/user/test.err' in script


def test_job_script_queue_name() -> None:
    # Note: doesn't test that it works, that's what test_scheduler is for
    job_desc = JobDescription()
    job_desc.queue_name = 'testing_queue'

    script = _job_desc_to_job_script(job_desc)

    assert '#PBS -q testing_queue' in script


def test_job_script_time_reserved() -> None:
    # Note: doesn't test that it works, that's what test_scheduler is for
    job_desc = JobDescription()
    job_desc.time_reserved = 70

    script = _job_desc_to_job_script(job_desc)

    assert '00:00:01:10' in script


def test_job_script_num_nodes() -> None:
    # Note: doesn't test that it works, that's what test_scheduler is for
    job_desc = JobDescription()
    job_desc.num_nodes = 42

    script = _job_desc_to_job_script(job_desc)

    assert 'nodes=42' in script


def test_job_script_processes_per_node() -> None:
    job_desc = JobDescription()
    job_desc.mpi_processes_per_node = 4

    script = _job_desc_to_job_script(job_desc)

    assert 'ppn=4' in script


def test_job_script_extra_scheduler_options() -> None:
    job_desc = JobDescription()
    job_desc.extra_scheduler_options = '-p 10'

    script = _job_desc_to_job_script(job_desc)

    assert '#PBS -p 10' in script


def test_seconds_to_time() -> None:
    time = (2 * 24 * 60 * 60) + (13 * 60 * 60) + (7 * 60) + 48
    time_str = _seconds_to_time(time)
    assert time_str == '02:13:07:48'

    time_str = _seconds_to_time(2)
    assert time_str == '00:00:00:02'
