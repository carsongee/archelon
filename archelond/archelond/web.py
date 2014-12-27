"""
Main entry point for flask application
"""
import logging
import os

from flask import Flask, jsonify, request
from passlib.apache import HtpasswdFile

from archelond.data import MemoryData, ElasticData, ORDER_TYPES
from archelond.log import configure_logging
from archelond.auth import requires_auth, generate_token

log = logging.getLogger('archelond')

V1_ROOT = '/api/v1/'


def run_server():
    """
    If started from command line, rebuild object in
    debug mode and run directly
    """
    host = os.environ.get('ARCHELOND_HOST', 'localhost')
    port = int(os.environ.get('ARCHELOND_PORT', '8580'))

    app.debug = True
    log.critical(
        'Running in debug mode. Do not run this way in production'
    )
    app.config['LOG_LEVEL'] = 'DEBUG'
    configure_logging(app)
    app.run(host=host, port=port)


def wsgi_app(debug=False):
    """
    Start flask application runtime
    """
    # Setup the app
    app = Flask('archelond')
    # Get configuration from default or via environment variable
    if os.environ.get('ARCHELOND_CONF'):
        app.config.from_envvar('ARCHELOND_CONF')
    else:
        app.config.from_object('archelond.config')

    # Load up user database
    app.config['users'] = HtpasswdFile(app.config['HTPASSWD_PATH'])

    # Setup database
    if app.config['DATABASE_TYPE'] == 'MemoryData':
        app.data = MemoryData(app.config)
    elif app.config['DATABASE_TYPE'] == 'ElasticData':
        app.data = ElasticData(app.config)

    # Set up logging
    configure_logging(app)

    return app


# Setup flask application
app = wsgi_app()


@app.route('/')
@requires_auth
def index(user):
    """
    Simple index view for documentation and navigation.
    """
    return 'Archelond Ready for Eating Shell History'


@app.route('{}token'.format(V1_ROOT), methods=['GET'])
@requires_auth
def token(user):
    """
    Return the user token for API auth that is based off the
    flask secret and user password
    """
    return jsonify({'token': generate_token(user)})


@app.route('{}history'.format(V1_ROOT), methods=['GET', 'POST'])
@requires_auth
def history(user):
    """
    POST=Add entry
    GET=Get entries with query
    """
    if request.method == 'GET':
        query = request.args.get('q')
        order = request.args.get('o')

        order_type = None
        if order:
            if order not in ORDER_TYPES:
                return jsonify(
                    {'error': 'Order specified is not an option'}
                ), 422
            else:
                order_type = order

        if query:
            results = app.data.filter(
                query, order_type, user, request.remote_addr
            )
        else:
            results = app.data.all(order_type, user, request.remote_addr)
        return jsonify({'commands': results})

    if request.method == 'POST':
        # Accept json or form type
        if request.json:
            data = request.json
        else:
            data = request.form
        if not data.get('command'):
            return jsonify({'error': 'Missing command parameter'}), 422

        app.data.add(data['command'], user, request.remote_addr)
        return '', 201
