"""
Base test classes to use for common needs like
VCR and WebHistory setup.
"""
from __future__ import absolute_import, unicode_literals
import inspect
import os
import unittest

import vcr


class WebTest(unittest.TestCase):
    """
    Battery for verifying the Web history class works as expected.
    """
    URL = os.environ.get('ARCHELON_TEST_URL', 'http://localhost:8580')
    TOKEN = os.environ.get('ARCHELON_TEST_TOKEN', '1234')
    CASSETTE_LIBRARY_BASE = 'archelonc/tests/testdata/cassettes/'
    VCR = vcr.VCR(
        serializer='yaml',
        record_mode='once',
        match_on=['method', 'scheme', 'path', 'query', 'body'],
    )

    def __init__(self, *args, **kwargs):
        """
        Setup ``cassette_library_dir`` on construction.
        """
        super(WebTest, self).__init__(*args, **kwargs)
        current_file = os.path.abspath(inspect.getfile(self.__class__))
        basename = os.path.basename(current_file)
        self.VCR.cassette_library_dir = '{0}{1}'.format(
            self.CASSETTE_LIBRARY_BASE,
            basename.replace('.py', '', 1)
        )
