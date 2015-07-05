"""
Verify that the API calls work as expected
"""
from __future__ import absolute_import, print_function, unicode_literals
import os
import time
import unittest

import mock
import vcr

from archelonc.data import (
    LocalHistory, WebHistory, ArcheloncConnectionException
)


class TestLocalHistory(unittest.TestCase):
    """
    Battery of tests for verifying the data classes
    """
    def setUp(self):
        """
        Initialize a LocalHistory class with test data.
        """
        with mock.patch('os.path.expanduser') as expand_hijack:
            expand_hijack.return_value = os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                "testdata",
                "history"
            )
            self.history = LocalHistory()

    def test_local_init(self):
        """
        Verify data is as expected from the history test file.
        """
        self.assertEqual(
            self.history.data,
            ["echo 'Hey you guys!'", "export FOO='bar'"]
        )

    def test_local_search_forward(self):
        """
        Verify searching and paging work and don't work respectively
        """
        self.assertEqual(
            self.history.search_forward('Hey'),
            ["echo 'Hey you guys!'"]
        )
        # Local has not paging, assert that any page other than 0 is empty
        self.assertEqual(
            self.history.search_forward('Hey', 1),
            []
        )

    def test_local_search_reverse(self):
        """
        Verify searching and paging work and don't work respectively in reverse
        """
        self.assertEqual(
            self.history.search_reverse('e'),
            ["export FOO='bar'", "echo 'Hey you guys!'"]
        )
        # Local has not paging, assert that any page other than 0 is empty
        self.assertEqual(
            self.history.search_reverse('Hey', 1),
            []
        )


class TestWebHistory(unittest.TestCase):
    """
    Battery for verifying the Web history class works as expected.
    """
    URL = os.environ.get('ARCHELON_TEST_URL', 'http://localhost:8580')
    TOKEN = os.environ.get('ARCHELON_TEST_TOKEN', '1234')
    VCR = vcr.VCR(
        serializer='yaml',
        cassette_library_dir='archelonc/tests/testdata/cassettes/test_data/',
        record_mode='once',
        match_on=['method', 'scheme', 'path', 'query', 'body'],
    )

    def _get_all_commands(self):
        """
        Grab all of the commands available.

        Returns:
            list: all commands available at the test
                url.
        """
        history = WebHistory(self.URL, self.TOKEN)
        commands = []
        page = 0
        new_commands = history.all(page)
        while len(new_commands) > 0:
            commands.extend(new_commands)
            if(
                    len(new_commands) == 1 and
                    'Error in API Call' in new_commands[0]
            ):
                raise Exception('API call failed unexpectedly.')
            page += 1
            new_commands = history.all(page)
        return commands

    def test_init(self):
        """
        Validate the constructor.
        """
        url = 'https://test'
        token = 'foo'
        web_history = WebHistory(url, token)

        self.assertEqual(
            web_history.url,
            '{url}{endpoint}'.format(url=url, endpoint=WebHistory.SEARCH_URL)
        )
        self.assertEqual(
            web_history.session.headers['Authorization'],
            'token {}'.format(token)
        )

    @VCR.use_cassette()
    def test_add_successful(self):
        """
        Test adding a command successfully.
        """
        new_command = 'TestUnique - TestAdd'
        history = WebHistory(self.URL, self.TOKEN)
        # Do the nominal case, add a command and verify it is there.
        self.assertNotIn(new_command, self._get_all_commands())
        history.add(new_command)
        # Sleep a second for processing
        time.sleep(1)
        self.assertIn(new_command, self._get_all_commands())

    def test_add_connection_issue(self):
        """
        Test we raise when a connection is bad.
        """
        history = WebHistory('http://blah', 'asdf')
        with self.assertRaises(ArcheloncConnectionException):
            history.add('nope')

    def test_add_bad_response(self):
        """
        Test we raise when a connection is bad.
        """
        json_return = 'foobar'
        status_code = 422
        history = WebHistory('http://blah', 'asdf')
        response_mock = mock.MagicMock()
        response_mock.status_code = status_code
        response_mock.json.return_value = json_return
        history.session = mock.MagicMock()
        history.session.post.return_value = response_mock
        failed_add = history.add('blah')
        self.assertEqual(
            failed_add,
            (False, (json_return, status_code))
        )
