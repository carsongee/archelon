# -*- coding: utf-8 -*-
"""
Tests for the search interface and classes.
"""
from __future__ import absolute_import, unicode_literals
import os
from tempfile import NamedTemporaryFile
import unittest

import mock

from archelonc.search import Search, SearchForm
from archelonc.data import LocalHistory, WebHistory


class TestSearchMain(unittest.TestCase):
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
