# -*- coding: utf-8 -*-
"""
Command line entry points for the archelon client.
"""
from __future__ import print_function

from archelonc.search import Search


def search_form():
    """
    Entry point to search history
    """
    Search().run()


def watcher():
    """
    Watch for commands, listen to signals, upload, etc
    """
    print('not implemented')
