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
Unittests for pysimsearch.similarity package

To run unittests, run 'nosetests' from the test directory
'''
from __future__ import(division, absolute_import, print_function,
                       unicode_literals)

import unittest

import math
import os
import pprint

from pysimsearch import similarity

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


if __name__ == "__main__":
    unittest.main()
