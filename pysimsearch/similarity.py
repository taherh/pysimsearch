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
@author: taherh

Sample usage as a script:
$ python similarity.py http://www.stanford.edu/ http://www.berkeley.edu/ http://www.mit.edu/
Comparing files ['http://www.stanford.edu/', 'http://www.berkeley.edu/', 'http://www.mit.edu/']
sim(http://www.stanford.edu/,http://www.berkeley.edu/)=0.322771960247
sim(http://www.stanford.edu/,http://www.mit.edu/)=0.142787018368
sim(http://www.berkeley.edu/,http://www.mit.edu/)=0.248877629741

'''
from __future__ import division, absolute_import, print_function, unicode_literals

import codecs
import sys
import math
import re
import io
import httplib2
import lxml.html
from lxml.html.clean import clean_html

# --- top-level functions ---
def measure_similarity(file_a, file_b, sim_func = None):
    '''
    Returns the textual similarity of file_a and file_b using chosen similarity metric
    'sim_func' defaults to cosine_sim if not specified
    Consumes file_a and file_b
    '''
    if sim_func == None: sim_func = cosine_sim  # default to cosine_sim
    
    u = term_vec(file_a)
    v = term_vec(file_b)
    
    return sim_func(u, v)

def pairwise_compare(filenames, sim_func = None):
    '''
    Does a pairwise comparison of the entries in 'filenames' and prints similarities
    '''
    print('Comparing files {0}'.format(str(filenames)))
    for i in range(0,len(filenames)):
        for j in range(i+1, len(filenames)):
            fname_a = filenames[i]
            fname_b = filenames[j]
            with get_text_stream(fname_a) as file_a:
                with get_text_stream(fname_b) as file_b:
                    print('sim({0},{1})={2}'.
                          format(fname_a, fname_b,
                                 measure_similarity(file_a, file_b, sim_func)))
  
# --- Similarity measures ---
    
def cosine_sim(u, v):
    '''
    Returns the cosine similarity of u,v: <u,v>/(|u||v|)
    where |u| is the L2 norm
    '''
    return dot_product(u, v) / (l2_norm(u) * l2_norm(v))

def jaccard_sim(A, B):
    r'''
    Returns the Jaccard similarity of A,B: |A \cap B| / |A \cup B|
    We treat A and B as multi-sets (The Jaccard coefficient is technically defined over sets)
    '''
    return mag_intersect(A, B) / mag_union(A, B)

# --- Term-vector operations ---

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

# another name for l2_norm()
magnitude = l2_norm

# --- Utilities for creating term vectors from data ---

def term_vec(file):
    '''Returns a term vector for 'file', represented as a dictionary mapping {term->frequency}'''
    
    tf_dict = {}
    for line in file:
        for term in line.split():
            if not term in tf_dict: tf_dict[term] = 0
            tf_dict[term] += 1
    return tf_dict

# get_text_stream() needs an http object
_h = httplib2.Http(str('.cache'))  # httplib2 doesn't like unicode for cachefile name

def get_text_stream(name):
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
        file  = codecs.open(name, encoding='utf-8')
    return file

# --- Support for TFIDF weighting ---
def parse_df(file):
    '''
    Parses a document frequency file for use in applying df term weighting
    '''
    df_dict = {}
    for line in file:
        ln_list = line.split()
        if len(ln_list) == 0: continue  # skip blank lines without warning
        if len(ln_list) != 2:  # raise exception if there were not exactly two entries in the line
            raise FileFormatException(
                'Bad line in doc freq file ({0} entries, expecting 2): {1}'.
                format(len(ln_list), line))
        (term, df) = ln_list
        df_dict[term] = int(df)
    return df_dict

def write_df(df_dict, file):
    '''
    Writes the document frequency data structure to file
    TODO: sort order?
    '''
    for (term, df) in df_dict.items():
        file.write(u'{0}\t{1}\n'.format(term, df))
    
def compute_df(files):
    '''
    Creates a document frequency count by processing a collection of files
    '''
    df_dict = {}
    for file in files:
        term_seen = set()
        for line in file:
            for term in line.split():
                if term not in term_seen:
                    if term not in df_dict: df_dict[term] = 0
                    df_dict[term]+=1
                    term_seen.add(term)
    return df_dict

# --- Exceptions ---
class Error(Exception):
    '''Base class for Exception types used in this module'''
    pass

class FileFormatException(Exception):
    pass
    
# --- main() ---

def main():
    pairwise_compare(sys.argv[1:])

if __name__ == '__main__':
    main()
