"""
Abstract base class for data stores
"""
from abc import ABCMeta, abstractmethod


class HistoryData(object):
    """Abstract Data storage for command history

    Abstract class implementation of a database for use with command
    history.  Generally a command data item needs just two things, an
    ID and the command itself.  It also needs order.  See the
    :py:class:`archelond.data.MemoryData` class as the simplest
    structure using an :py:class:`collections.OrderedDict`.

    An ID can be any string, and the concrete implementation of
    :py:class:`HistoryData` is responsible for type casting it if
    needed.

    It is also required implicitly that there is only one entry
    per command.  Thus ``add`` ing the same command multiple times
    should result in the return of just one command when filtered
    by a term equal to that command.

    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, config):
        """Setup and configuration of data storage.

        Any connections and configuration of the data store should be
        done here. It receives the full flask configuration
        dictionary.

        Args:
            config (dict): The flask application configuration
                dictionary.
        """
        self.config = config

    @abstractmethod
    def add(self, command, username, host, **kwargs):
        """Add or update a command

        Save (update or create) a command to the data store.

        Args:
            command (str): The command to store
            username (str): The username of the person adding it
            host (str): The IP address of API caller
        Returns:
            Command ID (str): The id of the command stored
        """
        pass  # pragma: no cover

    @abstractmethod
    def delete(self, command_id, username, host, **kwargs):
        """Delete a command

        Remove a command from the data store, raise a KeyError
        if it is not available to be deleted.

        Args:
            command_id (str): Unique command identifier
            username (str): The username of the person adding it
            host (str): The IP address of API caller
        """
        pass  # pragma: no cover

    @abstractmethod
    def get(self, command_id, username, host, **kwargs):
        """Get a single command

        Retrieve a single command by username and id. Raise a
        KeyError if the command does not exist.

        Args:
            command_id (str): Unique command identifier
            username (str): The username of the person adding it
            host (str): The IP address of API caller

        Returns:
            Command (dict): Dictionary with at least the keys ``id``
                            and ``command``
        """
        pass  # pragma: no cover

    @abstractmethod
    def all(self, order, username, host, **kwargs):
        """Unfiltered but ordered command history

        Return the full data set as a list of dict structures
        in the specified order.

        Args:
            order (str): An ordering from :py:const:`ORDER_TYPES`
            username (str): The username of the person adding it
            host (str): The IP address of API caller

        Returns:

            list: A list of dictionaries where each dictionary must
                have at least a ``command`` key and an ``id`` key.
        """
        pass  # pragma: no cover

    @abstractmethod
    def filter(self, term, order, username, host, **kwargs):
        """Get a filtered by term and ordered command history

        Args:
            term (str): The term being searched for/filtered by.
            order (str): An ordering from :py:const:`ORDER_TYPES`
            username (str): The username of the person adding it
            host (str): The IP address of API caller

        Returns:

            list: A list of dictionaries where each dictionary must
                have at least a ``command`` key and an ``id`` key.
        """
        pass  # pragma: no cover
