# -*- coding: utf-8 -*-
"""
Command line entry points for the archelon client.
"""
from __future__ import print_function
import os
import subprocess
import sys

from archelonc.search import Search
from archelonc.data import WebHistory


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


def import_history():
    """
    Import current shell's history into server
    """
    # Check if we are pointed at an archelond server
    url = os.environ.get('ARCHELON_URL')
    token = os.environ.get('ARCHELON_TOKEN')
    if not (url and token):
        print(
            'You must specify an ARCHELON server in the environment with '
            '`ARCHELON_URL` and `ARCHELON_TOKEN` environment variables'
        )
        sys.exit(1)
    web_history = WebHistory(url, token)

    # Read history and post to server.  if arg[1]
    # is given, use that file as the history file.
    hist_file = '~/.bash_history'
    if len(sys.argv) == 2:
        hist_file = sys.argv[1]

    with open(os.path.expanduser(hist_file)) as history_file:
        commands = {}
        for line in history_file:
            command = line.strip()
            if not command:
                continue
            commands[command] = None
        success, response = web_history.bulk_add(commands.keys())
        if not success:
            print('Failed to add commands, got:\n {}'.format(
                response
            ))
