# -*- coding: utf-8 -*-
"""
Tests for the search interface and classes.
"""
from __future__ import absolute_import, unicode_literals
import os
from tempfile import NamedTemporaryFile
import unittest

import mock

from archelonc.search import (
    Search, SearchForm, SearchBox, CommandBox, SearchResults, SearchResult
)
from archelonc.data import (
    LocalHistory, WebHistory, ArcheloncConnectionException
)


class TestSearchResult(unittest.TestCase):
    """
    Verify the SearchResult Component.
    """
    def test_update(self):
        """
        Verify that we handle update events properly.
        """
        with mock.patch('npyscreen.Textfield.__init__') as mock_init:
            mock_init.return_value = None
            search_result = SearchResult(mock.MagicMock())
        mock_parent = search_result.parent = mock.MagicMock()
        # Call without highlight set to verify we don't change any state
        # except by calling the super update method.
        mock_parent.results_list.side_effect = Exception
        search_result.highlight = False
        with mock.patch('npyscreen.Textfield.update') as mock_update:
            search_result.update()
            self.assertTrue(mock_update.called_once)

        # Verify case of not needing to page results.
        mock_parent.reset_mock()
        search_result.highlight = True
        mock_parent.results_list.side_effect = None
        mock_parent.results_list.values = ['a', 'b', 'c']
        mock_parent.results_list.cursor_line = 1
        with mock.patch('npyscreen.Textfield.update') as mock_update:
            search_result.update()
        self.assertTrue(mock_update.called_once)
        self.assertFalse(mock_parent.results_list.update.called)

        # Do the paging with results and assert we increment page.
        mock_parent.reset_mock()
        mock_parent.parentApp.page = 41
        mock_parent.results_list.cursor_line = 2
        mock_parent.search_box.search.return_value = range(2)
        with mock.patch('npyscreen.Textfield.update') as mock_update:
            search_result.update()
        self.assertTrue(mock_update.called_once)
        self.assertTrue(mock_parent.results_list.update.called)
        self.assertEqual(42, mock_parent.parentApp.page)
        self.assertNotEqual(False, mock_parent.parentApp.more)
        mock_parent.search_box.search.assert_called_once_with(page=42)

        # Do the paging without results and assert we falsify
        # ``parent.ParentApp.more``.
        mock_parent.reset_mock()
        mock_parent.results_list.values = ['a', 'b', 'c']
        mock_parent.search_box.search.return_value = []
        mock_parent.parentApp.more = True
        with mock.patch('npyscreen.Textfield.update') as mock_update:
            search_result.update()
        self.assertTrue(mock_update.called_once)
        self.assertTrue(mock_parent.results_list.update.called)
        self.assertEqual(43, mock_parent.parentApp.page)
        self.assertEqual(False, mock_parent.parentApp.more)
        mock_parent.search_box.search.assert_called_once_with(page=43)


class TestCommandBox(unittest.TestCase):
    """
    Verify the CommandBox component.
    """
    @staticmethod
    def _get_command_box():
        """
        Get mocked command box.
        """
        with mock.patch('npyscreen.TitleText.__init__') as mock_init:
            mock_init.return_value = None
            return CommandBox(mock.MagicMock())

    def test_init(self):
        """
        Verify the constructor does as we expect.
        """
        command_box = self._get_command_box()
        self.assertFalse(command_box.been_edited)

    def test_edited_handler(self):
        """
        Verify the constructor does as we expect.
        """
        command_box = self._get_command_box()
        self.assertFalse(command_box.been_edited)
        command_box.when_value_edited()
        self.assertTrue(command_box.been_edited)


class TestSearchBox(unittest.TestCase):
    """
    Verify the SearchBox component.
    """
    @staticmethod
    def _get_mocked_searchbox():
        """
        Generate a nicely mocked SearchBox.
        """
        with mock.patch('npyscreen.TitleText.__init__') as mock_init:
            mock_init.return_value = None
            search_box = SearchBox(mock.MagicMock())
        search_box.entry_widget = mock.MagicMock()
        search_box.value = 'Hi'
        mock_parent = mock.MagicMock()
        search_box.parent = mock_parent
        mock_parent.order = None
        return search_box, mock_parent

    def test_search(self):
        """
        Searching forward works.
        """
        search_box, mock_parent = self._get_mocked_searchbox()

        # Test forward search
        search_box.search()
        mock_parent.parentApp.data.search_forward.assert_called_with(
            search_box.value, 0
        )

        # Set page in call and verify
        search_box.search(14)
        mock_parent.parentApp.data.search_forward.assert_called_with(
            search_box.value, 14
        )

        # Test reverse search
        mock_parent.order = 'r'
        search_box.search()
        mock_parent.parentApp.data.search_reverse.assert_called_with(
            search_box.value, 0
        )

        # Set page in call and verify
        search_box.search(14)
        mock_parent.parentApp.data.search_reverse.assert_called_with(
            search_box.value, 14
        )

    def test_search_exception(self):
        """
        Verify we exit out on search failures.
        """
        search_box, mock_parent = self._get_mocked_searchbox()
        mock_parent.parentApp.data.search_forward.side_effect = (
            ArcheloncConnectionException
        )
        with self.assertRaises(SystemExit) as exception_context:
            search_box.search()
        self.assertEqual(exception_context.exception.code, 1)
        mock_parent.parentApp.data.search_forward.assert_called_with(
            search_box.value, 0
        )

    def test_value_edited_handler(self):
        """
        Veriy that the value edited handler does as expected.
        """
        search_box, mock_parent = self._get_mocked_searchbox()
        search_box.search = mock.MagicMock()

        # Verify no op on no value
        search_box.value = ''
        search_box.when_value_edited()
        self.assertFalse(search_box.search.called)

        # Verify page setting, state changing and other commands
        mock_parent.parentApp.page = 40
        mock_parent.parentApp.more = False
        search_box.value = 'Hi'
        search_box.when_value_edited()
        self.assertEqual(mock_parent.parentApp.page, 0)
        self.assertEqual(mock_parent.parentApp.more, True)
        mock_parent.results_list.reset_display_cache.assert_called_once_with()
        mock_parent.results_list.reset_cursor.assert_called_once_with()
        mock_parent.results_list.update.assert_called_once_with()

        # Verify that we update command box if it hasn't been edited
        mock_parent.command_box.been_edited = False
        search_box.when_value_edited()
        # No results, so nothing should be done with the box
        self.assertFalse(mock_parent.command_box.update.called)
        # Add some results
        search_box.search.return_value = ['foo']
        search_box.when_value_edited()
        self.assertEqual(mock_parent.command_box.value, 'foo')


class TestSearchResults(unittest.TestCase):
    """
    Verify the SearchResults component handlers.
    """
    def test_highlighted_action(self):
        """
        Verify that we update the CommandBox when highlighted and
        it hasn't been updated.
        """
        with mock.patch('npyscreen.MultiLineAction.__init__') as mock_init:
            mock_init.return_value = None
            search_results = SearchResults(mock.MagicMock())
        mocked_parent = search_results.parent = mock.MagicMock()
        mocked_parent.editw = 0
        test_value = 'fhqwhgads'
        search_results.actionHighlighted(test_value, None)
        self.assertEqual(mocked_parent.command_box.value, test_value)
        self.assertEqual(2, mocked_parent.editw)
        mocked_parent.command_box.edit.assert_called_once_with()
        mocked_parent.command_box.update.assert_called_once_with()


@mock.patch('npyscreen.ActionFormWithMenus.__init__')
class TestSearchForm(unittest.TestCase):
    """
    Test for the main form and creation.
    """

    def test_form_init(self, mocked_super):
        """
        Verify we are calling super and that order is set.
        """
        form = SearchForm(1, a='b')
        mocked_super.assert_called_with(1, a='b')
        self.assertTrue(hasattr(form, 'order'))

    def test_create(self, _):
        """
        Verify all of our creation code is as expected (thought this is
        strictly a unit test since I am mocking everything else out, and
        create is called during the initialization with the super class
        that I am mocking out as well.
        """
        form = SearchForm()
        form.add = mock.MagicMock()
        form.add_handlers = mock.MagicMock()
        with mock.patch('archelonc.search.SearchBox') as _,\
                mock.patch('archelonc.search.SearchResults') as _,\
                mock.patch('archelonc.search.CommandBox') as _:
            form.create()
            self.assertEqual(form.order, 'r')
            for attr in ('search_box', 'results_list', 'command_box'):
                self.assertTrue(hasattr(form, attr))
            self.assertEqual(len(form.menu.getItemObjects()), 2)
            self.assertTrue(form.add_handlers.called_once)

    def test_orders(self, _):
        """
        Verify the forward and reverse orders do as expected.
        """
        form = SearchForm()
        form.search_box = mock.MagicMock()
        form.order = 'not_real'
        form.forward_order()
        self.assertIsNone(form.order)
        self.assertTrue(form.search_box.when_value_edited.called_once())

        # Now the reverse.
        form.search_box = mock.MagicMock()
        form.order = 'flibber-flab'
        form.reverse_order()
        self.assertEqual('r', form.order)
        self.assertTrue(form.search_box.when_value_edited.called_once())

    def test_edit_events(self, _):
        """
        Verify the event handlers (before and after).
        """
        form = SearchForm()
        form.preserve_selected_widget = False
        form.beforeEditing()
        self.assertTrue(form.preserve_selected_widget)

        form.parentApp = mock.MagicMock()
        form.afterEditing()
        form.parentApp.setNextForm.assert_called_with(None)

    def test_exit_handlers(self, _):
        """
        Verify the exit handlers do what we want.
        """
        form = SearchForm()
        with self.assertRaises(SystemExit) as exception_context:
            form.on_cancel()
        self.assertEqual(exception_context.exception.code, 1)
        form.command_box = mock.MagicMock()
        test_command = 'Hello Testo'
        form.command_box.value = test_command
        with NamedTemporaryFile(mode='r+') as temp_file:
            with mock.patch('os.path.expanduser') as expand_hijack:
                expand_hijack.return_value = os.path.abspath(temp_file.name)
                with self.assertRaises(SystemExit) as exception_context:
                    form.on_ok()
                self.assertEqual(exception_context.exception.code, 0)
                temp_file.seek(0)
                self.assertEqual(test_command, temp_file.read())


class TestSearch(unittest.TestCase):
    """
    Test for the main app and history initialization.
    """

    def test_search_init(self):
        """
        Verify main form initializes as expected.
        """
        search = Search()
        self.assertTrue(hasattr(search, 'data'))

    def test_search_onstart(self):
        """
        Verify we setup the form and data class correctly
        """
        search = Search()
        search.addForm = mock.MagicMock()
        # Verify local data with no URLs set.
        with mock.patch.dict('os.environ', {}, clear=True):
            with mock.patch('archelonc.search.LocalHistory.__init__') as init:
                init.return_value = None
                search.onStart()
        self.assertTrue(isinstance(search.data, LocalHistory))

        # Verify Web data with URLs set.
        with mock.patch.dict(
            'os.environ',
            {'ARCHELON_URL': 'http://foo', 'ARCHELON_TOKEN': 'foo'},
            clear=True
        ):
            search.onStart()
        self.assertTrue(isinstance(search.data, WebHistory))
