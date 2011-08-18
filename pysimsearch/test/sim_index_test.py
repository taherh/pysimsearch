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
Unittests for pysimsearch.sim_index package

To run unittests, run 'nosetests' from the test directory
'''
from __future__ import(division, absolute_import, print_function,
                       unicode_literals)

import unittest

import io
import math
import pprint

from pysimsearch import doc_reader
from pysimsearch.sim_index import SimpleMemorySimIndex
from pysimsearch.sim_index import SimIndexCollection
from pysimsearch import query_scorer

class SimIndexTest(object):
    '''
    Provides common tests for different implementations of the SimIndex
    interface.
    
    To test a concrete implementation of SimIndex, must sublcass SimIndexTest,
    and also inherit unittest.TestCase.  We intentionally do not inherit
    unittest.TestCase for SimIndexTest, as SimIndex is only an abstract
    class that cannot be instantiated.
    '''
    longMessage = True

    sim_index = None

    # Test documents
    docs = [ ('doc1', "hello there world     hello"),
             ('doc2', "hello       world          "),
             ('doc3', "hello there       bob      ") ]
    
    # Postings that correspond to test documents
    golden_postings = { 'hello': {'doc1': 2, 'doc2': 1, 'doc3': 1},
                        'there': {'doc1': 1, 'doc3': 1},
                        'world': {'doc1': 1, 'doc2': 1},
                        'bob': {'doc3': 1} }

    # Golden hits data (Conjunctive: Requires presence of all terms)
    #
    # We can reuse golden_postings to provide some test input here
    golden_conj_hits = { term: set(postings.keys())
        for (term, postings) in golden_postings.items() }
    # and of course throw in some multiword queries as well
    golden_conj_hits.update({ "hello there": {'doc1', 'doc3'},
                              "there world": {'doc1'},
                              "hello world": {'doc1', 'doc2'} })
    
    # Golden hits data for SimpleCountQueryScorer (frequencies are simple
    # match-counts between query terms and document terms).
    #   (Disjunctive: requires any term to be present)
    #
    # We can reuse golden_postings to provide some test input here
    golden_scored_hits = { term: docnames
        for (term, docnames) in golden_postings.items() }
    # and of course throw in some multiword queries as well
    golden_scored_hits.update({ "hello there": {'doc1': 3, 'doc2': 1, 'doc3': 2},
                                "there world": {'doc1': 2, 'doc2': 1, 'doc3': 1},
                                "hello world": {'doc1': 3, 'doc2': 2, 'doc3': 1} })

    def get_golden_hits_cos(self):
        '''Manually computes cosine scores for test set to create golden results'''
        d1_len = math.sqrt(2^2 + 1 + 1)
        d2_len = math.sqrt(1 + 1)
        d3_len = math.sqrt(1 + 1 + 1)
        N = 3
        hello_idf = math.log(N/3)
        there_idf = math.log(N/2)
        world_idf = math.log(N/2)
        bob_idf = math.log(N/1)
        r = ({ "hello there": {'doc1': hello_idf * 2 / d1_len + there_idf / d1_len,
                               'doc2': hello_idf / d2_len,
                               'doc3': hello_idf / d3_len + there_idf / d3_len},
               "there world": {'doc1': there_idf / d1_len + world_idf / d1_len,
                               'doc2': world_idf / d2_len,
                               'doc3': there_idf / d3_len},
               "hello world": {'doc1': hello_idf * 2 / d1_len + world_idf / d1_len,
                               'doc2': hello_idf / d2_len + world_idf / d2_len,
                               'doc3': hello_idf / d3_len} })
        pprint.pprint(r)
        return r
    
    def test_docname_docid_translation(self):
        '''Test docname_to_docid()/docid_to_docname() using known data'''

        for (docname, doc) in self.docs:
                self.assertEqual(docname,
                             self.sim_index.docid_to_name(
                                self.sim_index.name_to_docid(docname)))

    def test_postings_list(self):
        '''Test postings_list() using known data
        
        We use sets instead of lists to more easily allow equality
        comparison with golden data.
        '''

        for term in self.golden_postings:    
            translated_postings = {
                self.sim_index.docid_to_name(docid): freq
                    for (docid, freq) in
                            self.sim_index.postings_list(term)
                }
            self.assertEqual(translated_postings,
                             self.golden_postings[term])

    def test_docnames_with_terms(self):
        '''Test docnames_with_terms() using known data
        
        We use sets instead of lists to more easily allow equality
        comparison with golden data.
        '''

        # We unpack the golden hit lists, construct a golden set of docnames
        # for the hits, and compare with sim_index.docnames_with_terms()
        for (query, golden_doc_hits) in self.golden_conj_hits.items():
            query_vec = doc_reader.term_vec_from_string(query)
            terms = [term for (term, freq) in query_vec.items()]
            
            self.assertEqual(golden_doc_hits,
                             set(self.sim_index.docnames_with_terms(*terms)))

    def test_query_simple_scorer(self):
        '''Test query() with simple_scorer using known data.
        
        Uses SimpleCountQueryScorer for scoring.
        '''
        self.sim_index.set_query_scorer(query_scorer.SimpleCountQueryScorer())
        for (query, golden_doc_hits) in self.golden_scored_hits.items():
            self.assertEqual(golden_doc_hits,
                             dict(self.sim_index.query_by_string(query)),
                             msg = "query={}".format(query))

    def test_query_tfidf_scorer(self):
        '''Test query() with tfidf using known data.
        
        Uses TFIDFQueryScorer for scoring.
        '''
        self.sim_index.set_query_scorer(query_scorer.TFIDFQueryScorer())
        for (query, golden_doc_hits_cos) in self.get_golden_hits_cos().items():
            results = self.sim_index.query_by_string(query)
            for (docname, score) in results:
                self.assertAlmostEqual(score,
                                       golden_doc_hits_cos[docname],
                                       msg="results={}".format(str(results)))


class SimpleMemorySimIndexTest(SimIndexTest, unittest.TestCase):
    '''
    All tests hitting the SimIndex interface are in the parent class, SimIndexTest
    
    Tests for api's not in parent class are tested separately here.  This is
    so we can reuse test code across all implementations of SimIndex.
    
    '''
    def setUp(self):
        self.sim_index = SimpleMemorySimIndex()

        named_files = ((docname, io.StringIO(doc))
                            for (docname, doc) in self.docs)
        self.sim_index.index_files(named_files)
    
    def tearDown(self):
        pass
        
    def test_save_load(self):
        '''Test save()/load() functionality'''
        with io.BytesIO() as output:
            self.sim_index.save(output)
            output.seek(0)
            loaded_sim_index = SimpleMemorySimIndex.load(output)
        self.sim_index = loaded_sim_index
        self.test_query_simple_scorer()  # make sure test_query() still works


class SimIndexCollectionTest(SimIndexTest, unittest.TestCase):
    def setUp(self):
        self.sim_index = SimIndexCollection()
        for i in range(1):
            self.sim_index.add_shards(SimpleMemorySimIndex())
            
        named_files = ((docname, io.StringIO(doc))
                            for (docname, doc) in self.docs)
        self.sim_index.index_files(named_files)
    
    def tearDown(self):
        pass
        

if __name__ == "__main__":
    unittest.main()
