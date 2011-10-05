#!/usr/bin/env python

# Copyright (c) 2011, Taher Haveliwala <oss@taherh.org>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#         * Redistributions of source code must retain the above copyright
#           notice, this list of conditions and the following disclaimer.
#         * Redistributions in binary form must reproduce the above copyright
#           notice, this list of conditions and the following disclaimer in the
#           documentation and/or other materials provided with the distribution.
#         * The names of project contributors may not be used to endorse or
#           promote products derived from this software without specific
#           prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


'''
SimIndexCollection

Sample usage::

    from pprint import pprint
    from pysimsearch.sim_index import MemorySimIndex, SimIndexCollection

    indexes = (MemorySimIndex(), MemorySimIndex())
    index_coll = SimIndexCollection()
    index_coll.add_shards(*indexes)
    index_coll.set_query_scorer('tfidf')
    index_coll.index_urls('http://www.stanford.edu/',
                          'http://www.berkeley.edu',
                          'http://www.ucla.edu',
                          'http://www.mit.edu')
    
    pprint(index_coll.query('stanford university'))

'''

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from collections import defaultdict
import operator
import os

from . import SimIndex
from ..exceptions import *

class SimIndexCollection(SimIndex):
    '''
    Inherits from :class:`pysimsearch.sim_index.SimIndex`.
    
    Provides a :class:`SimIndex` view over a sharded collection of SimIndexes.
    
    Useful with collections of remote SimIndexes to provide a
    distributed indexing and serving architecture.
    
    Assumes document-level sharding:
    
      - ``query()`` requests are routed to all shards in collection.
      - ``index_files()`` requests are routed according to a sharding function
    
    Note that if we had used query-sharding, then instead, queries would
    be routed using a sharding function, and index-requests would be
    routed to all shards.  The two sharding approaches correspond to either
    partitioning the postings matrix by columns (doc-sharding),
    or rows (query-sharding).
    
    The shard-function is only used for ``index_*()`` operations.  If you
    have a read-only collection, you don't need a sharding function.
    '''
    
    def __init__(self, shards=(), root=True):
        super(SimIndexCollection, self).__init__()

        self._shards = []
        self.shard_func = self.default_shard_func
        self._name_to_docid_map = {}
        self._docid_to_name_map = {}
        self._df_map = {}
        
        self._dirty = False
        
        self.set_config('root', root, passthrough=False)
        
        if shards:
            self.add_shards(*shards)

    def set_config(self, key, value, passthrough=True):
        '''Update config var for shards'''
        super(SimIndexCollection, self).set_config(key, value)
        if passthrough:
            for shard in self._shards:
                shard.set_config(key, value)
            
    def update_config(self, passthrough=True, **d):
        '''Update config for shards'''
        super(SimIndexCollection, self).update_config(**d)
        if passthrough:
            for shard in self._shards:
                shard.update_config(**d)

    def clear_shards(self):
        self._shards = []
        
    def add_shards(self, *sim_index_shards):
        for shard in sim_index_shards:
            shard.update_config(**self._config)
        self._shards.extend(sim_index_shards)
        self.update_trigger_helper()
    
    _salt = None
    def default_shard_func(self, shard_key):
        '''implements the default sharding function'''
        if self._salt is None:
            self._salt = os.urandom(4)
        return hash(str(shard_key)+self._salt) % len(self._shards)
        
    def set_shard_func(self, func):
        self._shard_func = func

    def set_global_N(self, N):
        for shard in self._shards:
            shard.set_global_N(N)

    def set_global_df_map(self, df_map):
        for shard in self._shards:
            shard.set_global_df_map(df_map)
        
    def get_local_df_map(self):
        return self._df_map
    
    def get_name_to_docid_map(self):
        return self._name_to_docid_map

    def update_trigger(method):
        '''
        Decorator for methods that update the index.  Used as a post-update
        trigger that gathers new term stats, and propagates them back down (if
        we're the root node)
        '''
        def wrapper(self, *args, **kwargs):
            self._dirty = True
            val = method(self, *args, **kwargs)
            if self._dirty:
                self.update_trigger_helper()
                self._dirty = False
        
        return wrapper

    @update_trigger
    def index_files(self, named_files):
        '''
        Translate to index_string_buffers() call, since file objects
        can't be serialized for rpcs to backends.  Note: we
        currently read in all files in memory, and make one call to
        index_string_buffers() -- this can be memory-intesive
        if named_files represents a large number of files.
        
        TODO: read in files in smaller batches, and then make mutiple
        calls to index_string_buffers().
        '''
        named_string_buffers = [(name, file.read())
            for (name, file) in named_files]
        self.index_string_buffers(named_string_buffers)

    @update_trigger
    def index_string_buffers(self, named_string_buffers):
        '''Routes index_string_buffers() call to appropriate shard.'''
        # minimize rpcs by collecting (name, buffer) tuples for
        # different shards up-front
        sharded_input_map = defaultdict(list)
        for (name, buffer) in named_string_buffers:
            sharded_input_map[self.shard_func(name)].append((name, buffer))

        # issue an indexing rpc to each sharded backend that has some input
        # TODO: use non-blocking rpc's
        for shard_id in sharded_input_map:
            self._shards[shard_id].index_string_buffers(
                sharded_input_map[shard_id]
            )

    @update_trigger
    def index_urls(self, *urls):
        '''Index web pages given by urls'''
        # minimize rpcs by collecting (name, buffer) tuples for
        # different shards up-front
        sharded_input_map = defaultdict(list)
        for url in urls:
            sharded_input_map[self.shard_func(url)].append(url)

        # Issue an indexing call to each sharded backend that has some input
        # Generally the sharded servers should be backed with
        # ConcurrentSimIndexes so that the index_urls() call will generally
        # be non-blocking.
        for shard_id in sharded_input_map:
            self._shards[shard_id].index_urls(
                *sharded_input_map[shard_id]
            )

    @update_trigger
    def del_docids(self, *docids):
        '''Delete docid from index collection'''

        sharded_del_map = defaultdict(list)
        for docid in docids:
            # make sure we have a compound docid
            assert '-' in docid
            (shard_id, sep, remote_docid) = docid.partition('-')
            shard_id = int(shard_id)
            # if the remote shard is expected to be a leaf, then cast
            # remote docid to int
            if '-' not in remote_docid:
                remote_docid = int(remote_docid)
            sharded_del_map[shard_id].append(remote_docid)
        
        # propagate the requests the appropriate shard
        for (shard_id, remote_docids) in sharded_del_map.items():
            self._shards[shard_id].del_docids(*remote_docids)
    
    @staticmethod
    def make_node_docid(shard_id, docid):
        return "{}-{}".format(shard_id, docid)
    
    def docid_to_name(self, docid):
        '''Translates node docid to name'''
        return self._docid_to_name_map[docid]
    
    def name_to_docid(self, name):
        '''Translates name to node docid'''
        return self._name_to_docid_map[name]
    
    def postings_list(self, term):
        '''Returns aggregated postings list in terms of global docids'''

        merged_postings_list = []
        for shard_id in range(len(self._shards)):
            merged_postings_list.extend(
                 [(self.make_node_docid(shard_id, docid), freq) for
                  (docid, freq) in self._shards[shard_id].postings_list(term)]
                )
        
        return merged_postings_list
    
    def set_query_scorer(self, query_scorer):
        '''Passes ``set_query_scorer()`` request to all shards.
        
        Params:
            query_scorer: scorer object or name. If any backends are remote,
                          query_scorer needs to be a scorer name, rather than
                          a scorer object (which we currently don't serialize
                          for rpcs)
        '''
        for shard in self._shards:
            shard.set_query_scorer(query_scorer)
            
    def _query(self, query_vec):
        '''Issues query to collection and returns merged results
        
        TODO: use a merge alg. (heapq.merge doesn't have a key= arg yet)
        TODO: add support for rank-aggregation in the case of heterogenous
              collections where ir scores are not directly comparable
        '''
        results = []
        for shard in self._shards:
            results.extend(shard.query(query_vec))
        results.sort(key=operator.itemgetter(1), reverse=True)
        return results

    def update_trigger_helper(self):
        self.update_node_stats()

        # If we're the root of the collection, then propogate back node
        # stats (which are global stats) to children.  Else some ancestor
        # node will have that responsibility.
        if self.config('root'):
            self.broadcast_node_stats()

    def update_node_stats(self):
        '''
        Fetches local stats from all shards, aggregates them, and
        rebroadcasts global stats back to shards.  Currently uses
        "brute-force"; incremental updating (in either direction)
        is not supported.
        '''

        def merge_df_map(target, source):
            '''
            Helper function to merge df_maps.
            '''
            for (term, df) in source.items():
                if term not in target: target[term] = 0
                target[term] += df

        # Collect global stats
        self._N = 0
        self._df_map = {}
        name_to_docid_maps = {}
        for shard_id in range(len(self._shards)):
            shard = self._shards[shard_id]
            self._N += shard.get_local_N()
            merge_df_map(self._df_map, shard.get_local_df_map())
            name_to_docid_maps[shard_id] = shard.get_name_to_docid_map()

        # Update our name <-> node_docid mapping
        for (shard_id, name_to_docid_map) in name_to_docid_maps.iteritems():
            for (name, docid) in name_to_docid_map.iteritems():
                gdocid = self.make_node_docid(shard_id, docid)
                self._name_to_docid_map[name] = gdocid
                self._docid_to_name_map[gdocid] = name

    def broadcast_node_stats(self):  
        # Broadcast global stats.  Only called by collection root node.
        for shard in self._shards:
            shard.set_global_N(self._N)
            shard.set_global_df_map(self._df_map)

