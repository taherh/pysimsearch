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
@author: taherh

Sample usage:

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

'''


from __future__ import (division, absolute_import, print_function,
        unicode_literals)


from collections import defaultdict

from .exceptions import *
from . import doc_reader

class SimIndex(object):
    '''
       Base class for similarity indexes
       Defines interface as well as provides default implementation for
       several methods.
    '''
    
    def index_files(self, named_files):
        '''Build a similarity index over collection given in named_files
           named_files is an iterable of (filename, file) pairs
        '''
        raise AbstractMethodException()

    def index_filenames(self, filenames):
        '''Build a similarity index over files given by filenames'''
        return self.index_files(zip(filenames,
                                    doc_reader.get_text_files(filenames)))
    
    def docid_to_name(self, docid):
        '''Returns document name for a given docid'''
        raise AbstractMethodException()
        
    def name_to_docid(self, name):
        '''Returns docid for a given document name'''
        raise AbstractMethodException()

    def postings_list(self, term):
        '''Return list of (docid, frequency) tuples for docs that contain term'''
        raise AbstractMethodException()
    
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
        '''Returns a list of docnames containing terms'''
        return (self.docid_to_name(docid) for docid in self.docids_with_terms(terms))
        
    def query(self, doc):
        '''Return documents similar to doc'''
        raise AbstractMethodException()



class SimpleMemorySimIndex(SimIndex):
    '''
    Simple implementation of SimIndex using in-memory data structures.
    (Not meant to scale to large datasets)
    '''

    _next_docid = 0
    
    name_to_docid_map = {}
    docid_to_name_map = {}
    term_index = defaultdict(list)

    class Config(object):
        lowercase = True
    config = Config()
    
    def __init__(self, config = Config()):
        self.config = config
        pass
    
    def index_files(self, named_files):
        '''Build a similarity index over collection given in named_files
           named_files is an iterable of (filename, file) pairs
           
           Example:
           sim_index.index_files(
             doc_reader.get_named_text_files('a.txt', 'b.txt', 'c.txt'))
        '''
        for (name, _file) in named_files:
            with _file as file:  # create 'with' context for file
                self.name_to_docid_map[name] = self._next_docid
                self.docid_to_name_map[self._next_docid] = name
                self._add_vec(self._next_docid, doc_reader.term_vec(file))
                self._next_docid += 1

    def _add_vec(self, docid, term_vec):
        '''Add term_vec to the index'''
        for (term, freq) in term_vec.iteritems():
            if self.config.lowercase:
                term = term.lower()
            self.term_index[term].append((docid, freq))

    def docid_to_name(self, docid):
        return self.docid_to_name_map[docid]
        
    def name_to_docid(self, name):
        return self.name_to_docid_map[name]

    def postings_list(self, term):
        '''Returns list of (docid, freq) tuples for documents containing
           term'''
        return self.term_index[term]
    
    def query(self, doc):
        '''Return documents similar to doc'''
        pass
