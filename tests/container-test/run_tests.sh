#!/bin/bash

# Note: mypy can take a long time to run, so don't set the timeout too tight

for VERSION in 3.7 3.8 3.9 3.10 3.11 3.12 ; do

    rm -rf .venv
    python${VERSION} -m venv .venv
    . .venv/bin/activate && python -m pip install --upgrade pip wheel
    . .venv/bin/activate && python -m pip install -r /home/cerulean/test_requirements.txt

    . .venv/bin/activate && python -m pytest --timeout=120 -k 'not test_scheduler' --mypy --cov=cerulean --cov-report term-missing

    result="$?"
    echo "$result" >/home/cerulean/pytest_exit_codes
    if [ "$result" != "0" ] ; then
        exit $result
    fi

    # clean up test files for the subsequent tests
    chmod 755 /home/cerulean/test_files/testdir/dir1
    rm -rf /home/cerulean/test_files/testdir

done


if [ "$CI" == 'true' ] ; then
    pytest --timeout=300 -s -vv --log-cli-level=DEBUG -k 'test_scheduler and not flaky' -v -n 4 --max-worker-restart=0 --cov=cerulean --cov-append --cov-report term-missing --cov-report xml
else
    pytest --timeout=600 -s -vv --log-cli-level=DEBUG -k 'test_scheduler' -v -n 8 --max-worker-restart=0 --cov=cerulean --cov-append --cov-report term-missing --cov-report xml
fi
echo "$?" >>/home/cerulean/pytest_exit_codes

