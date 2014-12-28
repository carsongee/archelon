"""
Data modeling for shell history
"""
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from datetime import datetime
import hashlib
import logging

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError
import pytz


ORDER_TYPES = [
    'r',  # reverse
]

log = logging.getLogger(__name__)

class HistoryData(object):
    """
    Abstract class implementation of a database for use with
    command history.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, config):
        """
        The flask application configuration gets
        passed in to all HistoryData classes
        """
        self.config = config

    @abstractmethod
    def add(self, command, username, host, **kwargs):
        """
        Save (update or create) a command to history.
        """
        pass

    @abstractmethod
    def all(self, order, username, host, **kwargs):
        """
        Return the full data set in the list of dict structure
        in the specified order
        """
        pass

    @abstractmethod
    def filter(self, term, order, username, host, **kwargs):
        """
        Return a list of dictionaries with at least the
        'command' key ordered as requested by string
        """
        pass


class MemoryData(HistoryData):
    """
    A quick in memory deduplicated structure for standalone testing
    and development.
    """
    INITIAL_DATA = OrderedDict(
        [
            ('cd', {}),
            ('pwd', {}),
            ('echo hi', {}),
            ('cat /proc/cpuinfo', {}),
        ]
    )

    def __init__(self, config):
        """
        Initialize internal data structure with init data
        """
        super(MemoryData, self).__init__(config)
        self.data = self.INITIAL_DATA

    def add(self, command, username, host):
        """
        Append item to data list
        """
        self.data['command'] = {
            'username': username,
            'host': host,
            'timestamp': datetime.utcnow().replace(tzinfo=pytz.utc),
        }

    def all(self, order, username, host, **kwargs):
        """
        Simply rewrap the data structure, order,  and return
        """
        return self.filter(None, order, username, host)

    def filter(self, term, order, username, host, **kwargs):
        """
        Return filtered and reversed OrderedDict.
        """
        if order and order == 'r':
            ordered_set = reversed(self.data.items())
        else:
            ordered_set = self.data.items()
        result_list = []
        for command, meta in ordered_set:
            if term is None or term in command:
                meta['command'] = command
                result_list.append(meta)
        return result_list


class ElasticData(HistoryData):
    """
    An ElasticSearch implementation of HistoryData.
    This is what should be used in production
    """
    DOC_TYPE = 'history'
    # Only return a max of 50 results
    NUM_RESULTS = 50

    def __init__(self, config):
        """
        Configure and setup the ES client
        """
        super(ElasticData, self).__init__(config)

        # Connect
        self.elasticsearch = Elasticsearch(
            self.config['ELASTICSEARCH_URL']
        )
        # Create configured index.
        # Analayzer is setup such that every single character can
        # be part of the search query
        self.index = self.config['ELASTICSEARCH_INDEX']
        self.elasticsearch.indices.create(
            index=self.index, ignore=400,
            body={
                'settings' : {
                    'analysis' : {
                        'analyzer' : {
                            'command_analyzer' : {
                                'tokenizer' : 'keyword',
                                'filter': 'lowercase'
                            }
                        }
                    }
                },
                'mappings': {
                    self.index: {
                        'properties': {
                            'command': {
                                'search_analyzer': 'command_analyzer',
                                'index_analyzer': 'command_analyzer',
                                'type': 'string'
                            }
                        }
                    }
                }
            }
        )

    def _doc_type(self, username):
        """
        return doc type for given user
        """
        return '{0}_{1}'.format(username, self.DOC_TYPE)

    @staticmethod
    def _doc_id(command):
        """
        hash the command to make the document id
        """
        return hashlib.sha256(command).hexdigest()

    def add(self, command, username, host):
        """
        Add the command to the index with a time stamp and id
        by hash of the command and append username to doc type
        for user separation of data.
        """
        doc_type = self._doc_type(username)
        doc_id = ElasticData._doc_id(command)
        document = {
            'command': command,
            'username': username,
            'host': host,
            'timestamp': datetime.utcnow().replace(tzinfo=pytz.utc),
        }
        result = self.elasticsearch.index(
            index=self.index, doc_type=doc_type, id=doc_id, body=document
        )
        log.debug(result)

    def all(self, order, username, host, **kwargs):
        """
        Just build a body with match all and return filter
        """
        body = {
            "query": {
                "match_all": {}
            }
        }
        return self.filter(None, order, username, host, body)

    def filter(self, term, order, username, host, body=None, **kwargs):
        """
        Return filtered search that is ordered
        """
        doc_type = self._doc_type(username)
        sort = ''
        if order and order == 'r':
            sort = 'timestamp:desc'
        if not body:
            body = {
                'query': {
                    'match_phrase_prefix': {
                        'command': {
                            'query': term,
                            'max_expansions': self.NUM_RESULTS
                        }
                    }
                }
            }
        # Implicitly we are sorting by score without order set, which
        # is nice
        try:
            results = self.elasticsearch.search(
                index=self.index, doc_type=doc_type, size=self.NUM_RESULTS,
                body=body, sort=sort
            )
        except RequestError, ex:
            log.exception(ex)
            return []
        log.debug(results)
        log.debug('Got %s hits for %s', results['hits']['total'], term)
        results_list = []
        for hit in results['hits']['hits']:
            results_list.append(hit['_source'])
        return results_list
