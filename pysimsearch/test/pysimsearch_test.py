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
Unittests for pysimsearch package

To run unittests, run 'nosetests' from the test directory
'''
from __future__ import(division, absolute_import, print_function,
                       unicode_literals)

import unittest

import io
import itertools
import math
import os
import sys

from pysimsearch import similarity
from pysimsearch import freq_tools
from pysimsearch import doc_reader
from pysimsearch.sim_index import SimpleMemorySimIndex
from pysimsearch import query_scorer


class SimilarityTest(unittest.TestCase):
    longMessage = True
    testdata_dir = None  # Will be set in setUp()

    def setUp(self):
        # set testdata_dir
        rel_file_path = os.path.dirname(__file__)
        self.testdata_dir = os.path.join(os.getcwd(), rel_file_path, 'data/')

    def tearDown(self):
        pass

    def test_measure_similarity(self):
        '''
        measure_similarity() should give known results for known inputs
        known input files are listed in 'test/data/test_filenames'
        known results are listed in 'test/data/expected_results' with the format
            filename1 filename2 sim
        '''
        # read test filenames
        with open(self.testdata_dir + 'test_filenames') as input_filenames_file:
            input_filenames = [fname.rstrip() for fname in 
                               input_filenames_file.readlines()]
        
        input_filenames.sort()
                
        # read expected results
        expected_sims = dict()
        with open(self.testdata_dir + 'expected_results') as \
                expected_results_file:
            for line in expected_results_file:
                (fname_a, fname_b, expected_sim) = line.split()
                self.assertTrue(fname_a < fname_b,
                             'expected_results: require fname_a < fname_b: ' + 
                             line)
                expected_sims[(fname_a,fname_b)] = float(expected_sim)
                
        # check computed similarities against expected similarities
        for (fname_a, fname_b) in expected_sims:
            print('Comparing {0},{1}'.format(fname_a, fname_b))
            with open(self.testdata_dir + fname_a) as file_a:
                with open(self.testdata_dir + fname_b) as file_b:
                    sim = similarity.measure_similarity(file_a, file_b)
                    self.assertAlmostEqual(
                            sim, expected_sims[(fname_a, fname_b)], 
                            places = 3,
                            msg = 'Mismatch for pair {0}: got {1}, expected {2}'.
                            format((fname_a, fname_b), sim, 
                                   expected_sims[(fname_a, fname_b)]))

    def test_cosine_sim(self):
        '''cosine_sim() test using known inputs'''
        u = {'a':1, 'b':2, 'c':5}
        v = {'a':1,        'c':2, 'd':3}
    
        self.assertEqual(similarity.cosine_sim(u, v), 11 / (math.sqrt(30) * math.sqrt(14)))
        
    def test_jaccard_sim(self):
        '''jaccard_sim() test using known inputs'''
        A = {'a':1, 'b':2, 'c':5}
        B = {'a':1,        'c':2, 'd':3}
    
        self.assertEqual(similarity.jaccard_sim(A, B), 3 / 14)
    
class FreqToolsTest(unittest.TestCase):
    longMessage = True

    def test_read_df(self):
        '''read_df() test'''
        df_dict = {'a':5, 'b':3, 'c':1}
        df_file_str =\
        '''
        a    5
        b    3
        c    1
        '''
        df_file = io.StringIO(df_file_str)
        self.assertEqual(freq_tools.read_df(df_file), df_dict)
        
    def test_write_df(self):
        '''write_df() test'''
        df_dict = {'a':5, 'b':3, 'c':1}
        df_file = io.StringIO()
        freq_tools.write_df(df_dict, df_file)
        
        df_file.seek(0)
        self.assertEqual(freq_tools.read_df(df_file), df_dict)
            
    def test_compute_df(self):
        doc1 = 'a b b     c d e e e e f'
        doc2 = '  b           e         g g g h i'
        doc3 = '  b b b b c d                 h  '
        
        df_dict = {'a':1, 'b':3, 'c':2, 'd':2, 'e':2, 'f':1, 'g':1, 'h':2,
                   'i':1}
        
        files = (io.StringIO(doc1), io.StringIO(doc2), io.StringIO(doc3))
        self.assertEqual(freq_tools.compute_df(files), df_dict)
    
class TermVecTest(unittest.TestCase):
    longMessage = True

    def test_dot_product(self):
        '''dot_product() test using known inputs'''
        v1 = {'a':1, 'b':2, 'c':0.5}
        v2 = {'a':2,        'c':2, 'd':100}
        
        self.assertEqual(similarity.dot_product(v1, v2), 3)

    def test_l2_norm(self):
        '''l2_norm() test using known inputs'''
        v = {'a':1, 'b':2, 'c':5}
        
        self.assertEqual(similarity.l2_norm(v), math.sqrt(1 + 2**2 + 5**2))

    def test_magnitude(self):
        '''magnitude() test using known inputs'''
        v = {'a':1, 'b':2, 'c':5}
        
        self.assertEqual(similarity.l2_norm(v), math.sqrt(1 + 2**2 + 5**2))
        
    def test_mag_union(self):
        '''mag_union() test using known inputs'''
        A = {'a':1, 'b':2, 'c':5}
        B = {'a':1,        'c':2, 'd':3}
        
        self.assertEqual(similarity.mag_union(A, B), 14)
    
    def test_mag_intersect(self):
        '''mag_intersect() test using known inputs'''
        A = {'a':1, 'b':2, 'c':5}
        B = {'a':1,        'c':2, 'd':3}
        
        self.assertEqual(similarity.mag_intersect(A, B), 3)
    
class SimIndexTest(unittest.TestCase):
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
    
    # Golden hits data (frequencies are simple match-counts between query terms
    # and document terms). (Disjunctive: requires any term to be present)
    #
    # We can reuse golden_postings to provide some test input here
    golden_scored_hits = { term: docnames
        for (term, docnames) in golden_postings.items() }
    # and of course throw in some multiword queries as well
    golden_scored_hits.update({ "hello there": {'doc1': 3, 'doc2': 1, 'doc3': 2},
                                "there world": {'doc1': 2, 'doc2': 1, 'doc3': 1},
                                "hello world": {'doc1': 3, 'doc2': 2, 'doc3': 1} })
    
    def setUp(self):
        self.sim_index = SimpleMemorySimIndex()

        named_files = ((docname, io.StringIO(doc))
                            for (docname, doc) in self.docs)
        self.sim_index.index_files(named_files)
    
    def tearDown(self):
        pass
        
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
        comparison with golden data.assertE
        '''

        # We unpack the golden hit lists, construct a golden set of docnames
        # for the hits, and compare with sim_index.docnames_with_terms()
        for (query, golden_doc_hits) in self.golden_conj_hits.items():
            query_vec = doc_reader.term_vec_from_string(query)
            terms = [term for (term, freq) in query_vec.items()]
            
            self.assertEqual(golden_doc_hits,
                             set(self.sim_index.docnames_with_terms(*terms)))

    def test_query(self):
        '''Test query() using known data'''
        self.sim_index.set_query_scorer(query_scorer.SimpleCountQueryScorer())
        for (query, golden_doc_hits) in self.golden_scored_hits.items():
            query_vec = doc_reader.term_vec_from_string(query)
            self.assertEqual(golden_doc_hits,
                             dict(self.sim_index.query(query_vec)),
                             msg = "query={}".format(query))

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
