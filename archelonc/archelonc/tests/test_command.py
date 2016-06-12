# -*- coding: utf-8 -*-
"""
Verify the various archelonc commands.
"""
from __future__ import absolute_import, print_function, unicode_literals
import filecmp
from io import BytesIO
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
    TEST_BASH_HISTORY_ALT = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "testdata",
        "history_alt"
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
        Do the successful test with one command.
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
        with TempFile(mode='rb+') as arch_history:
            with mock.patch(
                'archelonc.command.HISTORY_FILE', arch_history.name
            ):
                arch_history.write("export FOO='bar☠'\n".encode('UTF-8'))
                arch_history.flush()
                update()
                self.assertEqual(
                    mock_web.bulk_add.call_args[0][0],
                    ["echo 'Hey you guys!☠'"]
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
            print('blah☠'.encode('UTF-8'), file=bash)
            print('', file=bash)
            bash.flush()
            print('blah☠'.encode('UTF-8'), file=arch)
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
        self.assertEqual(exception_context.exception.code, 3)

    @mock.patch.dict('os.environ', {'HISTFILE': TEST_BASH_HISTORY}, clear=True)
    @mock.patch('archelonc.command.HISTORY_FILE', TEST_ARCHELON_HISTORY)
    @mock.patch('archelonc.command.LARGE_UPDATE_COUNT', 1)
    @mock.patch('archelonc.command._get_web_setup')
    @mock.patch('sys.stdout.buffer', new_callable=BytesIO)
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
        self.assertIn('This may take a while', str(mock_stdout.getvalue()))

    @mock.patch.dict('os.environ', {'HISTFILE': TEST_BASH_HISTORY}, clear=True)
    @mock.patch('archelonc.command.HISTORY_FILE', TEST_ARCHELON_HISTORY)
    @mock.patch('archelonc.command._get_web_setup')
    def test_import_success(self, mock_web_setup):
        """
        Verify the uploading of our history file to the server.
        """
        self.addCleanup(os.remove, self.TEST_ARCHELON_HISTORY)
        mock_web = mock.MagicMock()
        mock_web.bulk_add.return_value = True, 'foo'
        mock_web_setup.return_value = mock_web
        with mock.patch('sys.argv', []):
            import_history()
        self.assertTrue(
            filecmp.cmp(self.TEST_ARCHELON_HISTORY, self.TEST_BASH_HISTORY)
        )

    @mock.patch.dict('os.environ', {'HISTFILE': TEST_BASH_HISTORY}, clear=True)
    @mock.patch('archelonc.command.HISTORY_FILE', TEST_ARCHELON_HISTORY)
    @mock.patch('archelonc.command._get_web_setup')
    def test_import_success_specified(self, mock_web_setup):
        """
        Verify the uploading of our history file to the server
        from a specified file.
        """
        self.addCleanup(os.remove, self.TEST_ARCHELON_HISTORY)
        mock_web = mock.MagicMock()
        mock_web.bulk_add.return_value = True, 'foo'
        mock_web_setup.return_value = mock_web
        with mock.patch('sys.argv', ['a', self.TEST_BASH_HISTORY_ALT]):
            import_history()
        self.assertTrue(
            filecmp.cmp(self.TEST_ARCHELON_HISTORY, self.TEST_BASH_HISTORY_ALT)
        )

    @mock.patch.dict('os.environ', {'HISTFILE': TEST_BASH_HISTORY}, clear=True)
    @mock.patch('archelonc.command._get_web_setup')
    def test_import_errors(self, mock_web_setup):
        """
        Test handling of connection error handling.
        """
        mock_web = mock.MagicMock()
        mock_web.bulk_add.side_effect = ArcheloncConnectionException()
        mock_web_setup.return_value = mock_web
        with mock.patch('sys.argv', []):
            with self.assertRaises(SystemExit) as exception_context:
                import_history()
        self.assertEqual(exception_context.exception.code, 4)

        # Test bad results coming back
        mock_web.bulk_add.side_effect = None
        mock_web.bulk_add.return_value = False, 'foo'
        with mock.patch('sys.argv', []):
            with self.assertRaises(SystemExit) as exception_context:
                import_history()
        self.assertEqual(exception_context.exception.code, 6)

    @mock.patch('archelonc.command._get_web_setup')
    @mock.patch('sys.stdout.buffer', new_callable=BytesIO)
    def test_export_success_stdout(self, mock_stdout, mock_web_setup):
        """
        Validate that we can export all commands successfully.
        """
        test_list = ['testing-export1', 'testing-export2☠']
        mock_web = mock.MagicMock()

        def side_effect(*args):
            """Do two pages of the same results."""
            if args[0] < 2:
                return test_list
            else:
                return []

        mock_web.all.side_effect = side_effect
        mock_web_setup.return_value = mock_web
        with mock.patch('sys.argv', []):
            export_history()
        self.assertEqual(
            mock_stdout.getvalue(),
            ('\n'.join(test_list * 2) + '\n').encode('UTF-8')
        )

    @mock.patch('archelonc.command._get_web_setup')
    def test_export_success_file(self, mock_web_setup):
        """
        Validate that we can export all commands successfully to a specified
        file.
        """
        self.addCleanup(os.remove, self.TEST_ARCHELON_HISTORY)
        test_list = ['testing-export1', 'testing-export2☠']
        mock_web = mock.MagicMock()

        def side_effect(*args):
            """Do two pages of the same results."""
            if args[0] < 2:
                return test_list
            else:
                return []

        mock_web.all.side_effect = side_effect
        mock_web_setup.return_value = mock_web
        with mock.patch('sys.argv', ['a', self.TEST_ARCHELON_HISTORY]):
            export_history()
        with open(self.TEST_ARCHELON_HISTORY, 'rb') as output_file:
            self.assertEqual(
                output_file.read().decode('UTF-8'),
                '\n'.join(test_list * 2) + '\n'
            )

    @mock.patch('archelonc.command._get_web_setup')
    def test_export_connection_error(self, mock_web_setup):
        """
        Test handling of connection error handling.
        """
        mock_web = mock.MagicMock()
        mock_web.all.side_effect = ArcheloncConnectionException()
        mock_web_setup.return_value = mock_web
        with mock.patch('sys.argv', []):
            with self.assertRaises(SystemExit) as exception_context:
                export_history()
        self.assertEqual(exception_context.exception.code, 5)
