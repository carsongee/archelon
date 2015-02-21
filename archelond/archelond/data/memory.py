"""
In memory data store implementation for development and testing
"""
from collections import OrderedDict
from datetime import datetime
import hashlib
import logging

import pytz

from archelond.data.abstract import HistoryData


log = logging.getLogger(__name__)  # pylint: disable=invalid-name


class MemoryData(HistoryData):
    """
    A quick in memory deduplicated structure for standalone testing
    and development.
    """
    INITIAL_DATA = [
        'cd',
        'pwd',
        'echo hi',
        'cat /proc/cpuinfo'
    ]

    def __init__(self, config):
        """
        Initialize internal data structure with init data
        """
        super(MemoryData, self).__init__(config)
        self.data = OrderedDict()
        for item in self.INITIAL_DATA:
            self.add(item, None, None)

    @staticmethod
    def _doc_id(command):
        """
        hash the command to make the id
        """
        return hashlib.sha256(command).hexdigest()

    def add(self, command, username, host, **kwargs):
        """
        Append item to data list
        """
        cmd_id = self._doc_id(command)
        self.data[cmd_id] = {
            'command': command,
            'username': username,
            'host': host,
            'timestamp': datetime.utcnow().replace(tzinfo=pytz.utc),
            'meta': kwargs
        }
        return cmd_id

    def delete(self, command_id, username, host, **kwargs):
        """
        Remove key from internal dictionary
        """
        del self.data[command_id]

    def get(self, command_id, username, host, **kwargs):
        """
        Pull the specified command out of the data store.
        """
        command = self.data[command_id]
        command['id'] = command_id
        return command

    def all(self, order, username, host, page=0, **kwargs):
        """
        Simply rewrap the data structure, order,  and return
        """
        if page != 0:
            return []
        return self.filter(None, order, username, host)

    def filter(self, term, order, username, host, page=0, **kwargs):
        """
        Return filtered and reversed OrderedDict.
        """
        if page != 0:
            return []

        if order and order == 'r':
            ordered_set = reversed(self.data.items())
        else:
            ordered_set = self.data.items()
        result_list = []
        for command_id, meta in ordered_set:
            if term is None or term in meta['command']:
                meta['id'] = command_id
                result_list.append(meta)
        return result_list
