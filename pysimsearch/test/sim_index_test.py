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
import sys
import time
from multiprocessing import Process
from pprint import pprint

from pysimsearch import term_vec
from pysimsearch.sim_index import MemorySimIndex
from pysimsearch.sim_index import ShelfSimIndex
from pysimsearch.sim_index import ConcurrentSimIndex
from pysimsearch.sim_index import SimIndexCollection
from pysimsearch.sim_index import RemoteSimIndex
from pysimsearch import sim_server

class SimIndexTest(object):
    '''
    Provides common tests for different implementations of the SimIndex
    interface.
    
    To test a concrete implementation of SimIndex, must sublcass SimIndexTest,
    and also inherit unittest.TestCase.  SimIndexTest intentionally does not
    inherit unittest.TestCase, as it is only an abstract class that cannot be
    instantiated and tested separately from an implementation.
    '''
    longMessage = True

    sim_index = None

    def setUp(self):
        with io.StringIO(self.stopfile_buffer) as stopfile:
            self.sim_index.load_stoplist(stopfile)
            
        self.sim_index.index_string_buffers(self.docs)

    # Stopword list
    stopfile_buffer = "stopword1 stopword2"

    # Test documents
    docs = ( ('doc1', "hello there world     hello stopword1"),
             ('doc2', "hello       world           stopword2"),
             ('doc3', "hello there       bob      ") )
    
    # Postings that correspond to test documents
    golden_postings = { 'hello': {'doc1': 2, 'doc2': 1, 'doc3': 1},
                        'there': {'doc1': 1, 'doc3': 1},
                        'world': {'doc1': 1, 'doc2': 1},
                        'bob': {'doc3': 1},
                        'nobody': {},
                        '': {}}

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
        pprint(r)
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

    def test_stoplist(self):
        '''Test stoplist functionality'''
        for term in self.stopfile_buffer.split():
            print("stopword={}".format(term))
            self.assertEqual(list(self.sim_index.postings_list(term)), [])

    def test_docnames_with_terms(self):
        '''Test docnames_with_terms() using known data
        
        We use sets instead of lists to more easily allow equality
        comparison with golden data.
        '''

        # We unpack the golden hit lists, construct a golden set of docnames
        # for the hits, and compare with sim_index.docnames_with_terms()
        for (query, golden_doc_hits) in self.golden_conj_hits.items():
            query_vec = term_vec.term_vec(query)
            terms = [term for (term, freq) in query_vec.items()]
            
            self.assertEqual(golden_doc_hits,
                             set(self.sim_index.docnames_with_terms(*terms)))

    def test_query_simple_scorer(self):
        '''Test query() with simple_scorer using known data.
        
        Uses SimpleCountQueryScorer for scoring.
        '''
        self.sim_index.set_query_scorer('simple_count')
        for (query, golden_doc_hits) in self.golden_scored_hits.items():
            self.assertEqual(golden_doc_hits,
                             dict(self.sim_index.query(query)),
                             msg = "query={}".format(query))

    def test_query_tfidf_scorer(self):
        '''Test query() with tfidf using known data.
        
        Uses TFIDFQueryScorer for scoring.
        '''
        self.sim_index.set_query_scorer('tfidf')
        for (query, golden_doc_hits_cos) in self.get_golden_hits_cos().items():
            results = self.sim_index.query(query)
            for (docname, score) in results:
                self.assertAlmostEqual(score,
                                       golden_doc_hits_cos[docname],
                                       msg="results={}".format(str(results)))
    
    def test_del_docids(self):
        '''Test del_docids()'''
        retest_list = (self.test_docnames_with_terms,
                       self.test_query_simple_scorer,
                       self.test_query_tfidf_scorer,)
        
        # Make sure that the selected tests already pass (just for clarity)
        for test in retest_list:
            test()

        # Add an extra doc to the index
        self.sim_index.index_string_buffers( (('extra_doc', "hello world"),) )

        # Make sure that selected tests fail when we add an extra 'unexpected'
        # doc to the index
        for test in retest_list:
            self.assertRaises(AssertionError, test)
        
        # Delete the extra doc
        docid = self.sim_index.name_to_docid('extra_doc')
        print('extra docid={}'.format(docid))
        self.sim_index.del_docids(docid)

        # Now make sure that the selected tests pass again
        for test in retest_list:
            test()
    
    def test_config(self):
        '''Ensure that various config params are properly handled'''

        ### Test 'lowercase' param
        
        def _check_lc(index, golden_results):
            '''helper that checks index against golden_results'''
            for (term, golden_docs) in golden_results:
                self.assertEqual(
                    set(index.docnames_with_terms(term)), golden_docs)
                self.assertEqual(
                    set([doc for (doc, score) in index.query(term)]), golden_docs)
                
        # test data
        test_docs = (('doc1', 'Hello There'),
                     ('doc2', 'hello there'))

        # lowercase=True
        index = MemorySimIndex()
        index.set_config('lowercase', True)
        index.index_string_buffers(test_docs)
        golden_results = (('hello', {'doc1', 'doc2'}),
                          ('Hello', {'doc1', 'doc2'}),
                          ('HELLO', {'doc1', 'doc2'}))
        _check_lc(index, golden_results)
        
        # lowercase=False
        index = MemorySimIndex()
        index.set_config('lowercase', False)
        index.index_string_buffers(test_docs)
        golden_results = (('hello', {'doc2'}),
                          ('Hello', {'doc1'}),
                          ('HELLO', set()))
        _check_lc(index, golden_results)

class MemorySimIndexTest(SimIndexTest, unittest.TestCase):
    '''
    All tests hitting the SimIndex interface are in the parent class, SimIndexTest
    
    Tests for api's not in parent class are tested separately here.  This is
    so we can reuse test code across all implementations of SimIndex.
    '''
    
    def setUp(self):
        print("MemorySimIndexTest")
        self.sim_index = MemorySimIndex()
        super(MemorySimIndexTest, self).setUp()

    def tearDown(self):
        pass
        
    def test_save_load(self):
        '''Test save()/load() functionality'''
        with io.BytesIO() as output:
            self.sim_index.save(output)
            output.seek(0)
            loaded_sim_index = MemorySimIndex.load(output)
        self.sim_index = loaded_sim_index
        self.test_query_simple_scorer()  # make sure test_query() still works

class ShelfSimIndexTest(SimIndexTest, unittest.TestCase):
    '''
    All tests hitting the SimIndex interface are in the parent class, SimIndexTest
    
    Tests for api's not in parent class are tested separately here.  This is
    so we can reuse test code across all implementations of SimIndex.
    '''
    
    def setUp(self):
        print("ShelfSimIndexTest")
        self.sim_index = ShelfSimIndex("/tmp/test_dbm", 'n')
        super(ShelfSimIndexTest, self).setUp()

    def tearDown(self):
        self.sim_index.close()

class ConcurrentSimIndexTest(SimIndexTest, unittest.TestCase):
    '''
    All tests hitting the SimIndex interface are in the parent class, SimIndexTest
    
    Tests for api's not in parent class are tested separately here.  This is
    so we can reuse test code across all implementations of SimIndex.
    '''
    
    def setUp(self):
        print("ConcurrentSimIndexTest")
        self.sim_index = ConcurrentSimIndex(MemorySimIndex())
        super(ConcurrentSimIndexTest, self).setUp()

    def tearDown(self):
        pass

class SimIndexCollectionTest(SimIndexTest, unittest.TestCase):
    '''
    All tests hitting the SimIndex interface are in the parent class, SimIndexTest
    
    Tests for api's not in parent class are tested separately here.  This is
    so we can reuse test code across all implementations of SimIndex.    
    '''

    def setUp(self):
        print("SimIndexCollectionTest")
        self.sim_index = SimIndexCollection()
        for i in range(2):
            self.sim_index.add_shards(MemorySimIndex())

        super(SimIndexCollectionTest, self).setUp()
    
    def tearDown(self):
        pass
    

class SimIndexRemoteCollectionTest(SimIndexTest, unittest.TestCase):
    '''
    All tests hitting the SimIndex interface are in the parent class, SimIndexTest
    
    Tests for api's not in parent class are tested separately here.  This is
    so we can reuse test code across all implementations of SimIndex.    
    '''

    processes = None
    
    def setUp(self):
        # setUpClass() may be more efficient for spinning up the servers,
        # but this way is more robust (since we'll start each test from a
        # clean slate). Otherwise we'd need clear() functionality added.

        print("SimIndexRemoteCollectionTest")
        
        # We will create a collection tree of the form:
        #
        #      Root
        #     /   \
        #    A     B
        #   /\     /\
        #  1  2   3  4
        self.processes = []

        # start leaves
        for i in range(4):
            port = 9100 + i
            process = Process(target=sim_server.start_sim_index_server,
                              kwargs={'port': port, 'logRequests': False})
            process.daemon = True
            process.start()
            self.processes.append(process)
            
        print("Waiting for leaf servers to start")
        time.sleep(0.1)
        
        leaf_nodes = [[],[]]
        for i in range(4):
            port = 9100 + i
            leaf_nodes[i//2].append(RemoteSimIndex(
                "http://localhost:{}/RPC2".format(port)))

        # start interior nodes (A, B)
        for i in range(2):
            port = 9200 + i
            process = Process(
                target=sim_server.start_sim_index_server,
                kwargs={ 'port': port,
                         'backends': leaf_nodes[i],
                         'root': False,
                         'logRequests': False
                        }
            )
            process.daemon = True
            process.start()
            self.processes.append(process)

        print("Waiting for intermediate servers to start")
        time.sleep(0.1)        

        interior_nodes = []
        for i in range(2):
            port = 9200 + i
            interior_nodes.append(
                RemoteSimIndex("http://localhost:{}/RPC2".format(port)))

        # root node
        self.sim_index = SimIndexCollection(root=True)
        self.sim_index.add_shards(*interior_nodes)
        
        super(SimIndexRemoteCollectionTest, self).setUp()
    
    def tearDown(self):
        for process in self.processes:
            process.terminate()
        time.sleep(0.1)


if __name__ == "__main__":
    unittest.main()
