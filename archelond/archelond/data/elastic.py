"""
ElasticSearch implementation of the data store.  Currently the
recommended default data store.
"""

from datetime import datetime
import hashlib
import logging

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import (
    RequestError, NotFoundError, ConnectionError
)
import pytz

from archelond.data.abstract import HistoryData

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


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
        # Analyzer is setup such that every single character can
        # be part of the search query
        self.index = self.config['ELASTICSEARCH_INDEX']
        # pylint: disable=unexpected-keyword-arg
        self.elasticsearch.indices.create(
            index=self.index, ignore=400,
            body={
                'settings': {
                    'analysis': {
                        'analyzer': {
                            'command_analyzer': {
                                'tokenizer': 'keyword',
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

    def add(self, command, username, host, **kwargs):
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
        # Add kwargs to meta key in document
        document['meta'] = kwargs
        result = self.elasticsearch.index(
            index=self.index, doc_type=doc_type, id=doc_id, body=document
        )
        log.debug(result)
        return doc_id

    def delete(self, command_id, username, host, **kwargs):
        """
        Remove item from elasticsearch
        """
        try:
            self.elasticsearch.delete(
                self.index, self._doc_type(username), command_id
            )
        except NotFoundError:
            raise KeyError

    def get(self, command_id, username, host, **kwargs):
        """
        Pull one command out of elasticsearch
        """
        try:
            hit = self.elasticsearch.get(
                self.index, command_id, self._doc_type(username)
            )
        except NotFoundError:
            raise KeyError
        result = hit['_source']
        result['id'] = hit['_id']
        return result

    def all(self, order, username, host, page=0, **kwargs):
        """
        Just build a body with match all and return filter
        """
        body = {
            "query": {
                "match_all": {}
            }
        }
        return self.filter(None, order, username, host, body, page)

    def filter(self, term, order, username, host, body=None, page=0, **kwargs):
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
            # pylint: disable=unexpected-keyword-arg
            results = self.elasticsearch.search(
                index=self.index, doc_type=doc_type, size=self.NUM_RESULTS,
                body=body, sort=sort, from_=self.NUM_RESULTS*page
            )
        except (ConnectionError, RequestError) as ex:
            log.exception(ex)
            return []
        log.debug(results)
        log.debug('Got %s hits for %s', results['hits']['total'], term)
        results_list = []
        for hit in results['hits']['hits']:
            result = hit['_source']
            result['id'] = hit['_id']
            result['score'] = hit['_score']
            results_list.append(result)
        return results_list
