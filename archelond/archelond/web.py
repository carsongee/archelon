"""
Main entry point for flask application
"""
import logging
import os

from flask import Flask, jsonify, request, render_template
from flask.ext.assets import Environment
from passlib.apache import HtpasswdFile

from archelond.auth import requires_auth, generate_token
from archelond.data import MemoryData, ElasticData, ORDER_TYPES
from archelond.log import configure_logging

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
    app.config['ASSETS_DEBUG'] = True
    configure_logging(app)
    app.run(host=host, port=port)


def wsgi_app():
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
assets = Environment(app)


@app.route('/')
@requires_auth
def index(user):
    """
    Simple index view for documentation and navigation.
    """
    return render_template('index.html'), 200


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
        command = data.get('command')
        commands = data.get('commands')
        if not (command or commands):
            return jsonify({'error': 'Missing command(s) parameter'}), 422

        # Allow bulk posting to speedup imports with commands parameter
        if commands:
            results_list = []
            if not isinstance(commands, list):
                return jsonify({'error': 'Commands must be list'}), 422
            for command in commands:
                app.data.add(command, user, request.remote_addr)
                results_list.append(('', 201))
            return jsonify(results_list), 200
        if not isinstance(command, str):
            return jsonify({'error': 'Command must be a string'}), 422
        app.data.add(command, user, request.remote_addr)
        return '', 201
