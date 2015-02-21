"""
Common test classes to inherit from
"""
import os
import unittest

import archelond.data
from archelond.web import wsgi_app


class ElasticTestClass(unittest.TestCase):
    """
    Base class that uses the elastic config
    """
    def setUp(self):
        """
        Create the ElasticData Object and make it available to tests.
        """
        self.old_conf = os.environ.get('ARCHELOND_CONF')
        os.environ['ARCHELOND_CONF'] = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'config', 'elastic.py'
        )
        self.config = wsgi_app().config
        self.data = archelond.data.ElasticData(self.config)
        self.app = wsgi_app()
        # Set well known secret for known token generation
        self.app.config['FLASK_SECRET'] = 'wellknown'

    def tearDown(self):  # pragma: no cover
        """
        Nuke the entire index at the end of each test, and reset the
        conf environment variable.
        """
        client = self.data.elasticsearch
        client.indices.delete(self.config['ELASTICSEARCH_INDEX'])
        if self.old_conf:
            os.environ['ARCHELOND_CONF'] = self.old_conf
        else:
            del os.environ['ARCHELOND_CONF']
