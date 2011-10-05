#!/usr/bin/env python
#
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
Term-vector operations
'''

import io
import math

def dot_product(v1, v2):
    '''Returns dot product of two term vectors'''
    val = 0.0
    for term in v1:
        if term in v2: val += v1[term] * v2[term]
    return val

def l2_norm(v):
    '''Returns L2 norm of term vector v'''
    val = 0.0
    for term in v:
        val += v[term]**2
    val = math.sqrt(val)
    return val

def mag_union(A, B):
    '''
    Returns magnitude of multiset-union of A and B
    '''
    val = 0
    for term in A: val += A[term]
    for term in B: val += B[term]
    return val

def mag_intersect(A, B):
    '''
    Returns magnitude of multiset-intersection of A and B
    '''
    val = 0
    for term in A:
        if term in B: val += min(A[term], B[term])
    return val

def magnitude(v):
    '''Returns L2 norm of term vector v (identical to l2_norm())'''
    return l2_norm(v)

def term_vec(input, stoplist=None, lowercase=False):
    '''
    Returns a term vector for ``input``, represented as a dictionary
    of the form {term: frequency}
    
    ``input`` can be either a string or a file
    '''
    if isinstance(input, basestring):
        with io.StringIO(input) as string_buffer:
            return term_vec(string_buffer)
    else:
        # default args:
        if stoplist is None:
            stoplist = set()
        
        tf_dict = {}
        for line in input:
            for term in line.split():
                if term not in stoplist:
                    if lowercase: term = term.lower()
                    if term not in tf_dict: tf_dict[term] = 0
                    tf_dict[term] += 1
        return tf_dict
