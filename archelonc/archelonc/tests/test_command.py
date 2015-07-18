"""
Verify the various archelnc commands.
"""
from __future__ import absolute_import, print_function, unicode_literals
import filecmp
import os

import mock

from archelonc.command import (
    _get_web_setup,
    search_form,
    update,
    import_history,
    export_history
)
from archelonc.tests.base import WebTest


class TestCommands(WebTest):
    """
    Battery of tests for validating the command entry points
    """

    TEST_ARCHELON_HISTORY = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "testdata",
        "archelon_history"
    )
    TEST_BASH_HISTORY = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "testdata",
        "history"
    )

    def test_web_setup(self):
        """
        Validate the common WebHistory configuration.
        """
        # Verify unconfigured behavior
        with mock.patch.dict('os.environ', {}, clear=True):
            self.assertIsNone(_get_web_setup())
        # Verify configured behavior
        with mock.patch.dict(
            'os.environ',
            {'ARCHELON_URL': 'foo', 'ARCHELON_TOKEN': 'bar'},
            clear=True
        ):
            web = _get_web_setup()
            self.assertEqual(web.url, 'foo{}'.format(web.SEARCH_URL))
            self.assertEqual(web.session.headers['Authorization'], 'token bar')

    @mock.patch('archelonc.command.Search')
    def test_search_form(self, mock_search):
        """
        Verify the search inittialization command.
        """
        search_form()
        self.assertTrue(mock_search().run.called_once)

    def test_commands_unconfigured(self):
        """
        Verify commands that need Web history exit when not configured.
        """
        with mock.patch.dict('os.environ', {}, clear=True):
            for function in (update, import_history, export_history):
                with self.assertRaises(SystemExit) as exception_context:
                    function()
                self.assertEqual(exception_context.exception.code, 1)

    @WebTest.VCR.use_cassette()
    @mock.patch.dict(
        'os.environ',
        {
            'ARCHELON_URL': WebTest.URL,
            'ARCHELON_TOKEN': WebTest.TOKEN,
            'HISTFILE': TEST_BASH_HISTORY
        },
        clear=True
    )
    @mock.patch('archelonc.command.HISTORY_FILE', TEST_ARCHELON_HISTORY)
    def test_update_successful(self,):
        """
        Do the succesful test with one command.
        """
        self.assertFalse(os.path.exists(self.TEST_ARCHELON_HISTORY))
        self.addCleanup(os.remove, self.TEST_ARCHELON_HISTORY)
        update()
        self.assertTrue(
            filecmp.cmp(self.TEST_ARCHELON_HISTORY, self.TEST_BASH_HISTORY)
        )
