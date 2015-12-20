"""
Main entry point for flask application
"""
from __future__ import absolute_import, unicode_literals
import json
import logging
import os

from flask import Flask, jsonify, request, render_template, url_for, g
# pylint: disable=no-name-in-module, import-error
from flask.ext.assets import Environment
from flask.ext.htpasswd import HtPasswdAuth
from werkzeug.contrib.fixers import ProxyFix
from six import string_types

from archelond.data import MemoryData, ElasticData, ORDER_TYPES
from archelond.log import configure_logging
from archelond.util import jsonify_code

log = logging.getLogger('archelond')  # pylint: disable=invalid-name

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
    # Disabling check since both types are implementations of same base class
    # pylint: disable=redefined-variable-type

    # Setup the app
    new_app = Flask('archelond')
    # Get configuration from default or via environment variable
    if os.environ.get('ARCHELOND_CONF'):
        new_app.config.from_envvar('ARCHELOND_CONF')
    else:
        new_app.config.from_object('archelond.config')

    # Setup database
    if new_app.config['DATABASE_TYPE'] == 'MemoryData':
        new_app.data = MemoryData(new_app.config)
    elif new_app.config['DATABASE_TYPE'] == 'ElasticData':
        new_app.data = ElasticData(new_app.config)
    else:
        raise Exception('No valid database type is set')

    # Set up logging
    configure_logging(new_app)
    return new_app


# Setup flask application
app = wsgi_app()  # pylint: disable=invalid-name
assets = Environment(app)  # pylint: disable=invalid-name
htpasswd = HtPasswdAuth(app)  # pylint: disable=invalid-name
# Add proxy fixer
app.wsgi_app = ProxyFix(app.wsgi_app)


@app.route('/')
def index():
    """
    Simple index view for documentation and navigation.
    """
    return render_template('index.html', user=g.user), 200


@app.route('{}token'.format(V1_ROOT), methods=['GET'])
def token():
    """
    Return the user token for API auth that is based off the
    flask secret and user password
    """
    return jsonify({'token': htpasswd.generate_token(g.user)})


@app.route('{}history'.format(V1_ROOT), methods=['GET', 'POST'])
def history():
    """
    POST=Add entry
    GET=Get entries with query
    """
    # We have a lot of logic here since we are doing query string
    # handling, so let pylint know that is ok.
    # pylint: disable=too-many-return-statements,too-many-branches
    if request.method == 'GET':
        query = request.args.get('q')
        order = request.args.get('o')
        page = int(request.args.get('p', 0))

        order_type = None
        if order:
            if order not in ORDER_TYPES:
                return jsonify_code(
                    {'error': 'Order specified is not an option'},
                    422
                )
            else:
                order_type = order

        if query:
            results = app.data.filter(
                query, order_type, g.user, request.remote_addr, page=page
            )
        else:
            results = app.data.all(
                order_type, g.user, request.remote_addr, page=page
            )
        return jsonify({'commands': results})

    if request.method == 'POST':
        # Accept json or form type
        from_form = True
        if request.json:
            data = request.json
            from_form = False
        else:
            data = request.form
        command = data.get('command')
        commands = data.get('commands')
        if not (command or commands):
            return jsonify_code({'error': 'Missing command(s) parameter'}, 422)

        # Allow bulk posting to speedup imports with commands parameter
        if commands:
            if from_form:
                commands = json.loads(commands)
            results_list = []
            if not isinstance(commands, list):
                return jsonify_code({'error': 'Commands must be list'}, 422)
            for command in commands:
                cmd_id = app.data.add(command, g.user, request.remote_addr)
                results_list.append(
                    {
                        'response': '',
                        'status_code': 201,
                        'headers': {
                            'location': url_for('history_item', cmd_id=cmd_id)
                        },
                    }
                )
            return jsonify({'responses': results_list})
        if not isinstance(command, string_types):
            return jsonify_code({'error': 'Command must be a string'}, 422)

        cmd_id = app.data.add(command, g.user, request.remote_addr)
        return '', 201, {'location': url_for('history_item', cmd_id=cmd_id)}
    else:  # pragma: no cover
        log.critical('Unsupported method used')
        raise Exception('Unsupported http method used')


@app.route('{}history/<cmd_id>'.format(V1_ROOT),
           methods=['GET', 'PUT', 'DELETE'])
def history_item(cmd_id):
    """Actions for individual command history items.

    Updates, gets, or deletes a command from the active data store.

    PUT: Takes a payload in either form or JSON request, and runs the
    add routine by passing the dictinoary minus ``command``,
    ``username``, and ``host`` as kwargs to the data stores ``add``
    routine.
    """
    # We have to handle several methods, which requires branches and
    # extra returns.  Until/when we switch to pluggable views, let
    # pylint know that is ok for this view.
    # pylint: disable=too-many-return-statements,too-many-branches
    if request.method == 'GET':
        log.debug('Retrieving %s for %s', cmd_id, g.user)
        try:
            cmd = app.data.get(cmd_id, g.user, request.remote_addr)
        except KeyError:
            return jsonify_code({'error': 'No such history item'}, 404)
        return jsonify(cmd)

    if request.method == 'PUT':
        # This will only update kwargs since we
        # have a deduplicated data structure by command.
        log.debug('Updating %s for %s', cmd_id, g.user)
        try:
            cmd = app.data.get(cmd_id, g.user, request.remote_addr)
        except KeyError:
            return jsonify_code({'error': 'No such history item'}, 404)
        from_form = True
        if request.json:
            data = request.json
            from_form = False
        else:
            data = request.form
        if not data:
            return jsonify_code(
                {'error': 'Data is required, received empty PUT'},
                422
            )
        put_command = data.get('payload')
        if not put_command:
            return jsonify_code(
                {'error': 'Request must contain ``payload`` parameter'},
                422
            )
        if from_form:
            put_command = json.loads(put_command)

        # Make sure we don't let them overwrite server side params
        try:
            del put_command['command']
            del put_command['username']
            del put_command['host']
        except KeyError:
            pass
        app.data.add(
            cmd['command'], g.user, request.remote_addr, **put_command
        )
        return '', 204

    if request.method == 'DELETE':
        log.debug('Deleting %s for %s', cmd_id, g.user)
        try:
            app.data.delete(cmd_id, g.user, request.remote_addr)
        except KeyError:
            return jsonify_code({'error': 'No such history item'}, 404)
        return jsonify(message='success')
    else:  # pragma: no cover
        log.critical('Unsupported method used')
        raise Exception('Unsupported http method used')
