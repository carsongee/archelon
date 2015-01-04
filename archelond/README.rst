Archelon Daemon
===============

This is the Web server side of archelon.  Once it is all configured
and wired up to archelonc it can be used to store your shell history
from all your hosts.

It is a simple Flask app that is generally designed to be wired up to
an elasticsearch host to provide a nicely indexed shell history, and
should be deployable for free on heroku using an elasticsearch addon.


Installation and Configuration
------------------------------

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
should be able to go `http://localhost:8580/
<http://localhost:8580/>`_, login with the username and password you
created in your htpasswd file, and see a lovely Web interface for
searching and deleting your shell history similar to:

.. image:: _static/images/archelond_screen.png
  :align: center

.  It also provides a simple
button to reveal the token you need in archelonc to connect the two
together. To access the RESTful API side directly, you can check out
the sample commands by visiting
`http://localhost:8580/api/v1/history
<http://localhost:8580/api/v1/history>`_ or get your token for use
with archelonc `http://localhost:8580/api/v1/token
<http://localhost:8580/api/v1/token>`_.

Wiring Up to Elasticsearch
--------------------------

In order to have your history survive start ups we can use
Elasticsearch.  You can either install it locally, or grab it from an
add-on on Heroku.  Once you have the connection URL, we just need to
add a couple environment variables to point at the service and set the
storage provider class with something like:

.. code-block:: bash

  export ARCHELOND_ELASTICSEARCH_URL='http://localhost:9200'
  export ARCHELOND_ELASTICSEARCH_INDEX='history'
  export ARCHELOND_DATABASE='ElasticData'

The index can be changed as desired, but it is the index in
elasticsearch that will be used to store the history.

.. note::

  archelond with the ``ElasticData`` can support multiple users as it
  uses the user in the document type

Running in Production
---------------------

Running the ``archelond`` command is good for testing out, but to run
it in production you will want to run it through a proper wsgi
application server.  As an example, we've added uwsgi in the
requirements and it can be run in production with something like:

.. code-block:: bash

  uwsgi --http :8580 -w archelond.web:app

and then a Web server like nginx proxying over https in order to
further secure your shell history.

Running in Heroku
~~~~~~~~~~~~~~~~~

For heroku, it is very easy to setup the application part.  Just
create a requirements.txt file in the root of your repo with at least
one line:

.. code-block:: text

  archelond

Setup a Procfile with:

.. code-block:: text

  web: uwsgi uwsgi.ini

and a uwsgi.ini that looks something like:

.. code-block:: ini

  [uwsgi]
  http-socket = :$(PORT)
  master = true
  processes = 10
  die-on-term = true
  module = archelond.web:app
  memory-report = true

You also need to setup your secrets using ``heroku config:set``
commands.  The vars that need to be set minimally for an elasticsearch
version are:

.. code-block:: bash

  ARCHELOND_DATABASE="ElasticData"
  ARCHELOND_ELASTICSEARCH_INDEX="my_index"
  ARCHELOND_ELASTICSEARCH_URL="http://example.com/elastic_search"
  ARCHELOND_FLASK_SECRET="a_very_long_randomized_string"
  ARCHELOND_HTPASSWD="username:hashfromhtpasswd"
  ARCHELOND_HTPASSWD_PATH="htpasswd"

.. note::

  I had to also add ``-e
  git+https://github.com/elasticsearch/elasticsearch-py.git@master#egg=elasticsearch``
  to my requirements file because my elasticsearch server needed to
  specify https, username, and password. Currently the release
  version ``1.2.0`` didn't have that feature, but it is available in
  their master branch
