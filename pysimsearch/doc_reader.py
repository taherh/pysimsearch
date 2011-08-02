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
import re
import io
import httplib2
import lxml.html
from lxml.html.clean import clean_html

# get_text_file() needs an http object
_HTTP = httplib2.Http(str('.cache'))  # httplib2 doesn't like unicode arg

def get_text_file(name):
    '''Returns a text stream from filename or url'''
    file = None
    http_pattern = '^http://'
    if re.search(http_pattern, name):
        (response, content) = _HTTP.request(name)
        html_tree = lxml.html.fromstring(content)
        clean_html(html_tree)  # removes crud from html
        clean_html_string = lxml.html.tostring(html_tree, 
                                               encoding=unicode, method='text')
        file = io.StringIO(clean_html_string)
    else:
        file = codecs.open(name, encoding='utf-8')
    return file

def get_text_files(*names):
    '''Returns iterator of files from filenames and/or urls'''
    return (get_text_file(name) for name in names)

def get_named_text_files(*names):
    '''
    Returns an iterator of (filename, file) tuples from filenames
    and/or urls (convenience function)
    '''
    return zip(names, get_text_files(*names))
    
def term_vec(file):
    '''
    Returns a term vector for 'file', represented as a dictionary
    of the form {term: frequency}
    
    Takes ownership of file   
    '''
    
    with file as f:
        tf_dict = {}
        for line in f:
            for term in line.split():
                if not term in tf_dict:
                    tf_dict[term] = 0
                tf_dict[term] += 1
        return tf_dict
    
def term_vec_from_string(s):
    '''
    Returns term vector for string s, represented as a dictionary of the
    from {term: frequency}

    (Convenience function - wraps term_vec())
    '''
    return term_vec(io.StringIO(s))
    