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
Similarity index module.

Sample usage::

    from pysimsearch.sim_index import SimpleMemorySimIndex
    from pysimsearch import doc_reader

    sim_index = SimpleMemorySimIndex()
    sim_index.index_filenames('http://www.stanford.edu/',
                              'http://www.berkeley.edu',
                              'http://www.ucla.edu',
                              'http://www.mit.edu')
    print(sim_index.postings_list('university'))
    print(list(sim_index.docnames_with_terms('university', 'california')))
    
    sim_index.set_query_scorer('simple_count')
    print(list(sim_index.query_by_string("stanford university")))

'''

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import abc
from collections import defaultdict
import cPickle as pickle
import heapq
import io
import itertools
import operator
from pprint import pprint
import sys
import types

import jsonrpclib as rpclib

from . import doc_reader
from . import query_scorer
from . import term_vec
from .exceptions import *
from .query_scorer import QueryScorer

class SimIndex(object):
    '''
    Base class for similarity indexes
    
    Defines interface as well as provides default implementation for
    several methods.
    
    Instance Attributes:
        config: dictionary of configuration variables
        
    '''

    __metaclass__ = abc.ABCMeta
    
    def __init__(self):
        self.config = {
            'lowercase': True
        }
        self.query_scorer = None

    def update_config(self, **config):
        '''Update any configuration variables'''
        self.config.update(config)
        
    def set_query_scorer(self, query_scorer):
        '''Set the query_scorer
        
        Params:
            query_scorer: if string type, we assume it is a scorer name,
                          else we assume it is itself a scoring object.
        '''
        if isinstance(query_scorer, basestring):
            self.query_scorer = QueryScorer.make_scorer(query_scorer)
        else:
            self.query_scorer = query_scorer

    @abc.abstractmethod
    def index_files(self, named_files):
        '''
        Adds collection given in named_files to the index.
        named_files is an iterable of (filename, file) pairs.
        
        Takes ownership of (and consumes) named_files
        '''
        return

    def index_filenames(self, *filenames):
        '''
        Build a similarity index over files given by filenames
        (Convenience method that wraps index_files())
        '''
        return self.index_files(zip(filenames,
                                    doc_reader.get_text_files(*filenames)))

    def index_string_buffers(self, named_string_buffers):
        '''
        Adds collection of string buffers given in named_string_buffers
        to the index.
        
        Params:
            named_string_buffers: iterable of (name, string) tuples
            
        '''
        named_files = []
        for (name, string_buffer) in named_string_buffers:
            if isinstance(string_buffer, str):
                string_buffer = unicode(string_buffer)
            named_files.append((name, io.StringIO(string_buffer)))
        self.index_files(named_files)
        
    @abc.abstractmethod
    def docid_to_name(self, docid):
        '''Returns document name for a given docid'''
        return
        
    @abc.abstractmethod
    def name_to_docid(self, name):
        '''Returns docid for a given document name'''
        return

    @abc.abstractmethod
    def postings_list(self, term):
        '''
        Return list of (docid, frequency) tuples for docs that contain term
        '''
        return
    
    def docids_with_terms(self, terms):
        '''Returns a list of docids of docs containing terms'''
        docs = None  # will hold a set of matching docids
        for term in terms:
            if docs is None:
                docs = set((x[0] for x in self.postings_list(term)))
            else:
                docs.intersection_update(
                    (x[0] for x in self.postings_list(term)))
                
        # return sorted list
        return sorted(docs)
    
    def docnames_with_terms(self, *terms):
        '''Returns an iterable of docnames containing terms'''
        return (self.docid_to_name(docid) for docid in self.docids_with_terms(terms))
        
    @abc.abstractmethod
    def query(self, query_vec):
        '''
        Finds documents similar to query_vec
        
        Params:
            query_vec: term vector representing query document
        
        Returns:
            A iterable of (docname, score) tuples sorted by score
        '''
        return
    
    def query_by_string(self, query_string):
        '''Finds documents similar to query_string.
        
        Convenience method that calls self.query()
        '''
        if isinstance(query_string, str):
            query_string = unicode(query_string)
        return self.query(doc_reader.term_vec_from_string(query_string))

class SimpleMemorySimIndex(SimIndex):
    '''
    Simple implementation of SimIndex using in-memory data structures.
    (Not meant to scale to large datasets)
    '''

    def __init__(self):
        super(SimpleMemorySimIndex, self).__init__();
        
        self.name_to_docid_map = {}
        self.docid_to_name_map = {}
        self.term_index = defaultdict(list)
        self.N = 0

        # additional stats used for scoring
        self.df_map = defaultdict(int)
        self.doc_len_map = defaultdict(int)
        
        # these are global stats, which is present, are used instead
        # of the local stats above
        self.global_df_map = None
        self.global_N = None

    def set_global_df_map(self, df_map):
        self.global_df_map = defaultdict(int, df_map)
        
    def get_local_df_map(self):
        return dict(self.df_map)
    
    def get_df_map(self):
        return self.global_df_map or self.df_map
    
    def set_global_N(self, N):
        self.global_N = N
    
    def get_local_N(self):
        return self.N
    
    def get_N(self):
        return self.global_N or self.N

    def get_name_to_docid_map(self):
        return self.name_to_docid_map
    
    def index_files(self, named_files):
        '''
        Build a similarity index over collection given in named_files
        named_files is a list iterable of (filename, file) pairs
        '''
        for (name, _file) in named_files:
            with _file as file:
                docid = self.N
                self.name_to_docid_map[name] = docid
                self.docid_to_name_map[docid] = name
                t_vec = doc_reader.term_vec(file)
                for term in t_vec:
                    self.df_map[term] += 1
                self._add_vec(docid, t_vec)
                self.doc_len_map[docid] = term_vec.l2_norm(t_vec)
                self.N += 1

    def _add_vec(self, docid, term_vec):
        '''Add term_vec to the index'''
        for (term, freq) in term_vec.iteritems():
            if self.config['lowercase']:
                term = term.lower()
            self.term_index[term].append((docid, freq))

    def docid_to_name(self, docid):
        return self.docid_to_name_map[docid]
        
    def name_to_docid(self, name):
        return self.name_to_docid_map[name]

    def postings_list(self, term):
        '''
        Returns list of (docid, freq) tuples for documents containing term
        '''
        if self.config['lowercase']:
            term = term.lower()
        return self.term_index[term]
        
    def query(self, query_vec):
        '''
        Finds documents similar to query_vec
        
        Params:
            query_vec: term vector representing query document
        
        Returns:
            A iterable of (docname, score) tuples sorted by score
        '''
        
        postings_lists = [(term, self.postings_list(term))
            for term in query_vec]
        
        hits = self.query_scorer.score_docs(query_vec = query_vec,
                                            postings_lists = postings_lists,
                                            N = self.get_N(),
                                            df_map = self.get_df_map(),
                                            doc_len_map = self.doc_len_map)
        
        return ((self.docid_to_name(docid), score) for (docid, score) in hits)
        
    def save(self, file):
        '''
        Saved index to file
        '''
        # pickle won't let us save query_scorer
        qs = self.query_scorer
        self.query_scorer = None
        pickle.dump(self, file)
        self.query_scorer = qs
        
    @staticmethod
    def load(file):
        '''
        Static method that returns a SimpleMemorySimIndex loaded from file
        '''
        return pickle.load(file)
        
    
class RemoteSimIndex(object):
    '''Proxy to a remote SimIndex'''
    
    def __init__(self, server_url):
        # can't import at top level because of circular dependency
        from . import sim_server
        self.PREFIX = sim_server.SimIndexService.PREFIX
        self.EXPORTED_METHODS = sim_server.SimIndexService.EXPORTED_METHODS
        self._server = rpclib.Server(server_url)
        
    def __getattr__(self, name):
        if name in self.EXPORTED_METHODS:
            func = getattr(self._server,
                           self.PREFIX + '.' + name)
            return func
    
class SimIndexCollection(SimIndex):
    '''
    Provides a SimIndex view over a sharded collection of SimIndexes
    
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
    '''
    
    def __init__(self):
        super(SimIndex, self).__init__()
        self.shards = []
        self.shard_func = self.default_shard_func
        self.name_to_docid_map = {}
        self.docid_to_name_map = {}

    def clear_shards(self):
        self.shards = []
        
    def add_shards(self, *sim_index_shards):
        self.shards.extend(sim_index_shards)
        
    def default_shard_func(self, shard_key):
        '''implements the default sharding function'''
        return hash(shard_key) % len(self.shards)
        
    def set_shard_func(self, func):
        self.shard_func = func

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
        
        self.update_global_stats()
        
    def index_string_buffers(self, named_string_buffers):
        '''
        Routes index_string_buffers() call to appropriate shard.
        '''
        # minimize rpcs by collecting (name, buffer) tuples for
        # different shards up-front
        sharded_input_map = defaultdict(list)
        for (name, buffer) in named_string_buffers:
            sharded_input_map[self.shard_func(name)].append((name, buffer))

        # issue an indexing rpc to each sharded backend that has some input
        for shard_id in sharded_input_map:
            self.shards[shard_id].index_string_buffers(
                sharded_input_map[shard_id]
            )
            
        self.update_global_stats()
        
    def index_urls(self, *urls):
        '''
        We expose this as a separate api, so that backends can fetch
        and index urls themselves.
        
        In contrast, index_files()/index_filenames() will read/collect data
        centrally, then dispatch fully materialized input data to backends
        for indexing.
        '''
        # minimize rpcs by collecting (name, buffer) tuples for
        # different shards up-front
        sharded_input_map = defaultdict([])
        for url in urls:
            sharded_input_map[self.shard_func(url)].append(url)

        # issue an indexing call to each sharded backend that has some input
        for shard_id in sharded_input_map:
            self.shards[shard_id].index_filenames(
                *sharded_input_map[shard_id]
            )
            
        self.update_global_stats()

    @staticmethod
    def make_global_docid(shard_id, docid):
        return "{}-{}".format(shard_id, docid)
            
    
    def docid_to_name(self, docid):
        '''Translates global docid to name'''
        return self.docid_to_name_map[docid]
    
    def name_to_docid(self, name):
        '''Translates name to global docid'''
        return self.name_to_docid_map[name]
    
    def postings_list(self, term):
        '''Returns aggregated postings list in terms of global docids'''

        postings_lists = []
        for shard_id in range(len(self.shards)):
            postings_lists.extend(
                 [(self.make_global_docid(shard_id, docid), freq) for
                  (docid, freq) in self.shards[shard_id].postings_list(term)]
                )
        
        return postings_lists
    
    def set_query_scorer(self, query_scorer):
        '''Passes request to all shards.
        
        Note: if any backends are remote, query_scorer needs to be a
        scorer name, rather than a scorer object (which we currently
        can't serialize for an rpc)
        '''
        for shard in self.shards:
            shard.set_query_scorer(query_scorer)
            
    def query(self, query_vec):
        '''
        Issues query to collection and merges results
        
        TODO: use a merge alg. (heapq.merge doesn't have a key= arg yet)
        '''
        results = []
        for shard in self.shards:
            results.extend(shard.query(query_vec))
        results.sort(key=operator.itemgetter(1), reverse=True)
        return results

    def update_global_stats(self):
        '''
        Fetches local stats from all shards, aggregates them, and
        rebroadcasts global stats back to shards.  Currently uses
        "brute-force"; incremental updating (in either direction)
        is not supported.
        '''
        
        def merge_df_map(target, source):
            '''
            Helper function to merge df_maps.
            Target must be a defaultdict(int)
            '''
            for (term, df) in source.items():
                target[term] += df

        # Collect global stats
        global_N = 0
        global_df_map = defaultdict(int)
        name_to_docid_maps = {}
        for shard_id in range(len(self.shards)):
            shard = self.shards[shard_id]
            global_N += shard.get_local_N()
            merge_df_map(global_df_map, shard.get_local_df_map())
            name_to_docid_maps[shard_id] = shard.get_name_to_docid_map()
            
        # Broadcast global stats
        for shard in self.shards:
            shard.set_global_N(global_N)
            shard.set_global_df_map(dict(global_df_map))

        # Update our name <-> global_docid mapping
        for (shard_id, name_to_docid_map) in name_to_docid_maps.iteritems():
            for (name, docid) in name_to_docid_map.iteritems():
                gdocid = self.make_global_docid(shard_id, docid)
                self.name_to_docid_map[name] = gdocid
                self.docid_to_name_map[gdocid] = name
