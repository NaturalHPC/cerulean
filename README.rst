.. image:: https://readthedocs.org/projects/cerulean/badge/?version=master
    :target: https://cerulean.readthedocs.io/en/latest/?badge=master
    :alt: Documentation Build Status

.. image:: https://api.travis-ci.org/MD-Studio/cerulean.svg?branch=master
    :target: https://travis-ci.org/MD-Studio/cerulean
    :alt: Build Status

.. image:: https://api.codacy.com/project/badge/Grade/d4e477891b6d452589c94e2164cf6d7e
    :target: https://www.codacy.com/app/LourensVeen/cerulean
    :alt: Codacy Grade

.. image:: https://api.codacy.com/project/badge/Coverage/d4e477891b6d452589c94e2164cf6d7e
    :target: https://www.codacy.com/app/LourensVeen/cerulean
    :alt: Code Coverage

.. image:: https://requires.io/github/MD-Studio/cerulean/requirements.svg?branch=master
    :target: https://requires.io/github/MD-Studio/cerulean/requirements/?branch=master
    :alt: Requirements Status

################################################################################
Cerulean
################################################################################

Cerulean is a Python 3 library for talking to HPC clusters and supercomputers.
It lets you copy files between local and SFTP filesystems using a
``pathlib``-like API, it lets you start processes locally and remotely via SSH,
and it lets you submit jobs to schedulers such as Slurm and Torque/PBS.

Documentation and Help
**********************

Cerulean can be installed as usual using pip:

`pip install cerulean`

Instructions on how to use Cerulean can be found in `the Cerulean documentation
<https://cerulean.readthedocs.io>`_.

Code of Conduct
---------------

Before we get to asking questions and reporting bugs, we'd like to point out
that this project is governed by a code of conduct, as described in
CODE_OF_CONDUCT.rst, and we expect you to adhere to it. Please be nice to your
fellow humans.

Questions
---------

If you have a question that the documentation does not answer for you, then you
have found a bug in the documentation. We'd love to fix it, but we need a bit of
help from you to do so. Please do the following:

#. use the search functionality `here
   <https://github.com/MD-Studio/cerulean/issues>`__
   to see if someone already filed the same issue;
#. if your issue search did not yield any relevant results, make a new
   issue;
#. apply the "Question" label; apply other labels when relevant.

We'll answer your question, and improve the documentation where necessary.
Thanks!

Bugs
----

Like most software, Cerulean is made by humans, and we make mistakes. If you
think you've found a bug in Cerulean, please let us know! Reporting bugs goes as
follows.

#. Use the search functionality `here
   <https://github.com/yatiml/yatiml/issues>`_
   to see if someone already filed the same issue.
#. If your issue search did not yield any relevant results, make a new issue.
   Please explain:
   - what you were trying to achieve,
   - what you did to make that happen,
   - what you expected the result to be,
   - what happened instead.
   It really helps to have the actual code for a simple example that
   demonstrates the issue, but excerpts and error messages and a
   description are welcome too.
#. Finally, apply any relevant labels to the newly created issue.

With that, we should be able to fix the problem, but we may ask for some more
information if we can't figure it out right away.

Development
-----------

More information for Cerulean developers may be found in `the Cerulean
documentation <https://cerulean.readthedocs.io>`_.

License
*******

Copyright (c) 2018, The Netherlands eScience Center and VU University Amsterdam

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
