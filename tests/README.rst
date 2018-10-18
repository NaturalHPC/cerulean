Testing Cerulean
================

Testing a library that is intended to work with external hardware resources is a
bit tricky. Of course you can run unit tests, but you want to test the whole
thing as well. Cerulean solves this by using a set of Docker containers that run
simulated clusters running a variety of schedulers. The containers also contain
an SSH server, so everything can be tested.

Running the Cerulean tests is done by calling ``python3 setup.py test`` from the
root directory. When you do this, the following happens:

- ``setup.py`` runs ``pytest``
- ``pytest`` collects tests, but only in the ``tests/`` directory, finding
  ``test_cerulean.py``
- ``pytest`` runs ``test_cerulean.py``
- ``test_cerulean.py`` runs ``docker-compose pull`` to pull the images for the
  target containers from DockerHub. ``tests/docker-compose.yml`` guides this
  process.
- ``test_cerulean.py`` runs ``docker-compose build`` to build the test image.
  This copies the whole Cerulean repository into a ``cerulean-test-container``
  image.
- ``test_cerulean.py`` runs ``docker-compose up``, which launches all the target
  containers and then the ``cerulean-test-container``.
- ``pytest`` runs inside ``cerulean-test-container``, collecting tests from
  ``cerulean/test``, and running everything except scheduler tests. This uses
  ``pytest.ini`` from ``tests/container-test``.
- ``pytest`` runs a second time, still inside the container, and runs the
  scheduler tests, with some settings to make it merely take a long time, rather
  than a crazy long time. Coverage is aggregated together with the coverage
  reports from the first ``pytest`` run, and output as ``coverage.xml``.
- ``test_cerulean.py`` copies ``coverage.xml`` out of the container and into the
  main directory.

If we're running on Travis CI, the ``.travis.yml`` file in the root of the
repository contains some additional instructions for setting up the environment,
and a final command to upload the extracted ``coverage.xml`` to Codacy.

The images for the target containers are built from a `separate repository
<https://github.com/MD-Studio/cerulean-test-docker-images>`_.
