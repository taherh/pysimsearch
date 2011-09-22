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
Utilities for creating term vectors from data
'''

from __future__ import(division, absolute_import, print_function,
                       unicode_literals)

import codecs
import io
from itertools import chain
import re


import httplib2
import lxml.html
from lxml.html.clean import clean_html

# get_text_file() needs an http object
_HTTP = httplib2.Http(str('.cache'))  # httplib2 doesn't like unicode arg

def get_text_file(filename):
    '''Returns file for filename
    
    TODO: detect html and parse
    '''
    return codecs.open(filename, encoding='utf-8')

def get_url(url):
    http_pattern = '^http://'
    if re.search(http_pattern, url):
        (response, content) = _HTTP.request(url)
        html_tree = lxml.html.fromstring(content)
        clean_html(html_tree)  # removes crud from html
        clean_html_string = lxml.html.tostring(html_tree, 
                                               encoding=unicode,
                                               method='text')
        return io.StringIO(clean_html_string)
    else:
        raise Exception("Bad url: {}".format(url))

def get_text_files(filenames=None):
    '''
    Returns an iterator of (name, file) tuples for filenames
    
    Params:
        filenames: list of filenames
    '''
    if filenames is not None:
        return ((name, get_text_file(name)) for name in filenames)
    
def get_urls(urls=None):
    '''
    Returns an iterator of (name, file) tuples for urls
    
    Params:
        urls: list of urls to fetch
    '''
    if urls is not None:
        return ((url, get_url(url)) for url in urls)
    
def term_vec(input, stoplist = None):
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
                    if term not in tf_dict: tf_dict[term] = 0
                    tf_dict[term] += 1
        return tf_dict
