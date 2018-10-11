#!/bin/bash

pytest --timeout=10 -k 'not test_scheduler' --cov=cerulean --cov-report term-missing
echo "$?" >/home/cerulean/pytest_exit_codes

pytest --timeout=120 -k 'test_scheduler' -n 2 --cov=cerulean --cov-report term-missing --cov-append
echo "$?" >>/home/cerulean/pytest_exit_codes
