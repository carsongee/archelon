# -*- coding: utf-8 -*-
"""
Command line entry points for the archelon client.
"""
from __future__ import print_function
from difflib import Differ
import os
import shutil
import sys

from archelonc.search import Search
from archelonc.data import WebHistory, ArcheloncConnectionException

LARGE_UPDATE_COUNT = 50
HISTORY_FILE = os.path.expanduser('~/.archelon_history')
UNCONFIGURED_ERROR = ("Archelon isn't configured for Web history,"
                      " check `ARCHELON_URL` and `ARCHELON_TOKEN`"
                      " environment variables.")


def _get_web_setup():
    """
    either get a WebHistory object or None if we aren't configured for
    one.
    """
    # Check if we are pointed at an archelond server
    url = os.environ.get('ARCHELON_URL')
    token = os.environ.get('ARCHELON_TOKEN')
    if not (url and token):
        return None
    return WebHistory(url, token)


def search_form():
    """
    Entry point to search history
    """
    Search().run()


def update():
    """
    Capture diff between stored history and new history and upload
    the delta.
    """
    web_history = _get_web_setup()
    # If we aren't setup for Web usage, just bomb out.
    if not web_history:
        print(UNCONFIGURED_ERROR)
        sys.exit(1)

    current_hist_file = os.path.expanduser(
        os.environ.get('HISTFILE', '~/.bash_history')
    )
    # Create our diff file if it doesn't exist
    if not os.path.exists(HISTORY_FILE):
        open(HISTORY_FILE, 'a').close()

    # Compare the current history to our previously stored one,
    # upload any additions and copy the file over.
    commands = {}
    with open(HISTORY_FILE) as cached, open(current_hist_file) as current:
        differ = Differ()
        results = differ.compare(cached.readlines(), current.readlines())

        # use diff lib "codes" to see if we need to upload differences
        for diff in results:
            if diff[:2] == '+ ' or diff[:2] == '? ':
                if diff[2:-1]:
                    commands[diff[2:-1]] = None

    # Warn if we are doing a large upload
    num_commands = len(commands.keys())
    if num_commands > LARGE_UPDATE_COUNT:
        print('Beginning upload of {} history items. '
              'This may take a while...'.format(num_commands))

    try:
        success = True
        commands = [x for x in commands.keys() if x]
        # To ease testing, sort commands
        commands.sort()
        if len(commands) > 0:
            success, response = web_history.bulk_add(
                commands
            )
    except ArcheloncConnectionException as ex:
        print(ex)
        sys.exit(1)
    if not success:
        print('Failed to add commands, got:\n {}'.format(
            response
        ))
        sys.exit(2)
    shutil.copy(current_hist_file, HISTORY_FILE)


def import_history():
    """
    Import current shell's history into server
    """
    web_history = _get_web_setup()
    if not web_history:
        print(UNCONFIGURED_ERROR)
        sys.exit(1)

    # Read history and post to server.  if arg[1]
    # is given, use that file as the history file.
    hist_file = os.environ.get('HISTFILE', '~/.bash_history')
    if len(sys.argv) == 2:
        hist_file = sys.argv[1]

    hist_file_path = os.path.expanduser(hist_file)
    with open(hist_file_path) as history_file:
        commands = {}
        for line in history_file:
            command = line.strip()
            if not command:
                continue
            commands[command] = None
    try:
        success, response = web_history.bulk_add(commands.keys())
    except ArcheloncConnectionException as ex:
        print(ex)
        sys.exit(1)

    if not success:
        print('Failed to add commands, got:\n {}'.format(
            response
        ))
    # Make copy of imported history so we only have to track
    # changes from here on out when archelon is invoked
    shutil.copy(hist_file_path, HISTORY_FILE)


def export_history():
    """
    Pull all remote history down into a file specified or stdout if
    none is specified
    """
    web_history = _get_web_setup()
    if not web_history:
        print(UNCONFIGURED_ERROR)
        sys.exit(1)
    output_file = sys.stdout
    stdout = True
    if len(sys.argv) == 2:
        output_file = open(sys.argv[1], 'w')
        stdout = False
    page = 0
    try:
        results = web_history.all(page)
    except ArcheloncConnectionException as ex:
        print(ex)
        sys.exit(1)
    output_file.write('\n'.join(results))
    while len(results) > 0:
        page += 1
        results = web_history.all(page)
        output_file.write('\n'.join(results))
    if not stdout:
        output_file.close()
