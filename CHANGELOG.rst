###########
Change Log
###########

All notable changes to this project will be documented in this file.
This project adheres to `Semantic Versioning <http://semver.org/>`_.

0.3.0
*****

Added
-----

* New copy_permissions option to copy()
* New callback option to copy()
* New Path.walk() method

Fixed
-----

* Add missing EntryType and Permission classes to API
* SFTP-to-SFTP copy deadlock


0.2.0
*****

Added
-----

* Path.write_text()
* Scheduler.submit_job() is now Scheduler.submit()
* Scheduler.wait()

Fixed
-----

* Bugs in copy()
* Documentation for JobDescription


0.1.0
*****

Initial release
