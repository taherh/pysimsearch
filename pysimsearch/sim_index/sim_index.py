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
SimIndex

See :mod:`pysimsearch.sim_index.memory_sim_index` for sample usage

'''

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import abc
import io
import itertools

from .. import doc_reader
from .. import term_vec
from ..exceptions import *
from ..query_scorer import QueryScorer

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
        self._config = {
            'lowercase': True,
            'stoplist': {}  # using dict instead of set, for rpc support
        }
        self.query_scorer = None
        self._N = 0
        self._global_N = None
        self._next_docid = 0

    def config(self, key):
        return self._config[key]

    def set_config(self, key, value):
        self._config[key] = value

    def update_config(self, **d):
        self._config.update(d)
        
    def load_stoplist(self, stopfile):
        stoplist = {}
        for line in stopfile:
            stoplist.update(zip(line.split(), itertools.repeat(1)))
        self.set_config('stoplist', stoplist)

    @abc.abstractmethod
    def set_global_df_map(self, df_map):
        '''Set global df stats'''
        return
    
    @abc.abstractmethod
    def get_local_df_map(self):
        '''Get local df stats'''
        return
    
    @abc.abstractmethod
    def get_name_to_docid_map(self):
        '''Return local mapping of name to docids'''
        return

    def set_global_N(self, N):
        '''Set global number of documents'''
        self._global_N = N
    
    def get_local_N(self):
        '''Return local number of documents'''
        return self._N
        
    def set_query_scorer(self, query_scorer):
        '''Set the query_scorer
        
        Params:
            query_scorer: if string type, we assume it is a scorer name,
                          else we assume it is itself a scoring object
                          of base type :class:`query_scorer.QueryScorer`.
        '''
        if isinstance(query_scorer, basestring):
            self.query_scorer = QueryScorer.make_scorer(query_scorer)
        else:
            self.query_scorer = query_scorer

    @abc.abstractmethod
    def index_files(self, named_files):
        '''Add ``named_files`` to the index
        
        Params:
            named_files: iterable of (filename, file) pairs.
                         Takes ownership of (and consumes) the files.
        '''
        return

    def index_filenames(self, *filenames):
        '''Add ``filenames`` to the index
        
        Convenience method that wraps :meth:`index_files()`
        
        Params:
            ``filenames``: list of filenames to add to the index.
        '''
        return self.index_files(doc_reader.get_text_files(filenames))
        
    def index_urls(self, *urls):
        '''Add ``urls`` to the index
        
        Convenience method that wraps :meth:`index_files()`
        
        Params:
            ``urls``: list of urls of web pages to add to the index.
        '''
        return self.index_files(doc_reader.get_urls(urls))

    def index_string_buffers(self, named_string_buffers):
        '''Add ``named_string_buffers`` to the index
        
        Params:
            named_string_buffers: iterable of (name, string) tuples, where
                                  the string contains the data to index.
            
        '''
        named_files = []
        for (name, string_buffer) in named_string_buffers:
            if isinstance(string_buffer, str):
                string_buffer = unicode(string_buffer)
            named_files.append((name, io.StringIO(string_buffer)))
        self.index_files(named_files)
        
    @abc.abstractmethod
    def del_docids(self, *docids):
        '''Deletes documents corresponding to docids from the index'''
        return
    
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
        '''Returns a list of docids of docs containing all terms'''
        docs = None  # will hold a set of matching docids
        for term in terms:
            if docs is None:
                docs = set((x[0] for x in self.postings_list(term)))
            else:
                docs.intersection_update(
                    (x[0] for x in self.postings_list(term)))
                
        # return sorted list
        if docs is None: docs = []
        return sorted(docs)
    
    def docnames_with_terms(self, *terms):
        '''Returns an iterable of docnames containing terms'''
        if self.config('lowercase'):
            terms = [term.lower() for term in terms]
        return (self.docid_to_name(docid) for docid in self.docids_with_terms(terms))
        
    def query(self, q):
        '''Finds documents similar to q.
        
        Params:
            query: the query given as either a string or query vector
            
        Returns:
            A iterable of (docname, score) tuples sorted by score
        '''
        if isinstance(q, basestring):
            if isinstance(q, str):
                q = unicode(q)
            return self._query(
                term_vec.term_vec(q,
                                  stoplist=self.config('stoplist'),
                                  lowercase=self.config('lowercase')))
        else:
            return self._query(q)
        
    @abc.abstractmethod
    def _query(self, query_vec):
        '''Finds documents similar to query_vec
        
        Params:
            query_vec: term vector representing query document
        
        Returns:
            A iterable of (docname, score) tuples sorted by score
        '''
        return
    
