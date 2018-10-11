from cerulean.job_description import JobDescription
from cerulean.slurm_scheduler import _job_desc_to_job_script, _seconds_to_time


def test_job_script_name():
    job_desc = JobDescription()
    job_desc.name = 'test_name'

    script = _job_desc_to_job_script(job_desc)

    assert '#SBATCH --job-name=test_name' in script


def test_job_script_working_directory():
    # Note: doesn't test that it works, that's what test_scheduler is for
    job_desc = JobDescription()
    job_desc.working_directory = '/home/user/workdir'

    script = _job_desc_to_job_script(job_desc)

    assert '/home/user/workdir' in script


def test_job_script_command_args():
    # Note: doesn't test that it works, that's what test_scheduler is for
    job_desc = JobDescription()
    job_desc.command = 'echo'
    job_desc.arguments = ['-n', 'Hello world', 'testing']

    script = _job_desc_to_job_script(job_desc)

    assert "echo -n Hello world testing" in script


def test_job_script_stdout_file():
    # Note: doesn't test that it works, that's what test_scheduler is for
    job_desc = JobDescription()
    job_desc.stdout_file = '/home/user/test.out'

    script = _job_desc_to_job_script(job_desc)

    assert '/home/user/test.out' in script


def test_job_script_stderr_file():
    # Note: doesn't test that it works, that's what test_scheduler is for
    job_desc = JobDescription()
    job_desc.stderr_file = '/home/user/test.err'

    script = _job_desc_to_job_script(job_desc)

    assert '/home/user/test.err' in script


def test_job_script_queue_name():
    # Note: doesn't test that it works, that's what test_scheduler is for
    job_desc = JobDescription()
    job_desc.queue_name = 'testing_queue'

    script = _job_desc_to_job_script(job_desc)

    assert '#SBATCH --partition=testing_queue' in script


def test_job_script_time_reserved():
    # Note: doesn't test that it works, that's what test_scheduler is for
    job_desc = JobDescription()
    job_desc.time_reserved = 70

    script = _job_desc_to_job_script(job_desc)

    assert '00-00:01:10' in script


def test_job_script_num_nodes():
    # Note: doesn't test that it works, that's what test_scheduler is for
    job_desc = JobDescription()
    job_desc.num_nodes = 42

    script = _job_desc_to_job_script(job_desc)

    assert '#SBATCH --nodes=42' in script


def test_job_script_processes_per_node():
    job_desc = JobDescription()
    job_desc.mpi_processes_per_node = 4

    script = _job_desc_to_job_script(job_desc)

    assert '#SBATCH --ntasks-per-node=4' in script


def test_seconds_to_time():
    time = (2 * 24 * 60 * 60) + (13 * 60 * 60) + (7 * 60) + 48
    time_str = _seconds_to_time(time)
    assert time_str == '02-13:07:48'

    time_str = _seconds_to_time(2)
    assert time_str == '00-00:00:02'
