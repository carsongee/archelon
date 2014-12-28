Archelon Client
---------------

Curses based application for command history that can be wired up to a
Web server (archelond) for shared shell history across multiple hosts.

Installation
============

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
===================

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
