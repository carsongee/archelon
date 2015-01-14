"""
Unit tests for :py:module:`archelond.util`.
"""
import json
import unittest

from flask import Response

from archelond.util import jsonify_code
from archelond.web import app


class TestUtil(unittest.TestCase):
    """
    Verify expected util functionality.
    """
    def test_jsonify_code(self):
        """
        Test paths in py:function:`archelond.util.jsonify_code`
        """
        with app.test_request_context():
            # Check expected path
            response = jsonify_code({'test': 1}, 400)
            self.assertTrue(response.status_code, 400)
            self.assertTrue(isinstance(response, Response))
            self.assertEqual(
                response.response,
                [json.dumps({'test': 1}, indent=2)]
            )

            # Verify jsonify not accepting a root valued json object
            with self.assertRaisesRegexp(ValueError,
                                         'dictionary update sequence element'
                                         ' #0 .+'):

                jsonify_code('asdf', 200)

            # Verify bad status_code
            with self.assertRaisesRegexp(TypeError,
                                         'a number is required'):

                jsonify_code({'test': 1}, 'foo')
