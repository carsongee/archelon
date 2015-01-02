Archelon Client
===============

Curses based application for command history that can be wired up to a
Web server (archelond) for shared shell history across multiple hosts.

Installation
------------

.. code-block:: bash

  pip install archelonc

Once that is setup you can try it out by running ``. archelon`` this
uses your existing shell history to let you try out the client.  To
make this work more like the bash reverse history search via ``C-r`` I
recommend adding:

.. code-block:: bash

  bind '"\033a":". archelon\n"'

this will launch the reverse search of archelon via Alt-A.

Web Enabled History
-------------------

From here you can use archelon as is, but the cool part really start
when you install archelond and wire the client up to use that project
for shared and indexed shell history.  To configure the client side
after you have setup the server, you just need to add two environment
variables to the mix.

- ``ARCHELON_URL`` - Web URL to your archelond installation
- ``ARCHELON_TOKEN`` - The API token for your user.  You can get this
  by going to `https://your.archelond.domain/api/v1/token
  <https://your.archelond.domain/api/v1/token>`_ and logging in with
  the username and password you've created.

Add those to ``.bashrc``, ``.profile``, or whichever shell startup you
are using and it will be hooked up to the Web server.  You can verify
this and populate your Web history by running the ``archelon_import``
command which will import your current computers history.

Keyboard Shortcuts
------------------

Within the client curses application, there are a few handy keyboard shortcuts.

:Alt-o:

    This presses the Ok button and runs whatever command is in the
    ``command`` field

:Alt-c:

    This presses the cancel button and exits out of the application
    without running a command. ``Ctrl-C`` also works, but currently
    has a nasty exception message.

:Ctrl-x:

    This brings up the menu for doing things like changing the order of the
	search results.

Within Menus
~~~~~~~~~~~~

Within the menu there are also keyboard shortcuts.  And are executed emacs style, i.e. ``Ctrl-x Ctrl-f`` to set sorting order to oldest->newest.  So far those are:

:Ctrl-F:

    Sort results from oldest to newest

:Ctrl-R:

    Default order. Sort results from newest to oldest.
