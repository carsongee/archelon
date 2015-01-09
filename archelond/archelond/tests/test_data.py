"""
Test out the server data classes
"""
import unittest

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
        self.config = wsgi_app().config
        self.data = archelond.data.MemoryData(self.config)

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
