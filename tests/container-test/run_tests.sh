#!/bin/bash

pytest --timeout=10 -k 'not test_scheduler' --mypy --cov=cerulean --cov-report term-missing
result="$?"
echo "$result" >/home/cerulean/pytest_exit_codes
if [ "$result" != "0" ] ; then
    exit $result
fi

pytest --timeout=120 -k 'test_scheduler' -n 2 --max-worker-restart=0 --cov=cerulean --cov-append --cov-report term-missing --cov-report xml
echo "$?" >>/home/cerulean/pytest_exit_codes
