Developer Information
=====================

For better or worse, archelon is two projects in one.  To help with
that though, you can still run tests with just ``tox`` after having
tox installed, build just the docs with ``tox -e docs``, or just run
archelond with ``tox -e archelond``.

If you want to develop in a nice containerized environment so you
don't have to run ElasticSearch locally for example, there is also
docker-compose.  After running ``pip install docker-compose`` locally,
you should be able to run ``docker-compose up`` and ElasticSearch and
archelond will be running on port 8580 with the default credentials of
``admin`` and ``pass``.  Additionally, there is a secondary
docker-compose file for the client that is connected to the server.
This is a little more awkward because docker-compose isn't really
setup to run interactive containers.  To get this going, just run:
``docker-compose -f docker-client.yml run archelonc``.
