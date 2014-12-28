"""
Configure the flask application
"""
import os

DEBUG = False
FLASK_SECRET = os.environ.get('ARCHELOND_FLASK_SECRET', 'please-change-me')
LOG_LEVEL = os.environ.get('ARCHELOND_LOG_LEVEL', None)

DATABASE_TYPE = os.environ.get(
    'ARCHELOND_DATABASE',
    'MemoryData'
)

ELASTICSEARCH_URL = os.environ.get('ARCHELOND_ELASTICSEARCH_URL', None)
ELASTICSEARCH_INDEX = os.environ.get('ARCHELOND_ELASTICSEARCH_INDEX', None)

# Load path to environment variable to point to htpasswd file
# or write the ARCHELOND_HTPASSWD out to a file and ref that
HTPASSWD_PATH = os.environ.get('ARCHELOND_HTPASSWD_PATH', '.htpasswd')
if os.environ.get('ARCHELOND_HTPASSWD'):
    HTPASSWD_PATH = os.path.abspath('.htpasswd')
    with open(HTPASSWD_PATH, 'w') as wfile:
        wfile.write(os.environ['ARCHELOND_HTPASSWD'])
