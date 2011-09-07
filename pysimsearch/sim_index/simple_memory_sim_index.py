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

import cPickle as pickle

import jsonrpclib as rpclib
#import xmlrpclib as rpclib

from .sim_index import SimIndex
from .. import doc_reader
from .. import term_vec
from ..exceptions import *

class SimpleMemorySimIndex(SimIndex):
    '''
    Simple implementation of the ``SimIndex`` interface using in-memory data
    structures.
    '''

    def __init__(self):
        super(SimpleMemorySimIndex, self).__init__()

        # index data
        self.name_to_docid_map = {}
        self.docid_to_name_map = {}
        self.term_index = {}
        self.docid_to_feature_map = {}  # document level features
        self.N = 0

        # additional stats used for scoring
        self.df_map = {}
        self.doc_len_map = {}
        
        # these are global stats, which is present, are used instead
        # of the local stats above
        self.global_df_map = None
        self.global_N = None
        
        # set a default scorer
        self.set_query_scorer('tfidf')

    def set_global_df_map(self, df_map):
        self.global_df_map = df_map
        
    def get_local_df_map(self):
        return self.df_map
    
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
        for (name, file) in named_files:
            with file:
                t_vec = doc_reader.term_vec(file, self.config('stoplist'))
            docid = self.N
            self.name_to_docid_map[name] = docid
            self.docid_to_name_map[docid] = name
            for term in t_vec:
                if term not in self.df_map: self.df_map[term] = 0
                self.df_map[term] += 1
            self._add_vec(docid, t_vec)
            if docid not in self.doc_len_map: self.doc_len_map[docid] = 0
            self.doc_len_map[docid] = term_vec.l2_norm(t_vec)
            self.N += 1

    def _add_vec(self, docid, term_vec):
        '''Add term_vec to the index'''
        for (term, freq) in term_vec.iteritems():
            if self.config('lowercase'):
                term = term.lower()
            if term not in self.term_index: self.term_index[term] = []
            self.term_index[term].append((docid, freq))

    def docid_to_name(self, docid):
        return self.docid_to_name_map[docid]
        
    def name_to_docid(self, name):
        return self.name_to_docid_map[name]

    def postings_list(self, term):
        '''
        Returns list of (docid, freq) tuples for documents containing term
        '''
        if self.config('lowercase'):
            term = term.lower()

        return self.term_index.get(term, [])
        
    def query(self, query_vec):
        '''Finds documents similar to query_vec
        
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
        '''Saved index to file'''
        # pickle won't let us save query_scorer
        qs = self.query_scorer
        self.query_scorer = None
        pickle.dump(self, file)
        self.query_scorer = qs
        
    @staticmethod
    def load(file):
        '''Returns a ``SimpleMemorySimIndex`` loaded from pickle file'''
        return pickle.load(file)
