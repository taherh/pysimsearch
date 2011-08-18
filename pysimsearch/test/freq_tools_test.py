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
Unittests for pysimsearch.freq_tools package

To run unittests, run 'nosetests' from the test directory
'''
from __future__ import(division, absolute_import, print_function,
                       unicode_literals)

import unittest

import io
import pprint

from pysimsearch import freq_tools
from pysimsearch import doc_reader
    
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
    

if __name__ == "__main__":
    unittest.main()
