#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

setup(
    name='cerulean',
    version='0.3.8.dev',
    description="A Python 3 library for talking to HPC clusters and supercomputers",
    long_description=readme + '\n\n',
    author="Lourens Veen",
    author_email='l.veen@esciencecenter.nl',
    url='https://github.com/MD-Studio/cerulean',
    packages=[
        'cerulean',
    ],
    package_dir={'cerulean':
                 'cerulean'},
    include_package_data=True,
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='cerulean',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    test_suite='tests',
    install_requires=[
        'defusedxml',
        'paramiko',
        'requests',
        'types-requests',
    ],
    setup_requires=[
        # dependency for `python setup.py test`
        'pytest-runner',
        # dependencies for `python setup.py build_sphinx`
        'docutils',
        'sphinx',
        'sphinx-rtd-theme',
        'recommonmark'
    ],
    tests_require=[
        'coverage',
        'docker-compose',
        'docker[ssh]<7',
        'pytest>=3.6.0',
        'pytest-cov',
        'pycodestyle',
        'sh',
    ],
    extras_require={
        'dev':  ['prospector[with_pyroma]', 'yapf', 'isort'],
    }
)
