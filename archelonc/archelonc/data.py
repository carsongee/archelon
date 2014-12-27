# -*- coding: utf-8 -*-
"""
Data modeling for command history to be modular
"""
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
import os


class HistoryBase(object):
    """
    Base class of what all backend command history
    searches should use.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def search_reverse(self, term):
        """
        Return a list of dictionaries with at least 'command'
        that is in reverse time order. i.e newest first.
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

    def search_reverse(self, term):
        """
        Return reversed filtered list by term
        """
        results = [
            x for x in self.data
            if term in x
        ]
        results.reverse()
        return results
