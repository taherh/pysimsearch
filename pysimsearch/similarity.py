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

Sample usage as a script:
$ python similarity.py http://www.stanford.edu/ http://www.berkeley.edu/ http://www.mit.edu/
Comparing files ['http://www.stanford.edu/', 'http://www.berkeley.edu/', 'http://www.mit.edu/']
sim(http://www.stanford.edu/,http://www.berkeley.edu/)=0.322771960247
sim(http://www.stanford.edu/,http://www.mit.edu/)=0.142787018368
sim(http://www.berkeley.edu/,http://www.mit.edu/)=0.248877629741

'''
from __future__ import division, absolute_import, print_function

import sys
import math
import re
import io
import httplib2
import lxml.html
from lxml.html.clean import clean_html

def measure_similarity(file_a, file_b):
    '''
    Returns the textual similarity of file_a and file_b
    Uses the cosine similarity measure: <u,v>/(|u||v|)
    '''
    u = term_vec(file_a)
    v = term_vec(file_b)

    return dot_product(u, v) / (magnitude(u) * magnitude(v))
    
def dot_product(v1, v2):
    '''Returns dot product of two term vectors'''
    val = 0.0
    for term in v1:
        if term in v2: val += v1[term] * v2[term]
    return val

def magnitude(v):
    '''Returns magnitude (L2 norm) of term vector v'''
    val = 0.0
    for term in v:
        val += v[term]**2
    val = math.sqrt(val)
    return val

def term_vec(file):
    '''Returns a term vector for 'file', represented as a dictionary mapping {term->frequency}'''
    
    tf_dict = {}
    for line in file:
        for term in line.split():
            if type(term) == bytes:
                term = term.decode('utf-8')  # Make sure term is in unicode (Python 2.x hack)
            if not term in tf_dict: tf_dict[term] = 0
            tf_dict[term] += 1
    return tf_dict

# _get_text_stream() needs an http object
_h = httplib2.Http('.cache')

def _get_text_stream(name):
    '''Returns a text stream from either a file or a url'''
    file = None
    http_pattern = '^http://'
    if re.search(http_pattern, name):
        (response, content) = _h.request(name)
        html_tree = lxml.html.fromstring(content)
        clean_html(html_tree)  # removes crud from html
        clean_html_string = lxml.html.tostring(html_tree, 
                                               encoding=unicode, method='text')
        file = io.StringIO(clean_html_string)
    else:
        file  = open(name)
    return file

def pairwise_compare(files):
    print('Comparing files {0}'.format(str(files)))
    for i in range(0,len(files)):
        for j in range(i+1, len(files)):
            fname_a = files[i]
            fname_b = files[j]
            with _get_text_stream(fname_a) as file_a:
                with _get_text_stream(fname_b) as file_b:
                    print('sim({0},{1})={2}'.
                          format(fname_a, fname_b,
                                 measure_similarity(file_a, file_b)))    

def main():
    pairwise_compare(sys.argv[1:])

if __name__ == '__main__':
    main()
