"""
Test out our authentication module.
"""
import os
import unittest

from archelond.web import wsgi_app
from archelond.auth import (
    check_basic_auth
)


class TestAuth(unittest.TestCase):
    """
    Verify each piece of our authentication module using
    the htpasswd in tests/config/
    """
    def setUp(self):
        """
        Change the app.config and build the app object
        """

        os.environ['ARCHELOND_CONF'] = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'config', 'basic.py'
        )
        self.app = wsgi_app()

    def test_check_basic_auth(self):
        """
        Validate a test user works with the correct password
        and doesn't with a bad one
        """
        with self.app.app_context():
            print(self.app.config['users'].users())
            self.assertTrue('foo' in self.app.config['users'].users())
            # Verify positive case
            valid, username = check_basic_auth('foo', 'bar')
            self.assertTrue(valid)
            self.assertEqual(username, 'foo')

            # Verify negative password case
            valid, username = check_basic_auth('foo', 'blah')
            self.assertFalse(valid)
            self.assertEqual('foo', username)

            # Verify negative user case
            not_user = 'notreal'
            self.assertTrue(not_user not in self.app.config['users'].users())
            valid, username = check_basic_auth(not_user, 'blah')
            self.assertFalse(valid)
            self.assertEqual(not_user, username)
