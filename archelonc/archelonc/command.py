# -*- coding: utf-8 -*-
"""
Command line entry points for the archelon client.
"""
from __future__ import absolute_import, unicode_literals
import codecs
from difflib import Differ
import os
import shutil
import sys

from archelonc.search import Search
from archelonc.data import WebHistory, ArcheloncException

LARGE_UPDATE_COUNT = 50
HISTORY_FILE = os.path.expanduser('~/.archelon_history')
UNCONFIGURED_ERROR = ("Archelon isn't configured for Web history,"
                      " check `ARCHELON_URL` and `ARCHELON_TOKEN`"
                      " environment variables.")


def print_b(data):
    """Prints UTF decoded bytes with newline to ``sys.stdout``."""
    data = str(data) + '\n'
    sys.stdout.write(data.encode('UTF-8'))


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
        print_b(UNCONFIGURED_ERROR)
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
    with codecs.open(HISTORY_FILE, encoding='UTF-8') as cached, \
            codecs.open(current_hist_file, encoding='UTF-8') as current:
        differ = Differ()
        results = differ.compare(cached.readlines(), current.readlines())

        # use diff lib "codes" to see if we need to upload differences
        for diff in results:
            if diff[:2] == '+ ' or diff[:2] == '? ':
                if diff[2:-1]:
                    commands[diff[2:-1]] = None

    # Warn if we are doing a large upload
    num_commands = len(list(commands.keys()))
    if num_commands > LARGE_UPDATE_COUNT:
        print_b('Beginning upload of {} history items. '
                'This may take a while...\n'.format(num_commands))

    try:
        success = True
        commands = [x for x in list(commands.keys()) if x]
        # To ease testing, sort commands
        commands.sort()
        if len(commands) > 0:
            success, response = web_history.bulk_add(
                commands
            )
    except ArcheloncException as ex:
        print_b(ex)
        sys.exit(3)
    if not success:
        print_b('Failed to upload commands, got:\n {}'.format(
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
        print_b(UNCONFIGURED_ERROR)
        sys.exit(1)

    # Read history and post to server.  if arg[1]
    # is given, use that file as the history file.
    hist_file = os.environ.get('HISTFILE', '~/.bash_history')
    if len(sys.argv) == 2:
        hist_file = sys.argv[1]

    hist_file_path = os.path.expanduser(hist_file)
    with codecs.open(hist_file_path, encoding='UTF-8') as history_file:
        commands = {}
        for line in history_file:
            command = line.strip()
            if not command:
                continue
            commands[command] = None
    try:
        success, response = web_history.bulk_add(list(commands.keys()))
    except ArcheloncException as ex:
        print_b(ex)
        sys.exit(4)

    if not success:
        print_b('Failed to upload commands, got:\n {}'.format(
            response
        ))
        sys.exit(6)
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
        print_b(UNCONFIGURED_ERROR)
        sys.exit(1)
    # Block below is covered across versions of Python, but report
    # doesn't say that.
    if hasattr(sys.stdout, 'buffer'):  # pragma: no cover
        output_file = sys.stdout.buffer
    else:
        output_file = sys.stdout  # pragma: no cover
    stdout = True
    if len(sys.argv) == 2:
        output_file = open(sys.argv[1], 'wb')
        stdout = False
    page = 0
    try:
        results = web_history.all(page)
    except ArcheloncException as ex:
        print_b(ex)
        sys.exit(5)
    while len(results) > 0:
        output_file.write('\n'.join(results).encode('UTF-8'))
        output_file.write('\n'.encode('UTF-8'))
        page += 1
        results = web_history.all(page)
    if not stdout:
        output_file.close()
