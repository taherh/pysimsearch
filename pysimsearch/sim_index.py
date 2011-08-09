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
    sim_index.index_files(
        doc_reader.get_named_text_files('http://www.stanford.edu/',
                                        'http://www.berkeley.edu',
                                        'http://www.ucla.edu',
                                        'http://www.mit.edu'))
    print(sim_index.postings_list('university'))
    print(list(sim_index.docnames_with_terms('university', 'california')))
    
    sim_index.set_query_scorer(query_scorer.SimpleCountQueryScorer())
    print(list(sim_index.query(
        doc_reader.term_vec_from_string("stanford university"))))
'''

from __future__ import (division, absolute_import, print_function,
        unicode_literals)

import abc
from collections import defaultdict
import cPickle as pickle
import itertools
import sys

from .exceptions import *
from . import doc_reader
from . import query_scorer
from . import term_vec

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

    query_scorer = None
    
    def update_config(self, **config):
        '''Update any configuration variables'''
        self.config.update(config)
        
    def set_query_scorer(self, query_scorer):
        '''Set the query_scorer'''
        self.query_scorer = query_scorer

    @abc.abstractmethod
    def index_files(self, named_files):
        '''
        Build a similarity index over collection given in named_files
        named_files is an iterable of (filename, file) pairs.
        
        Takes ownership of (and consumes) named_files
        '''
        return

    def index_filenames(self, filenames):
        '''
        Build a similarity index over files given by filenames
        (Convenience method that wraps index_files())
        '''
        return self.index_files(zip(filenames,
                                    doc_reader.get_text_files(filenames)))
    
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
    
    def index_files(self, named_files):
        '''
        Build a similarity index over collection given in named_files
        named_files is an iterable of (filename, file) pairs
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
                                            N = self.N,
                                            df_map = self.df_map,
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
        Static method that loads index from disk and returns a
        SimpleMemorySimIndex
        '''
        return pickle.load(file)
        
    