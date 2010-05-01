#!/usr/bin/env python

# Copyright (c) 2010, Taher Haveliwala
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
@author: taherh

To run unittests, run 'nosetests' from the test directory
'''
from __future__ import division, absolute_import, print_function

import unittest

import itertools
import math
import os
import sys

from pysimsearch import similarity

class SimsearchTest(unittest.TestCase):
    testdata_dir = None  # Will be set in setUp()
    expected_sims = dict()

    def setUp(self):
        # set testdata_dir
        rel_file_path = os.path.dirname(__file__)
        self.testdata_dir = os.path.join(os.getcwd(), rel_file_path, 'data/')

    def tearDown(self):
        pass

    def test_dot_product(self):
        '''dot_product() test using known inputs'''
        v1 = {'a':1, 'b':2, 'c':0.5}
        v2 = {'a':2,        'c':2, 'd':100}
        
        self.assertEquals(similarity.dot_product(v1, v2), 3)

    def test_magnitude(self):
        '''magnitude() test using known inputs'''
        v = {'a':1, 'b':2, 'c':5}
        
        self.assertEquals(similarity.magnitude(v), math.sqrt(1 + 2**2 + 5**2))

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
        with open(self.testdata_dir + 'expected_results') as \
                expected_results_file:
            for line in expected_results_file:
                (fname_a, fname_b, expected_sim) = line.split()
                self.assert_(fname_a < fname_b,
                             'expected_results: require fname_a < fname_b: ' + 
                             line)
                self.expected_sims[(fname_a,fname_b)] = float(expected_sim)
                
        # generator of file-pairs to compare    
        file_pairs = ((fname_a, fname_b)
                      for (fname_a,fname_b) in \
                          itertools.product(input_filenames, repeat=2)
                      if fname_a < fname_b)  # We don't want to self-compare
        
        # check computed similarities against expected similarities
        for (fname_a, fname_b) in file_pairs:
            if (fname_a, fname_b) not in self.expected_sims: continue
            with open(self.testdata_dir + fname_a) as file_a:
                with open(self.testdata_dir + fname_b) as file_b:
                    sim = similarity.measure_similarity(file_a, file_b)
                    self.assertAlmostEquals(
                            sim, self.expected_sims[(fname_a, fname_b)], 
                            places = 3,
                            msg = 'Mismatch for pair {0}: got {1}, expected {2}'.
                            format((fname_a, fname_b), sim, 
                                   self.expected_sims[(fname_a, fname_b)]))
            
            
if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
