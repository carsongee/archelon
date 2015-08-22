# -*- coding: utf-8 -*-
"""
Data modeling for command history to be modular
"""
from __future__ import print_function, absolute_import, unicode_literals
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
import os

import requests
import six


class ArcheloncException(Exception):
    """Base archelonc exception class."""
    pass


class ArcheloncConnectionException(ArcheloncException):
    """Connection exception class."""
    pass


class ArcheloncAPIException(ArcheloncException):
    """API exception occurred."""
    pass


class HistoryBase(six.with_metaclass(ABCMeta, object)):
    """
    Base class of what all backend command history
    searches should use.
    """

    @abstractmethod
    def search_forward(self, term, page=0):
        """
        Return a list of commmands that is in forward
        time order. i.e oldest first.

        If paging is needed, the page parameter is available.
        """
        pass  # pragma: no cover

    @abstractmethod
    def search_reverse(self, term, page=0):
        """
        Return a list of commmands that is in reverse
        time order. i.e newest first.

        If paging is needed, the page parameter is available.
        """
        pass  # pragma: no cover


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
        self.data = list(history_dict.keys())

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

    def _connection_error(self):
        """
        Raise nice connection error message exception.

        Raises:
            ArcheloncConnectionException
        """
        raise ArcheloncConnectionException(
            'Failed to connect to server, check settings '
            '(currently: {url})'.format(url=self.url)
        )

    @staticmethod
    def _api_error(response):
        """
        Raise nice error message for API exception

        Args:
           response (requests.response object): Response that was wrong
        Raises:
            ArcheloncAPIException
        """
        raise ArcheloncAPIException(
            'Error in API Call ({0.status_code}): {0.text}'.format(response)
        )

    def search_forward(self, term, page=0):
        """
        Return a list of commmands that is in forward
        time order. i.e oldest first.

        Raises:
            ArcheloncConnectionException
            ArcheloncAPIException
        """
        try:
            response = self.session.get(
                self.url,
                params={'q': term, 'p': page}
            )
        except requests.exceptions.ConnectionError:
            self._connection_error()

        if response.status_code != 200:
            self._api_error(response)
        return [x['command'] for x in response.json()['commands']]

    def search_reverse(self, term, page=0):
        """
        Make request to API with sort order specified
        and return the results as a list.

        Raises:
            ArcheloncConnectionException
            ArcheloncAPIException
        """
        try:
            response = self.session.get(
                self.url,
                params={'q': term, 'o': 'r', 'p': page}
            )
        except requests.exceptions.ConnectionError:
            self._connection_error()

        if response.status_code != 200:
            self._api_error(response)
        return [x['command'] for x in response.json()['commands']]

    def add(self, command):
        """
        Post a command to the remote server using the API

        Raises:
            ArcheloncConnectionException
            ArcheloncAPIException
        """
        try:
            response = self.session.post(
                self.url,
                json={'command': command}
            )
        except requests.exceptions.ConnectionError:
            self._connection_error()
        if response.status_code != 201:
            self._api_error(response)
        else:
            return True, None

    def bulk_add(self, commands):
        """
        Post a list of commands

        Args:
            commands (list): List of commands to add to server.
        Raises:
            ArcheloncConnectionException
            ArcheloncAPIException
        """
        try:
            response = self.session.post(
                self.url,
                json={'commands': commands}
            )
        except requests.exceptions.ConnectionError:
            self._connection_error()
        if response.status_code != 200:
            self._api_error(response)
        else:
            return True, (response.json(), response.status_code)

    def all(self, page):
        """
        Return the entire data set available, one page at a time

        Raises:
            ArcheloncConnectionException
            ArcheloncAPIException
        """
        try:
            response = self.session.get(
                self.url,
                params={'p': page}
            )
        except requests.exceptions.ConnectionError:
            self._connection_error()

        if response.status_code != 200:
            self._api_error(response)
        return [x['command'] for x in response.json()['commands']]

    def delete(self, command):
        """
        Deletes the command given on the server.

        Raises:
            ArcheloncConnectionException
            ArcheloncAPIException
            ValueError
        Returns:
            None
        """
        # Get the command by ID
        try:
            response = self.session.get(
                self.url,
                params={'q': command}
            )
        except requests.exceptions.ConnectionError:
            self._connection_error()
        if response.status_code != 200:
            self._api_error(response)
        commands = response.json()['commands']
        if len(commands) != 1:
            raise ValueError(
                'More than one command returned by search, cannot delete'
            )
        command_id = commands[0]['id']
        response = self.session.delete(
            '{base_url}/{command_id}'.format(
                base_url=self.url, command_id=command_id
            )
        )
        if response.status_code != 200:
            self._api_error(response)
