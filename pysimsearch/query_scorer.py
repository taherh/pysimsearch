#!/usr/bin/env python

# Copyright (c) 2011, Taher Haveliwala <oss@taherh.org>
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
from math import log

class QueryScorer(object):
    '''
    Interface for query scorers which score similarity search results
    
    QueryScorers are used by the SimIndex.query() method to handle the
    scoring of similarity search results.    
    '''
    
    __metaclass__ = abc.ABCMeta
    
    # name->scorer mapping
    _scorers = { }
    
    @staticmethod
    def make_scorer(scorer_type):
        '''Returns a new scorer object'''
        return QueryScorer._scorers[scorer_type]()
    
    @staticmethod
    def register_scorers(scorer_map):
        QueryScorer._scorers.update(scorer_map)
        
    @abc.abstractmethod
    def score_docs(self, query_vec, postings_lists, **extra):
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


class SimpleCountQueryScorer(QueryScorer):
    '''
    QueryScorer that uses simple term frequencies for scoring.
    '''

    def score_docs(self, query_vec, postings_lists, **extra):
        '''
        Scores query-document similarity using number of occurrences
        of query terms in document.  Multiple occurrences of a term
        in the query are ignored.
        '''
        
        doc_hit_map = defaultdict(int)
        for (term, postings_list) in postings_lists:
            assert(query_vec[term] >= 1)
            for (docid, freq) in postings_list:
                doc_hit_map[docid] += freq
        
        # construct list of tuples sorted by value
        return sorted(doc_hit_map.iteritems(),
                      key=operator.itemgetter(1),
                      reverse=True)

class TFIDFQueryScorer(QueryScorer):
    '''
    QueryScorer that uses TFIDF weighting with the cosine similarity measure.
    
    This implementation is actually an approximation to the true
    cosine, because of the way we normalize by document length.
    When computing document length, we assume a term weight of 1 for
    each document term. E.g., we do not factor in term weights
    when computing the "document length", since that would require
    choosing the weighting strategy at index time.
    
    Query length is ignored, as it has no effect on relative ordering
    '''
    
    @staticmethod
    def tf_weight_raw(tf):
        '''Returns unscaled tf'''
        return tf
    
    @staticmethod
    def tf_weight_log(tf):
        '''Returns sublinear scaling of tf: 1+log(tf)'''
        assert(tf > 0)
        return 1 + log(tf)
    
    @staticmethod
    def idf_weight_log(N, df):
        '''Returns idf weight'''
        assert(df > 0)
        return log(N/df)
    
    def __init__(self, tf_weight_type = 'raw'):
        if tf_weight_type == 'log':
            self.tf_weight = self.tf_weight_log
        else:
            self.tf_weight = self.tf_weight_raw
        
        self.idf_weight = self.idf_weight_log
        
    def score_docs(self, query_vec, postings_lists, N, get_doc_freq, get_doc_len, **extra):
        '''
        Scores documents' similarities to query using cosine similarity
        in a vector space model.  Uses tf.idf weighting.
        
        An individual term hit is scored as::
        
            idf * self.tf_weight(q_tf) * self.tf_weight(d_tf)
        
        The overall score for a doc is given by the sum of the term-hit scores
        '''
        
        if N == 0: return ()
        doc_hit_map = defaultdict(int)
        for (term, postings_list) in postings_lists:
            idf = self.idf_weight(N, get_doc_freq(term))
            query_term_wt = self.tf_weight(query_vec[term]) * idf
            for (docid, freq) in postings_list:
                doc_hit_map[docid] += self.tf_weight(freq) * query_term_wt
        for (docid, weight) in doc_hit_map.iteritems():
            doc_len = get_doc_len(docid)
            doc_hit_map[docid] = weight / doc_len
            
        # construct list of tuples sorted by value
        return sorted(doc_hit_map.iteritems(),
                      key=operator.itemgetter(1),
                      reverse=True)

# Register scorers by name
QueryScorer.register_scorers({
    'simple_count': SimpleCountQueryScorer,
    'tfidf': TFIDFQueryScorer
})

