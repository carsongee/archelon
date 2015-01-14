"""
Verify the Web views
"""
import base64
import json
import os
import unittest

import mock
from passlib.apache import HtpasswdFile

from archelond.data import MemoryData
import archelond.web


class TestWeb(unittest.TestCase):
    """
    Verify the views and API
    """
    # pylint: disable=no-member

    USER = 'foo'
    PASS = 'bar'
    DEFAULT_COMMAND = 'cheese it'

    def setUp(self):
        """
        Start up an app instance with an memory data
        store for use by each test
        """
        self.old_conf = os.environ.get('ARCHELOND_CONF')
        os.environ['ARCHELOND_CONF'] = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'config', 'basic.py'
        )
        # For URLs to work and such we have to initialize the
        # existing app instead of just rebuilding with our test
        # configuration.
        app = archelond.web.app
        app.config.from_envvar('ARCHELOND_CONF')
        app.data = MemoryData(app.config)
        app.config['users'] = HtpasswdFile(app.config['HTPASSWD_PATH'])

        self.client = archelond.web.app.test_client()

    def _authed(self, url, method='GET', **kwargs):
        """
        Perform test client actions with auth headers wrapped in
        """
        if method == 'POST':
            caller = self.client.post
        elif method == 'PUT':
            caller = self.client.put
        elif method == 'DELETE':
            caller = self.client.delete
        else:
            caller = self.client.get

        return caller(url, headers={
            'Authorization': 'Basic {0}'.format(base64.b64encode(
                '{0}:{1}'.format(self.USER, self.PASS)
            ))
        }, **kwargs)

    def _create_command(self, command=DEFAULT_COMMAND):
        """
        Create and return the ID of a command.
        """
        response = self._authed(
            '/api/v1/history', method='POST',
            data={'command': command}
        )
        return response.headers['location'].split('/')[-1]

    def tearDown(self):  # pragma: no cover
        """
        Restore previous config variable
        """
        if self.old_conf:
            os.environ['ARCHELOND_CONF'] = self.old_conf
        else:
            del os.environ['ARCHELOND_CONF']

    def test_invalid_database_type(self):
        """
        See how we handle bad database types
        """
        old_class = os.environ.get('ARCHELOND_TEST_DATABASE')
        os.environ['ARCHELOND_TEST_DATABASE'] = 'NotADatabaseClass'
        with self.assertRaisesRegexp(
            Exception, 'No valid database type is set'
        ):
            archelond.web.wsgi_app()

        if old_class:  # pragma: no cover
            os.environ['ARCHELOND_TEST_DATABASE'] = old_class
        else:
            del os.environ['ARCHELOND_TEST_DATABASE']

    @mock.patch('archelond.web.app')
    def test_dev_mode(self, mock_app):
        """
        Launch our app in developer mode, and verify it is setup right
        """
        mock_app.config = {'LOG_LEVEL': None}
        archelond.web.run_server()
        self.assertTrue(mock_app.config['LOG_LEVEL'], 'DEBUG')
        self.assertTrue(mock_app.config['ASSETS_DEBUG'], True)
        mock_app.run.assert_called_with(host='localhost', port=8580)

    def test_index(self):
        """
        Verify index view
        """
        # Check that it is protected
        response = self.client.get('/')
        self.assertEqual(response.status_code, 401)

        # Auth
        response = self._authed('/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Archelon is Hungry' in response.data)

    def test_token_get(self):
        """
        Verify that we are getting a token when authed
        """
        response = self.client.get('/api/v1/token')
        self.assertEqual(response.status_code, 401)

        # Get an actual token
        response = self._authed('/api/v1/token')
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.data)
        # Grab token, will raise key error if it wasn't returned
        token = payload['token']

        # Use token to grab the token and validate they are equal
        response = self.client.get(
            '/api/v1/token',
            headers={'Authorization': 'token {}'.format(token)}
        )
        self.assertEqual(token, json.loads(response.data)['token'])

    def test_history_get(self):
        """
        Validate the history view read verbs
        """
        url = '/api/v1/history'

        # Verify it is protected
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # Verify get of all
        response = self._authed(url)
        self.assertEqual(response.status_code, 200)
        commands = json.loads(response.data)['commands']
        command_list = [x['command'] for x in commands]
        counter = 0
        for command in MemoryData.INITIAL_DATA:
            self.assertEqual(command_list[counter], command)
            counter += 1

        # Grab with reverse order to sort
        response = self._authed('{}?o=r'.format(url))
        self.assertEqual(response.status_code, 200)
        commands = json.loads(response.data)['commands']
        command_list = [x['command'] for x in commands]
        counter = len(MemoryData.INITIAL_DATA) - 1
        for command in MemoryData.INITIAL_DATA:
            self.assertEqual(command_list[counter], command)
            counter -= 1

        # Test out filtering
        response = self._authed('{}?q=cpuinfo'.format(url))
        self.assertEqual(response.status_code, 200)
        commands = json.loads(response.data)['commands']
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0]['command'], 'cat /proc/cpuinfo')

        # Test invalid order
        response = self._authed('{}?o=foo'.format(url))
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            json.loads(response.data)['error'],
            'Order specified is not an option'
        )

    def test_history_single_post(self):
        """
        Test adding history items via API
        """
        url = '/api/v1/history'

        # Verify it is protected
        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

        # Post form command
        response = self._authed(url, method='POST', data={'command': 'who'})
        self.assertEqual(201, response.status_code)

        # Post json command
        response = self._authed(
            url, method='POST', content_type='application/json',
            data=json.dumps({'command': 'who'})
        )

        # Verify that the command is in the store
        response = self._authed('{}?q=who'.format(url))
        commands = json.loads(response.data)['commands']
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0]['command'], 'who')

        # Send no command
        response = self._authed(url, method='POST', data={'fluffy': 'bunnies'})
        self.assertEqual(422, response.status_code)
        self.assertEqual(
            'Missing command(s) parameter',
            json.loads(response.data)['error']
        )

        # Send command that isn't a string
        response = self._authed(
            url, method='POST',
            data=json.dumps({'command': True}),
            content_type='application/json'
        )
        self.assertEqual(422, response.status_code)

    def test_multi_post(self):
        """
        Verify bulk posting via json or form
        """
        url = '/api/v1/history'

        commands = ['stuff', 'things', 'blah', 'ls']
        response = self._authed(
            url, method='POST', data={'commands': json.dumps(commands)}
        )
        self.assertEqual(200, response.status_code)
        responses = json.loads(response.data)['responses']
        for response in responses:
            self.assertEqual(201, response['status_code'])

        # Post via json just to make sure we work both ways
        response = self._authed(
            url, method='POST', content_type='application/json',
            data=json.dumps({'commands': commands})
        )
        self.assertEqual(200, response.status_code)
        responses = json.loads(response.data)['responses']
        for response in responses:
            self.assertEqual(201, response['status_code'])

        # Post a dictionary instead of a list
        response = self._authed(
            url, method='POST', content_type='application/json',
            data=json.dumps({'commands': {'stuff': None, 'things': None}})
        )
        self.assertEqual(422, response.status_code)
        self.assertEqual(
            json.loads(response.data)['error'],
            'Commands must be list'
        )

    def test_history_item_get(self):
        """
        Grab a single history item by id
        """
        base_url = '/api/v1/history/'
        # Post a single item to work with
        command_id = self._create_command()

        # Validate auth is required
        response = self.client.get('{}{}'.format(base_url, command_id))
        self.assertEqual(401, response.status_code)

        # Verify we can get the command with auth
        response = self._authed('{}{}'.format(base_url, command_id))
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            self.DEFAULT_COMMAND,
            json.loads(response.data)['command']
        )

        # Test against invalid command id
        response = self._authed('{}12345'.format(base_url))
        self.assertEqual(404, response.status_code)

    def test_history_item_put(self):
        """
        Verify PUT method
        """
        base_url = '/api/v1/history/'
        # Try and update non-existent command
        response = self._authed('{}12345'.format(base_url), method='PUT')
        self.assertEqual(404, response.status_code)
        self.assertEqual(
            'No such history item',
            json.loads(response.data)['error']
        )
        # Post a single item to work with
        command_id = self._create_command()

        # Try and update without sending any payload
        response = self._authed(
            '{}{}'.format(base_url, command_id),
            method='PUT',
            content_type='application/json',
            data=json.dumps({})
        )
        self.assertEqual(422, response.status_code)

        # Add data, but no payload key
        response = self._authed(
            '{}{}'.format(base_url, command_id),
            method='PUT',
            content_type='application/json',
            data=json.dumps({'foo': 'bar'})
        )
        self.assertEqual(422, response.status_code)

        # Now update it with PUT and verify the extra sauce
        response = self._authed(
            '{}{}'.format(base_url, command_id),
            method='PUT',
            data={'payload': json.dumps({'pumpkins': True})}
        )
        self.assertEqual(204, response.status_code)
        # Now check that pumpkins are there
        response = self._authed('{}{}'.format(base_url, command_id))
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            json.loads(response.data)['meta']['pumpkins']
        )

        # Make sure our PUT can't do bad things
        response = self._authed(
            '{}{}'.format(base_url, command_id),
            method='PUT',
            content_type='application/json',
            data=json.dumps({
                'payload': {
                    'command': 'enigma', 'username': 'steveo', 'host': 'enigma'
                }
            })
        )
        self.assertEqual(204, response.status_code)
        response = self._authed('{}{}'.format(base_url, command_id))
        self.assertFalse('enigma' in json.loads(response.data).values())

    def test_delete_item(self):
        """
        Test out deleting an item
        """
        base_url = '/api/v1/history/'

        # Delete non-existent command
        response = self._authed('{}12345'.format(base_url), method='DELETE')
        self.assertEqual(404, response.status_code)

        # Create a command to delete
        command_id = self._create_command()
        response = self._authed(
            '{}{}'.format(base_url, command_id),
            method='DELETE'
        )
        self.assertEqual(200, response.status_code)

        # Try and find it
        response = self._authed(
            '/api/v1/history?q={}'.format(self.DEFAULT_COMMAND)
        )
        self.assertEqual(0, len(json.loads(response.data)['commands']))
