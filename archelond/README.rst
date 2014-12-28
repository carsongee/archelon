Archelon Daemon
---------------

This is the Web server side of archelon.  Once it is all configured
and wired up to archelonc it can be used to store your shell history
from all your hosts.

It is a simple Flask app that is generally designed to be wired up to
an elasticsearch host to provide a nicely indexed shell history, and
should be deployable for free on heroku using an elasticsearch addon.


Installation and Configuration
==============================

.. code-block:: bash

  pip install archelond

Security is obviously important for shell history, and to setup
authentication we use basic authentication using apache htpasswd files
as the user database.  To add one for yourself and configure archelond
to use it, run something like:

.. code-block:: bash

  htpasswd -c ~/.htpasswd username
  export HTPASSWD_PATH=~/.htpasswd

After that minimal setup we can try things out with just a simple command of:

.. code-block:: bash

  archelond

Which will fire up the debug/development server using an in memory
bash history data store that is very forgetful.  Once it is up, you
should be able to go `http://localhost:8580/ <http://localhost:8580/>`_,
login with the username and password you created in your htpasswd
file, and see a lovely welcome page.  To check out the sample commands
you can go to `http://localhost:8580/api/v1/history
<http://localhost:8580/api/v1/history>`_ or get your token for use with
archelonc `http://localhost:8580/api/v1/token <http://localhost:8580/api/v1/token>`_.

Wiring Up to Elasticsearch
==========================

In order to have your history survive start ups we can use
Elasticsearch.  You can either install it locally, or grab it from an
add-on on Heroku.  Once you have the connection URL, we just need to
add a couple environment variables to point at the service and set the
storage provider class with something like:

.. code-block:: bash

  export ARCHELOND_ELASTICSEARCH_URL='http://localhost:9200'
  export ARCHELOND_ELASTICSEARCH_INDEX='history'
  export ARCHELOND_DATABASE='ElasticData'

The index can be changed, but is the index in elasticsearch that will
be used to store the history.

.. note::

  archelond with the ``ElasticData`` can support multiple users as it
  uses the user in the document type

Running in Production
=====================

Running the ``archelond`` is good for testing out, but to run it in
production you will want to run it through a proper wsgi application
server.  As an example, we've added uwsgi in the requirements and it
can be run in production with something like:

.. code-block:: bash
  uwsgi --http :8580 -w archelond.web:app

and then a Web server like nginx proxying over https in order to
further secure your shell history.  You could also put that into a
Heroku application Procfile.
