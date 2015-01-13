"""
Test out the server data classes
"""
import os
import time
import unittest

from elasticsearch import Elasticsearch

import archelond.data
from archelond.data.abstract import HistoryData
from archelond.web import wsgi_app


class TestBaseHistoryData(unittest.TestCase):

    """
    Test out abstract class for history data
    """

    def test_abc(self):
        """
        Verify that we are still abstract and
        can't be instantiated directly
        """
        with self.assertRaises(TypeError):
            HistoryData()

    def test_abc_signature(self):
        """
        Verify that the methods are what we expect.
        """
        expected_set = ('__init__', 'add', 'all', 'delete', 'filter', 'get',)
        abstract_methods = HistoryData.__abstractmethods__
        self.assertEqual(0, len(abstract_methods.difference(expected_set)))

    def test_subclasses(self):
        """
        Verify that all of our data classes are proper subclasses of
        HistoryData

        """
        from archelond.data import __all__
        for klass in __all__:
            self.assertTrue(
                HistoryData.__subclasscheck__(
                    eval('archelond.data.{}'.format(klass))
                )
            )


class TestMemoryData(unittest.TestCase):
    """
    Validate the MemoryData to be working as expected
    """

    def setUp(self):
        """
        Build internal data model with app context
        """
        self.old_conf = os.environ.get('ARCHELOND_CONF')
        os.environ['ARCHELOND_CONF'] = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'config', 'basic.py'
        )
        self.config = wsgi_app().config
        self.data = archelond.data.MemoryData(self.config)

    def tearDown(self):  # pragma: no cover
        """
        Restore previous config variable
        """
        if self.old_conf:
            os.environ['ARCHELOND_CONF'] = self.old_conf
        else:
            del os.environ['ARCHELOND_CONF']

    def test_init(self):
        """
        Verify ``__init__`` works as expected
        """
        # Assert super init being done
        self.assertEqual(self.config, self.data.config)

        # assert data set is equal to INITIAL_DATA
        data = self.data.data.values()
        print(data)
        commands = [x['command'] for x in data]
        for command in commands:
            self.assertTrue(command in self.data.INITIAL_DATA)

    def test_add_get_delete(self):
        """
        Verify the three single item operations work as expected.
        """
        COMMAND = 'echo "archelond is awesome"'
        # Not there to start
        self.assertEqual(
            0,
            len(self.data.filter(COMMAND, None,  None, None))
        )
        # Add
        id = self.data.add(COMMAND, None, None)
        # Make sure filter gets it
        self.assertEqual(
            1,
            len(self.data.filter(COMMAND, None,  None, None))
        )
        # Get by ID
        command = self.data.get(id, None, None)
        self.assertEqual(command['command'], COMMAND)

        # Delete
        command = self.data.delete(id, None, None)
        self.assertEqual(
            0,
            len(self.data.filter(COMMAND, None,  None, None))
        )
        with self.assertRaises(KeyError):
            self.data.get(id, None, None)

    def test_all(self):
        """
        Make sure ``all`` works as expected.
        """
        # Start by deleting everything from all
        for cmd in self.data.all(None, None, None):
            self.data.delete(cmd['id'], None, None)
        self.assertEqual(0, len(self.data.all(None, None, None)))

        # Add two items to check order
        COMMANDS = ['foo', 'bar']
        for item in COMMANDS:
            self.data.add(item, None, None)
        all_cmds = self.data.all(None, None, None)
        index = 0
        for item in all_cmds:
            self.assertEqual(item['command'], COMMANDS[index])
            index += 1
        # Verify reversed
        all_cmds = self.data.all('r', None, None)
        index = len(COMMANDS)-1
        for item in all_cmds:
            self.assertEqual(item['command'], COMMANDS[index])
            index -= 1


class TestElasticData(unittest.TestCase):
    """Test out elastic search backed data store.

    This requires a running ElasticSearch service and will create and
    destroy a test index using the test settings.
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

    def test_init(self):
        """Validate that init is doing what we want.

        Check that we are creating an index, setting up an analyzer
        and the command column, etc.
        """

        client = self.data.elasticsearch
        self.assertTrue(
            client.indices.exists(self.config['ELASTICSEARCH_INDEX'])
        )

        # Verify the mapping and analyzer
        settings = client.indices.get(
            self.config['ELASTICSEARCH_INDEX']
        )[self.config['ELASTICSEARCH_INDEX']]

        self.assertEqual(
            settings['settings']['index']['analysis'],
            {
                u'analyzer': {
                    u'command_analyzer':
                    {u'filter': u'lowercase', u'tokenizer': u'keyword'}
                }
            }
        )

        self.assertEqual(
            settings['mappings'],
            {
                self.config['ELASTICSEARCH_INDEX']: {
                    u'properties': {
                        u'command':
                        {
                            u'type': u'string',
                            u'analyzer': u'command_analyzer'
                        }
                    }
                }
            }
        )
          
    def test_doc_type(self):
        """
        Test that we are using the right document type
        """
        self.assertEqual(
            'enigma_{0}'.format(self.data.DOC_TYPE),
            self.data._doc_type('enigma')
        )

    def test_doc_id(self):
        """
        Use well known sha for document type to verify we are
        properly generating the document IDs.
        """
        self.assertEqual(
            self.data._doc_id('cat /foo'),
            'fdb20d1476775be75955a981f806509419cc198f1c74bc585a036baceefa8521'
        )

    def test_add_get_delete(self):
        """
        Verify the three single item operations work as expected.
        """
        USER = 'archelon-jr'
        COMMAND = 'echo "archelond is awesome"'

        # Add
        id = self.data.add(COMMAND, USER, None)

        # Get by ID
        command = self.data.get(id, USER, None)
        self.assertEqual(command['command'], COMMAND)

        # Delete
        command = self.data.delete(id, USER, None)

        with self.assertRaises(KeyError):
            self.data.get(id, None, None)

        # Delete again to verify it raises the right error
        with self.assertRaises(KeyError):
            self.data.delete(id, USER, None)

    def test_all(self):
        """
        Since this is paged and we don't support paging yet, we won't
        actually get all the results, but test that for smaller sets
        of commands, we do.
        """
        NUM_COMMANDS = self.data.NUM_RESULTS - 1
        USER = 'archelon-jr'
        NOT_USER = 'enigma'

        self.assertEqual(0, len(self.data.all(None, USER, None)))
        for command_increment in range(NUM_COMMANDS):
            self.data.add(
                'go giant turtle number {}'.format(command_increment),
                USER,
                None
            )
        # Add a command from another user to make sure we
        # are properly filtering by user.
        self.data.add('better not see me', NOT_USER, None)
        # Wait a little for the index to build
        time.sleep(1)
        results = self.data.all('r', USER, None)
        self.assertEqual(NUM_COMMANDS, len(results))
        # Verify order while we are at it
        self.assertEqual(
            results[0]['command'],
            'go giant turtle number {}'.format(NUM_COMMANDS-1)
        )

    def test_search(self):
        """
        Make sure we can find things we add
        """
        USER = 'archelon-jr'
        self.data.add('is this thing on', USER, None)
        self.data.add('cheesey petes', USER, None)
        time.sleep(1)
        results = self.data.filter('this', None, USER, None)
        self.assertEqual(1, len(results))
        self.assertFalse('petes' in results[0]['command'])

    def test_bad_connection(self):
        """
        Replace the data storage class instance with a dead one
        and call filter to see what happens
        """
        store_connection = self.data.elasticsearch
        self.data.elasticsearch = Elasticsearch(
            'localhost:65535'
        )
        self.data.all(None, 'enigma', None)
        self.data.elasticsearch = store_connection
