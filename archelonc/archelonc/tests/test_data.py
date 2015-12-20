# -*- coding: utf-8 -*-
"""
Verify that the API calls work as expected
"""
from __future__ import absolute_import, print_function, unicode_literals
import os
import time
import unittest

import mock
from six.moves import range  # pylint: disable=redefined-builtin,import-error

from archelonc.data import (
    LocalHistory,
    WebHistory,
    ArcheloncConnectionException,
    ArcheloncAPIException,
)
from archelonc.tests.base import WebTest


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
            ["echo 'Hey you guys!☠'", "export FOO='bar☠'"]
        )

    def test_local_search_forward(self):
        """
        Verify searching and paging work and don't work respectively
        """
        self.assertEqual(
            self.history.search_forward('Hey'),
            ["echo 'Hey you guys!☠'"]
        )
        # Local has no paging, assert that any page other than 0 is empty
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
            ["export FOO='bar☠'", "echo 'Hey you guys!☠'"]
        )
        # Local has no paging, assert that any page other than 0 is empty
        self.assertEqual(
            self.history.search_reverse('Hey', 1),
            []
        )


class TestWebHistory(WebTest):
    """
    Battery for verifying the Web history class works as expected.
    """
    CONNECTION_METHODS = [
        ('add', ['arg']),
        ('bulk_add', [['blah', 'foo']]),
        ('all', [0]),
        ('delete', ['foo']),
        ('search_forward', ['foo', 0]),
        ('search_reverse', ['foo', 0])
    ]

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

    def test_connection_issues(self):
        """
        Test we raise when a connection is bad.
        """
        history = WebHistory('http://blah', 'asdf')
        for method in self.CONNECTION_METHODS:
            print('Running {0}'.format(method[0]))
            with self.assertRaises(ArcheloncConnectionException):
                getattr(history, method[0])(*method[1])

    def test_bad_responses(self):
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
        history.session.get.return_value = response_mock

        for method in self.CONNECTION_METHODS:
            print('Running {0}'.format(method[0]))
            if method[0] == 'delete':
                # For delete method, start with bad get, then make the
                # the get good with multiple returns, and then a bad delete
                with self.assertRaises(ArcheloncAPIException):
                    getattr(history, method[0])(*method[1])
                get_mock = mock.MagicMock()
                get_mock.status_code = 200
                get_mock.json.return_value = {
                    'commands': [{'id': 0}, {'id': 1}]
                }
                history.session.delete.return_value = response_mock
                history.session.get.return_value = get_mock
                with self.assertRaises(ValueError):
                    getattr(history, method[0])(*method[1])
                get_mock.json.return_value = {'commands': [{'id': 0}]}
            else:
                history.session.get.return_value = response_mock

            with self.assertRaises(ArcheloncAPIException):
                getattr(history, method[0])(*method[1])

    @WebTest.VCR.use_cassette()
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

    @WebTest.VCR.use_cassette()
    def test_bulk_add_successful(self):
        """
        Test adding a command successfully.
        """
        new_commands = [
            'TestUnique - TestBulkAdd1',
            'TestUnique - TestBulkAdd2'
        ]
        history = WebHistory(self.URL, self.TOKEN)
        # Do the nominal case, add a command and verify it is there.
        self.assertFalse(
            set(new_commands).issubset(set(self._get_all_commands()))
        )
        history.bulk_add(new_commands)
        # Sleep a second for processing
        time.sleep(1)
        self.assertTrue(
            set(new_commands).issubset(set(self._get_all_commands()))
        )

    @WebTest.VCR.use_cassette()
    def test_delete_successful(self):
        """
        Test deleting a command successfully.
        """
        new_command = 'TestUnique - TestDelete'
        history = WebHistory(self.URL, self.TOKEN)
        history.add(new_command)
        # Sleep a second for processing
        time.sleep(1)
        self.assertIn(new_command, self._get_all_commands())
        # Now command is there, nuke it and assert it is gone
        history.delete(new_command)
        time.sleep(1)
        # Use special cassette to avoid using our previous all cassette
        with self.VCR.use_cassette('test_delete_successful_post_delete'):
            self.assertNotIn(new_command, self._get_all_commands())

    @WebTest.VCR.use_cassette()
    def test_search_forward(self):
        """
        Verify searching and paging work.

        Caution: This will create a bunch of junk commands if
            the cassette isn't available
        """
        # Create more than a page worth of commands
        commands = []
        prefix = 'TestUnique - SearchForward'
        for suffix in range(100):
            commands.append('{}{}'.format(prefix, suffix))
        history = WebHistory(self.URL, self.TOKEN)
        history.bulk_add(commands)
        time.sleep(1)
        # Search for one specific command
        self.assertEqual(
            history.search_forward('{}98'.format(prefix)),
            ['{}98'.format(prefix)]
        )
        # Assert we have results on the next page
        self.assertTrue(
            len(history.search_forward(prefix, 1)) > 1
        )
        # I'm not asserting order, since for ES it is by score which
        # doesn't match to numeric/alphabetical

    @WebTest.VCR.use_cassette()
    def test_search_reverse(self):
        """
        Verify searching and paging work and don't work respectively in reverse

        Caution: This will create a bunch of junk commands if
            the cassette isn't available
        """
        # Create more than a page worth of commands
        commands = []
        prefix = 'TestUnique - SearchReverse'
        for suffix in range(100):
            commands.append('{}{}'.format(prefix, suffix))
        history = WebHistory(self.URL, self.TOKEN)
        history.bulk_add(commands)
        time.sleep(1)
        # Search for one specific command
        self.assertEqual(
            history.search_reverse('{}42'.format(prefix)),
            ['{}42'.format(prefix)]
        )
        # Assert we have results on the next page
        self.assertTrue(
            len(history.search_reverse(prefix, 1)) > 1
        )
        # I'm not asserting order, since for ES it is by score which
        # doesn't match to numeric/alphabetical
