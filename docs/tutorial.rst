========
Tutorial
========

Welcome to the Cerulean tutorial. This tutorial demonstrates the basics of using
Cerulean: using local and remote file systems, running processes locally and
remotely, and using schedulers.

To install Cerulean, use

.. code-block:: bash

  pip install cerulean

If you're using Cerulean in a program, you will probably want to use a
virtualenv and install Cerulean into that, together with your other
dependencies.


Accessing files
===============

The file access functions of Cerulean use a ``pathlib``-like API, but unlike in
``pathlib``, Cerulean supports remote file systems. That means that there is no
longer just the local file system, but multiple file systems, and that Path
objects have a particular file system that they are on.

Of course, Cerulean also supports the local file system. To make an object
representing the local file system, you use this:

.. code-block:: python

  import cerulean

  fs = cerulean.LocalFileSystem()

And then you can make a path on the file system using:

.. code-block:: python

  import cerulean

  fs = cerulean.LocalFileSystem()
  my_home_dir = fs / 'home' / 'username'

In this example, ``my_home_dir`` will be a :class:``cerulean.Path`` object,
which is very similar to a normal Python ``pathlib.PosixPath``. For example, you
can read the contents of a file through it:

.. code-block:: python

  import cerulean

  fs = cerulean.LocalFileSystem()
  passwd_file = fs / 'etc' / 'passwd'

  users = passwd_file.read_text()
  print(users)

Note that ``cerulean.Path`` does not support ``open()``. Cerulean can copy files
and stream data from and to them, but it does not offer random access, as not
all remote file access protocols support this.

You can use the ``/`` operator to build paths from components as with
``pathlib``, and there's a wide variety of supported operations. See the API
documentation for :class:``cerulean.Path`` for details.

Remote filesystems
------------------

Cerulean supports remote file systems through the SFTP protocol. (It uses the
Paramiko library internally for this.) Accessing a remote file system through
SFTP goes like this:

.. code-block:: python

  import cerulean

  credential = cerulean.PasswordCredential('username', 'password')
  term = cerulean.SshTerminal('remotehost.example.com', 22, credential)
  fs = SftpFileSystem(term)

  my_home_dir = fs / 'home' / 'username'
  test_txt = (my_home_dir / 'test.txt').read_text()
  print(test_txt)

  # But see the safer example below
  fs.close()
  term.close()

Since we are going to connect to a remote system, we need a credential.
Cerulean has two types of credentials, :class:``PasswordCredential`` and
:class:``PubKeyCredential``. They are what you expect, one holds a username and
a password, the other a username, a local path to a public key file, and
optionally a passphrase for the key.

Once we have a credential, we can open a terminal. Like a terminal window on
your desktop, a :class:``Terminal`` object lets you run commands. Cerulean
supports local terminals and remote terminals through SSH. Since the SFTP
protocol is an extension to the SSH protocol, we need an SSH terminal connection
first, so we make one, connecting to a host, on a port, with our credential.

Once we have the terminal, we can make an :class:``SftpFileSystem`` object, and
from there it works just like a local file system. There is one exception
though: the remote connection needs to be closed when we are done. This can be
done by calling ``close()`` on the file system and then on the terminal.
However, both :class:``SshTerminal`` and :class:``SftpFileSystem`` are context
managers, and that's the safer and more Pythonic way to deal with this:

.. code-block:: python

  import cerulean

  credential = cerulean.PasswordCredential('username', 'password')
  with cerulean.SshTerminal('remotehost.example.com', 22, credential) as term
      with SftpFileSystem(term) as fs:
          my_home_dir = fs / 'home' / 'username'
          test_txt = (my_home_dir / 'test.txt').read_text()
          print(test_txt)


Running commands
================

If you have read the above, then the secret is already out: running commands
using Cerulean is done using a :class:``Terminal``. For example, you can run a
command locally using:

.. code-block:: python

  import cerulean

  term = cerulean.LocalTerminal()

  exit_code, stdout_text, stderr_text = term.run(
          10.0, 'ls', ['-l'], None, '/home/username')

The first argument to :meth:``Terminal.run`` is a timeout value in seconds,
which determines how long Cerulean will wait for the command to finish. The
second argument is the command to run, followed by a list of arguments. Next is
an optional string that, if you specify it, will be fed into the standard input
of the program you are starting. The final argument is a string specifying the
working directory in which to execute the command.

The function returns a tuple containing three values: the exit code of the
process (or `None` if it didn't finish in time), a string containing text
printed to standard output, and a string containing text printed to standard
error by the command you ran.

Running commands remotely through SSH of course works in exactly the same way,
except you use an :class:``SshTerminal``, as above:

.. code-block:: python

  import cerulean

  credential = cerulean.PasswordCredential('username', 'password')
  with cerulean.SshTerminal('remotehost.example.com', 22, credential) as term
      exit_code, stdout_text, stderr_text = term.run(
              10.0, 'ls', ['-l'], None, '/home/username')


Submitting jobs
===============

On High-Performance Computing machines, you don't run commands directly.
Instead, you submit batch jobs to a scheduler, which will place them in a queue,
and run them when everyone else in line before you is done. The most popular
scheduler at the moment seems to be Slurm, but Cerulean also supports
Torque/PBS. To use a scheduler by hand, you open a terminal on the HPC machine
using SSH, and then run commands that submit jobs and check on their status.
Cerulean works in the same way:

.. code-block:: python

  import cerulean
  import time

  credential = cerulean.PasswordCredential('username', 'password')
  with cerulean.SshTerminal('remotehost.example.com', 22, credential) as term
      sched = cerulean.SlurmScheduler(term)

      job = cerulean.JobDescription()
      job.name = 'cerulean_test'
      job.command = 'ls'
      job.arguments = ['-l']

      job_id = sched.submit_job(job)

      time.sleep(5)
      status = sched.get_status(job_id)

      if status == cerulean.JobStatus.DONE:
          exit_code = sched.get_exit_code()
          print('Job exited with code {}'.format(exit_code))

Of course, if you intend to run your submission script on the head node, then
the scheduler is local, and you want to use a :class:``LocalTerminal`` with your
:class:``SlurmScheduler``. If your HPC machine runs Torque/PBS, use a
:class:``TorqueScheduler`` instead.


More information
================

To find all the details of what Cerulean can do and how to do it, please refer
to the :doc:`API documentation<apidocs/cerulean>`.
