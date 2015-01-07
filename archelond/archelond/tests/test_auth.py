"""
Test out our authentication module.
"""
import os
import unittest

from archelond.web import wsgi_app
from archelond.auth import (
    check_basic_auth,
    generate_token,
    get_hashhash,
    get_signature
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

    def test_token_generation(self):
        """
        Verify token authentication using known hash and signature
        """
        test_user = 'foo'
        known_token = ('eyJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6ImZvbyIsImhhc2'
                       'hoYXNoIjoiNTEwNjI3M2Y3Nzg5ZjFlMjZiNGEyMTI3ODk5OTJmN'
                       'zVjMTU0MzNmNDAyZjNlOTRhZDE4ZTdjODBhZWU4MGZhZiJ9.Bas'
                       'bIHjgUzemMiBI34SmbiOkOm49ktZZWrFT6b71mVs')
        known_hashhash = ('5106273f7789f1e26b4a212789992f75c15433f402f3e94a'
                          'd18e7c80aee80faf')

        with self.app.app_context():
            # Set well known secret for known token generation
            self.app.config['FLASK_SECRET'] = 'wellknown'

            # Verify token generation against known value
            token = generate_token(test_user)
            self.assertEqual(known_token, token)

            # Verify hashhash against known value
            hashhash = get_hashhash(test_user)
            self.assertEqual(hashhash, known_hashhash)

            # Now go ahead and verify the reverse
            serializer = get_signature()
            data = serializer.loads(token)
            self.assertTrue(data['username'], test_user)
            self.assertTrue(data['hashhash'], hashhash)
