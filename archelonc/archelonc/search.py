# -*- coding: utf-8 -*-
"""
npyscreen based application for searching shell history
"""
import curses
import os
import sys

import npyscreen

from archelonc.data import LocalHistory, WebHistory


class SearchResult(npyscreen.Textfield):
    """
    Search result item
    """
    def update(self, clear=True):
        if self.highlight:
            results_list = self.parent.results_list
            current_item = results_list.cursor_line
            total_items = len(results_list.values)
            app = self.parent.parentApp
            if (current_item == total_items - 1) and app.more:
                # Grab the next set of results
                app.page += 1
                results = self.parent.search_box.search(page=app.page)
                if len(results) == 0:
                    app.more = False
                results_list.values.extend(results)
                results_list.reset_display_cache()
                results_list.update()
        super(SearchResult, self).update(clear)


class CommandBox(npyscreen.TitleText):
    """
    Command Box widget
    """

    def __init__(self, screen, **kwargs):
        """
        Just add some state to the default
        widget to track if we have been manually
        edited
        """
        self.been_edited = False
        super(CommandBox, self).__init__(screen, **kwargs)

    def when_value_edited(self):
        """
        Mark myself as having been edited
        """
        self.been_edited = True


class SearchResults(npyscreen.MultiLineAction):
    """
    MultiLine widget for displaying search
    results.
    """
    _contained_widgets = SearchResult

    def actionHighlighted(self, act_on_this, key_press):
        cmd_box = self.parent.command_box
        cmd_box.value = act_on_this
        cmd_box.been_edited = True
        cmd_box.update()
        self.parent.editw = 2
        self.parent.command_box.edit()


class SearchBox(npyscreen.TitleText):
    """
    Search box command, updates trigger
    deeper searching.
    """
    def search(self, page=0):
        """
        Do the search and return the results
        """
        if not self.parent.order:
            return self.parent.parentApp.data.search_forward(self.value, page)
        elif self.parent.order == 'r':
            return self.parent.parentApp.data.search_reverse(self.value, page)

    def when_value_edited(self):
        """
        Do the search and filter the search result
        list based on what is returned
        """
        if len(self.value) == 0:
            return
        results_list = self.parent.results_list
        cmd_box = self.parent.command_box

        # Reset page number back to 0
        self.parent.parentApp.page = 0
        self.parent.parentApp.more = True

        search_results = self.search()
        results_list.values = search_results
        results_list.reset_display_cache()
        results_list.reset_cursor()
        results_list.update()

        # If you haven't edited the command box, go ahead
        # and put the top value in there to save time.
        if not cmd_box.been_edited:
            if len(search_results) > 0:
                cmd_box.value = search_results[0]
                cmd_box.update()


class SearchForm(npyscreen.ActionFormWithMenus):
    """
    Command history search form
    """

    def forward_order(self):
        """
        Change sort order to forward
        """
        self.order = None
        self.search_box.when_value_edited()

    def reverse_order(self):
        """
        Change sort order to forward
        """
        self.order = 'r'
        self.search_box.when_value_edited()

    def afterEditing(self):
        """
        This is the form to display, so set next to None
        """
        self.parentApp.setNextForm(None)

    def create(self):
        """
        Build the form for searching
        """
        # Set default order to reverse
        self.order = 'r'

        self.search_box = self.add(
            SearchBox,
            name='Search',
            begin_entry_at=10
        )
        self.results_list = self.add(
            SearchResults,
            name='Results',
            scroll_exit=True,
            max_height=-2,
            values=[]
        )
        self.command_box = self.add(
            CommandBox,
            name='Command',
            begin_entry_at=10,
            rely=-3
        )

        self.add_handlers({
            '!o': self.on_ok,
            '!c': self.on_cancel,
            curses.ascii.ESC: self.on_cancel
        })

        # Create our menus
        self.menu = self.new_menu()
        self.menu.addItemsFromList([
            ('Forward Order', self.forward_order, '^F'),
            ('Reverse Order', self.reverse_order, '^R'),
        ])

    def beforeEditing(self):
        """
        Set the edit index to the search box
        and tell it to preserve the value
        """
        self.preserve_selected_widget = True

    def on_ok(self, *args):
        """
        We just drop the command into a
        known file for the wrapper to pick
        up
        """
        with open(os.path.expanduser('~/.archelon_cmd'), 'w') as cmd_file:
            cmd_file.write(self.command_box.value)
        sys.exit(0)

    def on_cancel(self, *args):
        """
        Drop out with a non 1 exit code so the
        wrapper doesn't execute anything
        """
        sys.exit(1)


class Search(npyscreen.NPSAppManaged):
    """
    Search application.  Determines which form to show.
    """
    # Set default page, and whether there are more results
    page = 0
    more = True

    def onStart(self):
        """
        Startup routine for the search application
        """
        url = os.environ.get('ARCHELON_URL')
        token = os.environ.get('ARCHELON_TOKEN')

        #  Determine the data model to use.
        if url and token:
            self.data = WebHistory(url, token)
        else:
            self.data = LocalHistory()

        self.addForm('MAIN', SearchForm, name='Archelon: Reverse Search')
