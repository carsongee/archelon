Release Notes
-------------

Version 0.6.0
=============

- Converted to using tox with py.test as test runner.
- Documentation updates
- Added release notes page
- Added docker containers for client and server
- Python 3 compatibility for both client and server
- Switched to using flask-htpasswd for authentication
- All views protected with before_request
- Full test coverage in client and server
- Required at least ElasticSearch client 1.3.0 or greater


Version 0.5.0
=============

- Results paging in both client and server
- Added unit tests for server
- Documentation corrections
- Allowed for empty htpasswd file, but logged as critical
- Pylint fixes

Version 0.4.1
=============

- Corrected bad tar on pypi

Version 0.4.0
=============

- Delete command option
- Favicon and style improvements
- Sphinx/RTD docs

Version 0.3.1
=============

- Fixed an incorrectly cased javascript file include.

Version 0.3.0
=============

Archelon Client
~~~~~~~~~~~~~~~

- Optimized interface
- Menus added for sorting

Archelon Server
~~~~~~~~~~~~~~~

- New index page with searchable history

Version 0.2.1
=============

- PyPi version bump only

Version 0.2.0
=============

- Added default value for htpasswd path
- Removed elastic search sniffing

Version 0.1.0
=============

- Initial Release
