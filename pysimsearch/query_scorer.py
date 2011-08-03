#!/usr/bin/env python

# Copyright (c) 2010, Taher Haveliwala <oss@taherh.org>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * The names of project contributors may not be used to endorse or
#       promote products derived from this software without specific
#       prior written permission.
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
Scoring algorithms for finding similar documents
'''

from __future__ import (division, absolute_import, print_function,
        unicode_literals)

import abc
from collections import defaultdict
import operator

class QueryScorer(object):
    '''
    Interface for query scorers which score similarity search results
    
    QueryScorers are passed to the SimIndex.query() method to handle
    scoring of similarity search results.
    
    Attributes:
    
    '''
    
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def score_docs(self, query_vec, postings_lists):
        '''Scores documents' similarities to query
        
        Scans postings_lists to compute similarity scores for docs for the
        query term vector
        
        Params:
            query: the query document
            postings_lists: a list of postings lists for terms in query
        
        Returns:
            A sorted iterable of (docid, score) tuples
        '''
        return


class SimpleCountQueryScorer(object):
    '''
    Query scorer that uses simple term frequencies for scoring hits.    
    '''
    
    def score_docs(self, query_vec, postings_lists):
        '''
        Scores documents' similarities to query using simple term counts.
        If a term appears multiple times in query, the count for that
        term is multiplied by the query frequency when accumulating hits.
        '''
        
        doc_hit_map = defaultdict(int)
        for (term, postings_list) in postings_lists:
            query_term_freq = query_vec[term]
            for (docid, freq) in postings_list:
                doc_hit_map[docid] += freq * query_term_freq
        
        # construct list of tuples sorted by value
        return sorted(doc_hit_map.iteritems(),
                      key=operator.itemgetter(1),
                      reverse=True)
