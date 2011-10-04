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
MemorySimIndex

Sample usage::

    from pprint import pprint
    from pysimsearch.sim_index import MemorySimIndex
    from pysimsearch import doc_reader

    sim_index = MemorySimIndex()
    sim_index.index_urls('http://www.stanford.edu/',
                         'http://www.berkeley.edu',
                         'http://www.ucla.edu',
                         'http://www.mit.edu')
    pprint(sim_index.postings_list('university'))
    pprint(list(sim_index.docnames_with_terms('university', 'california')))
    
    sim_index.set_query_scorer('simple_count')
    pprint(list(sim_index.query("stanford university")))

'''

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import cPickle as pickle
from collections import defaultdict

from . import MapSimIndex
from pysimsearch.exceptions import *

class MemorySimIndex(MapSimIndex):
    '''
    Inherits from :class:`pysimsearch.sim_index.MapSimIndex`.
    
    Memory-based implementation of :class:`SimIndex`.  Indexes are backed with
    ``dict``.
    '''
    
    def __init__(self):
        
        # index metadata
        name_to_docid_map = dict()
        docid_to_name_map = dict()
        docid_to_feature_map = dict()

        # term index
        term_index = dict()
        
        # document vectors
        doc_vectors = dict()
        
        # additional stats used for scoring
        df_map = dict()
        doc_len_map = dict()

        self._maps = dict(name_to_docid_map=name_to_docid_map,
                          docid_to_name_map=docid_to_name_map,
                          docid_to_feature_map=docid_to_feature_map,
                          term_index=term_index,
                          doc_vectors=doc_vectors,
                          df_map=df_map,
                          doc_len_map=doc_len_map)
        
        super(MemorySimIndex, self).__init__(**self._maps)
        
    def save(self, file):
        '''Saved index to file'''
        # pickle won't let us save query_scorer
        qs = self.query_scorer
        self.query_scorer = None
        pickle.dump(self, file)
        self.query_scorer = qs
        
    @staticmethod
    def load(file):
        '''Returns a ``MemorySimIndex`` loaded from pickle file'''
        return pickle.load(file)

