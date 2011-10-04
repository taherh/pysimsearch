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
ShelfSimIndex

Sample usage::

    from pprint import pprint
    from pysimsearch.sim_index import ShelfSimIndex
    from pysimsearch import doc_reader

    sim_index = ShelfSimIndex()
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

from collections import defaultdict, MutableMapping
from shelve import DbfilenameShelf as DBShelf

from . import MapSimIndex
from ..exceptions import *

class ShelfSimIndex(MapSimIndex):
    '''
    Inherits from :class:`pysimsearch.sim_index.MapSimIndex`.
    
    Shelf-based implementation of :class:`SimIndex`.  Indexes are backed with
    persistent :class:`shelve.DbfilenameShelf` objects.
    '''
    
    
    def __init__(self, filename, flag):
        name_to_docid_map = StrKeyMap(DBShelf(filename + '_n2d', flag))
        docid_to_name_map = StrKeyMap(DBShelf(filename + '_d2n', flag))
        docid_to_feature_map = StrKeyMap(DBShelf(filename + '_feat', flag))

        # term index
        term_index = StrKeyMap(DBShelf(filename + '_term', flag))

        # document vectors
        doc_vectors = StrKeyMap(DBShelf(filename + '_doc_vec', flag))

        # additional stats used for scoring
        df_map = StrKeyMap(DBShelf(filename + '_df', flag))
        doc_len_map = StrKeyMap(DBShelf(filename + '_dl', flag))

        self._maps = dict(name_to_docid_map=name_to_docid_map,
                          docid_to_name_map=docid_to_name_map,
                          docid_to_feature_map=docid_to_feature_map,
                          term_index=term_index,
                          doc_vectors=doc_vectors,
                          df_map=df_map,
                          doc_len_map=doc_len_map)
        
        super(ShelfSimIndex, self).__init__(**self._maps)
        
        self._N = len(docid_to_name_map)

    def close(self):
        for (mapname, map) in self._maps.items():
            map.close()

class StrKeyMap(MutableMapping):
    '''
    Ensure that key is converted to str type that is compatible with keys
    for underlying map.
    '''
    def __init__(self, map):
        self._map = map
        
    def __getitem__(self, key):
        return self._map[str(key)]
        
    def __setitem__(self, key, value):
        self._map[str(key)] = value
        
    def __delitem__(self, key):
        del self._map[str(key)]
        
    def __iter__(self):
        raise Exception('Unsupported')
        # return iter(self._map)
        
    def __len__(self):
        return len(self._map)
        
    def close(self):
        return self._map.close()
