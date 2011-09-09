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
SimpleMemorySimIndex module

Sample usage::

    from pprint import pprint
    from pysimsearch.sim_index import SimpleMemorySimIndex
    from pysimsearch import doc_reader

    sim_index = SimpleMemorySimIndex()
    sim_index.index_filenames('http://www.stanford.edu/',
                              'http://www.berkeley.edu',
                              'http://www.ucla.edu',
                              'http://www.mit.edu')
    pprint(sim_index.postings_list('university'))
    pprint(list(sim_index.docnames_with_terms('university', 'california')))
    
    sim_index.set_query_scorer('simple_count')
    pprint(list(sim_index.query_by_string("stanford university")))

'''

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import cPickle as pickle

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

        # index metadata
        self._name_to_docid_map = {}
        self._docid_to_name_map = {}
        self._docid_to_feature_map = {}  # document level features

        # term index
        self._term_index = {}

        # additional stats used for scoring
        self._df_map = {}
        self._doc_len_map = {}
        
        # global stats, which if present, are used instead
        # of the local stats
        self._global_df_map = None
        
        # set a default scorer
        self.set_query_scorer('tfidf')

    def set_global_df_map(self, df_map):
        self._global_df_map = df_map
        
    def get_local_df_map(self):
        return self._df_map
    
    def get_name_to_docid_map(self):
        return self._name_to_docid_map
    
    def get_doc_freq(self, term):
        df_map = self._global_df_map or self._df_map
        return df_map.get(term, 1)
        
    def get_doc_len(self, docid):
        return self._doc_len_map.get(docid, 0)
        
    def index_files(self, named_files):
        '''
        Build a similarity index over collection given in named_files
        named_files is a list iterable of (filename, file) pairs
        '''
        for (name, file) in named_files:
            with file:
                t_vec = doc_reader.term_vec(file, self.config('stoplist'))
            docid = self._N
            self._name_to_docid_map[name] = docid
            self._docid_to_name_map[docid] = name
            for term in t_vec:
                if self.config('lowercase'):
                    term = term.lower()
                if term not in self._df_map: self._df_map[term] = 0
                self._df_map[term] += 1
            self._add_vec(docid, t_vec)
            self._doc_len_map[docid] = term_vec.l2_norm(t_vec)
            self._N += 1

    def _add_vec(self, docid, term_vec):
        '''Add term_vec to the index'''
        for (term, freq) in term_vec.iteritems():
            if self.config('lowercase'):
                term = term.lower()
            if term not in self._term_index: self._term_index[term] = []
            self._term_index[term].append((docid, freq))

    def docid_to_name(self, docid):
        return self._docid_to_name_map[docid]
        
    def name_to_docid(self, name):
        return self._name_to_docid_map[name]

    def postings_list(self, term):
        '''
        Returns list of (docid, freq) tuples for documents containing term
        '''
        if self.config('lowercase'):
            term = term.lower()

        return self._term_index.get(term, [])
        
    def query(self, query_vec):
        '''Finds documents similar to query_vec
        
        Params:
            query_vec: term vector representing query document
        
        Returns:
            A iterable of (docname, score) tuples sorted by score
        '''
        
        postings_lists = []
        for term in query_vec:
            if self.config('lowercase'): term = term.lower()
            postings_lists.append((term, self.postings_list(term)))

        
        N = self._global_N or self._N
        hits = self.query_scorer.score_docs(query_vec=query_vec,
                                            postings_lists=postings_lists,
                                            N=N,
                                            get_doc_freq=self.get_doc_freq,
                                            get_doc_len=self.get_doc_len)
        
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
