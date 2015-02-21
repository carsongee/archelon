# -*- coding: utf-8 -*-
"""
Data modeling for command history to be modular
"""
from __future__ import print_function
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
import os
import sys

import requests


class HistoryBase(object):
    """
    Base class of what all backend command history
    searches should use.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def search_forward(self, term, page=0):
        """
        Return a list of commmands that is in forward
        time order. i.e oldest first.

        If paging is needed, the page parameter is available.
        """
        pass

    @abstractmethod
    def search_reverse(self, term, page=0):
        """
        Return a list of commmands that is in reverse
        time order. i.e newest first.

        If paging is needed, the page parameter is available.
        """
        pass


class LocalHistory(HistoryBase):
    """
    Use local .bash_history for doing searches
    """
    def __init__(self):
        """
        Load up the bash history uniqueified into an
        OrderedDict for forward/backward searching and then
        dumped to a list.
        """
        history_dict = OrderedDict()
        with open(os.path.expanduser('~/.bash_history')) as history_file:
            for line in history_file:
                history_dict[line.strip()] = None
        self.data = history_dict.keys()

    def search_forward(self, term, page=0):
        """
        Return a list of commmands that is in forward
        time order. i.e oldest first.
        """
        if page != 0:
            return []
        return [
            x for x in self.data
            if term in x
        ]

    def search_reverse(self, term, page=0):
        """
        Return reversed filtered list by term
        """
        if page != 0:
            return []
        results = [
            x for x in self.data
            if term in x
        ]
        results.reverse()
        return results


class WebHistory(HistoryBase):
    """
    Use RESTful API to do searches against archelond.
    """
    SEARCH_URL = '/api/v1/history'

    def __init__(self, url, token):
        """
        Setup requests session with API key and set base
        URL.
        """
        self.url = '{url}{endpoint}'.format(
            url=url.rstrip('/'),
            endpoint=self.SEARCH_URL
        )
        self.session = requests.Session()
        self.session.headers = {'Authorization': 'token {}'.format(token)}

    def search_forward(self, term, page=0):
        """
        Return a list of commmands that is in forward
        time order. i.e oldest first.
        """
        try:
            response = self.session.get(
                self.url,
                params={'q': term, 'p': page}
            )
        except requests.exceptions.ConnectionError:
            print('Failed to connect to server, check settings')
            sys.exit(1)

        if response.status_code != 200:
            return ['Error in API Call {}'.format(response.text)]
        return [x['command'] for x in response.json()['commands']]

    def search_reverse(self, term, page=0):
        """
        Make request to API with sort order specified
        and return the results as a list.
        """
        try:
            response = self.session.get(
                self.url,
                params={'q': term, 'o': 'r', 'p': page}
            )
        except requests.exceptions.ConnectionError:
            print('Failed to connect to server, check settings')
            sys.exit(1)

        if response.status_code != 200:
            return ['Error in API Call {}'.format(response.text)]
        return [x['command'] for x in response.json()['commands']]

    def add(self, command):
        """
        Post a command to the remote server using the API
        """
        try:
            response = self.session.post(
                self.url,
                json={'command': command}
            )
        except requests.exceptions.ConnectionError:
            print('Failed to connect to server, check settings')
            sys.exit(1)

        if response.status_code != 201:
            return False, (response.json(), response.status_code)
        else:
            return True, None

    def bulk_add(self, commands):
        """
        Post a list of commands
        """
        response = self.session.post(
            self.url,
            json={'commands': commands}
        )
        if response.status_code != 200:
            return False, (response.json(), response.status_code)
        else:
            return True, (response.json(), response.status_code)

    def all(self, page):
        """
        Return the entire data set available, one page at a time
        """
        try:
            response = self.session.get(
                self.url,
                params={'p': page}
            )
        except requests.exceptions.ConnectionError:
            print('Failed to connect to server, check settings')
            sys.exit(1)

        if response.status_code != 200:
            return ['Error in API Call {}'.format(response.text)]
        return [x['command'] for x in response.json()['commands']]
