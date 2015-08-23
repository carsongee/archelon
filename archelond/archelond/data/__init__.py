"""
Import all known data store implementations
"""
from __future__ import absolute_import, unicode_literals
from archelond.data.elastic import ElasticData
from archelond.data.memory import MemoryData

ORDER_TYPES = [
    'r',  # reverse
]

__all__ = ['ElasticData', 'MemoryData']
