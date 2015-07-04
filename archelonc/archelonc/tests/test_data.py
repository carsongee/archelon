"""
Verify that the API calls work as expected
"""
from __future__ import absolute_import, unicode_literals
import os
import unittest

import mock

from archelonc.data import LocalHistory


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
