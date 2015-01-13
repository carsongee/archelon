"""
Setup test configuration
"""
import os

DEBUG = True
FLASK_SECRET = os.environ.get('ARCHELOND_TEST_FLASK_SECRET', 'dummy')
LOG_LEVEL = os.environ.get('ARCHELOND_TEST_LOG_LEVEL', None)
DATABASE_TYPE = os.environ.get(
    'ARCHELOND_TEST_DATABASE',
    'MemoryData'
)

ELASTICSEARCH_URL = os.environ.get(
    'ARCHELOND_TEST_ELASTICSEARCH_URL',
    'localhost:9200'
)
ELASTICSEARCH_INDEX = os.environ.get(
    'ARCHELOND_TEST_ELASTICSEARCH_INDEX', 'test_search_index'
)


# Load path to environment variable to point to htpasswd file
# Test password file is:
# enigma: pass
# norm: god
# foo: bar
HTPASSWD_PATH = os.environ.get(
    'ARCHELOND_TEST_HTPASSWD_PATH',
    os.path.join(os.path.dirname(
        os.path.abspath(__file__)
        ), 'test_htpasswd')
)
