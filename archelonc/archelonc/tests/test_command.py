"""
Verify the various archelnc commands.
"""
from __future__ import absolute_import, print_function, unicode_literals
from cStringIO import StringIO
import filecmp
import os
from tempfile import NamedTemporaryFile as TempFile

import mock

from archelonc.command import (
    _get_web_setup,
    search_form,
    update,
    import_history,
    export_history
)
from archelonc.data import ArcheloncConnectionException
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
    def test_update_successful(self):
        """
        Do the succesful test with one command.
        """
        self.assertFalse(os.path.exists(self.TEST_ARCHELON_HISTORY))
        self.addCleanup(os.remove, self.TEST_ARCHELON_HISTORY)
        update()
        self.assertTrue(
            filecmp.cmp(self.TEST_ARCHELON_HISTORY, self.TEST_BASH_HISTORY)
        )

    @mock.patch.dict('os.environ', {'HISTFILE': TEST_BASH_HISTORY}, clear=True)
    @mock.patch('archelonc.command._get_web_setup')
    def test_update_diff(self, mock_web_setup):
        """
        Verify that we are smart about diffing history.
        """
        mock_web = mock.MagicMock()
        mock_web.bulk_add.return_value = True, 'foo'
        mock_web_setup.return_value = mock_web
        with TempFile(mode='r+') as arch_history:
            with mock.patch(
                'archelonc.command.HISTORY_FILE', arch_history.name
            ):
                print("export FOO='bar'", file=arch_history)
                arch_history.flush()
                update()
                self.assertEqual(
                    mock_web.bulk_add.call_args[0][0],
                    ["echo 'Hey you guys!'"]
                )

    @mock.patch('archelonc.command._get_web_setup')
    def test_update_diff_blanks(self, mock_web_setup):
        """
        Verify that we ignore blank commands in history on update.
        """
        mock_web = mock.MagicMock()
        mock_web.bulk_add.return_value = True, 'foo'
        mock_web_setup.return_value = mock_web

        with TempFile(mode='r+') as bash, TempFile(mode='r+') as arch:
            print('blah', file=bash)
            print('', file=bash)
            bash.flush()
            print('blah', file=arch)
            arch.flush()
            with mock.patch.dict(
                'os.environ', {'HISTFILE': bash.name}, clear=True
            ):
                with mock.patch('archelonc.command.HISTORY_FILE', arch.name):
                    update()
            self.assertFalse(mock_web.bulk_add.called)

    @mock.patch.dict('os.environ', {'HISTFILE': TEST_BASH_HISTORY}, clear=True)
    @mock.patch('archelonc.command.HISTORY_FILE', TEST_ARCHELON_HISTORY)
    @mock.patch('archelonc.command._get_web_setup')
    def test_update_not_success(self, mock_web_setup):
        """
        Verify exception handling and failure mode in update command.
        """
        self.addCleanup(os.remove, self.TEST_ARCHELON_HISTORY)
        mock_web = mock.MagicMock()
        mock_web.bulk_add.return_value = False, 'foo'
        mock_web_setup.return_value = mock_web
        # Test with failed Web response
        with self.assertRaises(SystemExit) as exception_context:
            update()
        self.assertEqual(exception_context.exception.code, 2)
        mock_web.bulk_add.return_value = True, 'foo'
        mock_web.bulk_add.side_effect = ArcheloncConnectionException
        # Test with connection error
        with self.assertRaises(SystemExit) as exception_context:
            update()
        self.assertEqual(exception_context.exception.code, 1)

    @mock.patch.dict('os.environ', {'HISTFILE': TEST_BASH_HISTORY}, clear=True)
    @mock.patch('archelonc.command.HISTORY_FILE', TEST_ARCHELON_HISTORY)
    @mock.patch('archelonc.command.LARGE_UPDATE_COUNT', 1)
    @mock.patch('archelonc.command._get_web_setup')
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_update_large_indicator(self, mock_stdout, mock_web_setup):
        """
        Verify output when there are greater than 50 commands
        """
        self.addCleanup(os.remove, self.TEST_ARCHELON_HISTORY)
        mock_web = mock.MagicMock()
        mock_web.bulk_add.return_value = False, 'foo'
        mock_web_setup.return_value = mock_web
        with self.assertRaises(SystemExit) as exception_context:
            update()
        self.assertEqual(exception_context.exception.code, 2)
        self.assertIn('This may take a while', mock_stdout.getvalue())
