###########
Change Log
###########

All notable changes to this project will be documented in this file.
This project adheres to `Semantic Versioning <http://semver.org/>`_.

0.3.6
*****

Added
-----

* Support for redirecting scheduler/system output
* Path.remove() method

0.3.5
*****

Fixed
-----

* Detect a closed SSH socket and auto-reconnect.

0.3.4
*****

Fixed
-----

* Directory permissions when using mkdir(). This is a security issue, and you
  should upgrade as soon as possible.

Added
-----

* Equality comparison of FileSystems and Terminals, which makes equality
  comparison for Paths work better as well.
* Add `interval` parameter to scheduler.wait(), and improve default behaviour.

0.3.3
*****

Fixed
-----

* Copy silently ignored missing file, now raises FileNotFoundError

Added
-----

* FileSystem.root() to get a Path for the root
* Path.__repr__() for better debugging output

0.3.2
*****

Fixed
-----

* Various small things

Added
-----

* Support for Slurm 18.08 (worked already, now also part of the tests)
* Add command prefix for schedulers
* Add support for WebDAV

0.3.1
*****

Fixed
-----

* Extraneous slashes in paths
* Properly handle errors on Slurm submission
* Leftover print statement in Path.walk


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
