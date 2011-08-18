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
Unittests for pysimsearch.term_vec package

To run unittests, run 'nosetests' from the test directory
'''
from __future__ import(division, absolute_import, print_function,
                       unicode_literals)

import unittest

import math
import os
import pprint

from pysimsearch import term_vec

class TermVecTest(unittest.TestCase):
    longMessage = True

    def test_dot_product(self):
        '''dot_product() test using known inputs'''
        v1 = {'a':1, 'b':2, 'c':0.5}
        v2 = {'a':2,        'c':2, 'd':100}
        
        self.assertEqual(term_vec.dot_product(v1, v2), 3)

    def test_l2_norm(self):
        '''l2_norm() test using known inputs'''
        v = {'a':1, 'b':2, 'c':5}
        
        self.assertEqual(term_vec.l2_norm(v), math.sqrt(1 + 2**2 + 5**2))

    def test_magnitude(self):
        '''magnitude() test using known inputs'''
        v = {'a':1, 'b':2, 'c':5}
        
        self.assertEqual(term_vec.l2_norm(v), math.sqrt(1 + 2**2 + 5**2))
        
    def test_mag_union(self):
        '''mag_union() test using known inputs'''
        A = {'a':1, 'b':2, 'c':5}
        B = {'a':1,        'c':2, 'd':3}
        
        self.assertEqual(term_vec.mag_union(A, B), 14)
    
    def test_mag_intersect(self):
        '''mag_intersect() test using known inputs'''
        A = {'a':1, 'b':2, 'c':5}
        B = {'a':1,        'c':2, 'd':3}
        
        self.assertEqual(term_vec.mag_intersect(A, B), 3)


if __name__ == "__main__":
    unittest.main()
