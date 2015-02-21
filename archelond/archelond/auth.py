"""
Decorators for authentication via basic auth or tokens
"""
from functools import wraps
import hashlib
import logging

from flask import request, Response, current_app
from itsdangerous import JSONWebSignatureSerializer as Serializer
from itsdangerous import BadSignature

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


def check_basic_auth(username, password):
    """
    This function is called to check if a username /
    password combination is valid via the htpasswd file.
    """
    valid = current_app.config['users'].check_password(username, password)
    if not valid:
        log.warn('Invalid login from %s', username)
        valid = False
    return (
        valid,
        username
    )


def get_signature():
    """
    Setup crypto sig.
    """
    return Serializer(current_app.config['FLASK_SECRET'])


def get_hashhash(username):
    """
    Generate a digest of the htpasswd hash
    """
    return hashlib.sha256(
        current_app.config['users'].find(username)
    ).hexdigest()


def generate_token(username):
    """
    assumes user exists in htpasswd file.

    Return the token for the given user by signing a token of
    the username and a hash of the htpasswd string.
    """
    serializer = get_signature()
    return serializer.dumps(
        {
            'username': username,
            'hashhash': get_hashhash(username)
        }
    )


def check_token_auth(token):
    """
    Check to see who this is and if their token gets
    them into the system.
    """
    users = current_app.config['users']
    serializer = get_signature()

    try:
        data = serializer.loads(token)
    except BadSignature:
        log.warn('Received bad token signature')
        return False, None
    if data['username'] not in users.users():
        log.warn(
            'Token auth signed message, but invalid user %s',
            data['username']
        )
        return False, None
    if data['hashhash'] != get_hashhash(data['username']):
        log.warn(
            'Token and password do not match, %s needs to regenerate token',
            data['username']
        )
        return False, None
    return True, data['username']


def auth_failed():
    """
    Sends a 401 response that enables basic auth
    """
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials',
        401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def requires_auth(func):
    """
    Decorator function with basic and token authentication handler
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        """
        Actual wrapper to run the auth checks.
        """
        basic_auth = request.authorization
        is_valid = False
        if basic_auth:
            is_valid, user = check_basic_auth(
                basic_auth.username, basic_auth.password
            )
        else:
            token = request.headers.get('Authorization', None)
            param_token = request.args.get('access_token')
            if token or param_token:
                if token:
                    # slice the 'token ' piece of the header (following
                    # github style):
                    token = token[6:]
                else:
                    # Grab it from query dict instead
                    token = param_token
                log.debug('Received token: %s', token)

                is_valid, user = check_token_auth(token)

        if not is_valid:
            return auth_failed()
        kwargs['user'] = user
        return func(*args, **kwargs)
    return decorated
