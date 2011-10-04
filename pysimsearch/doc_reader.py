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
from concurrent import futures
import io
from itertools import chain
import re
import urllib

import lxml.html
from lxml.html.clean import clean_html

def get_text_file(filename):
    '''Returns file for filename
    
    TODO: detect html and parse
    '''
    return codecs.open(filename, encoding='utf-8')

def get_url(url):
    http_pattern = '^http://'
    if re.search(http_pattern, url):
        urlfh = urllib.urlopen(url)
        content = urlfh.read()
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

_executor = None

def get_urls(urls=None):
    '''
    Returns an iterator of (name, file) tuples for urls
    
    Params:
        urls: list of urls to fetch
    '''
    # The below effectively implements
    #
    #    return ((url, get_url(url)) for url in urls)
    #
    # but uses futures to allow parallel fetching/processing of urls
    
    # Initialize the executor if necessary
    global _executor
    if _executor is None:
        _executor = futures.ThreadPoolExecutor(max_workers=10)

    if urls is not None:
        # submit the get_url() requests
        future_to_url = {
            _executor.submit(get_url, url): url
            for url in urls
        }
        
        # generator that lazily iterates over futures and yields
        # (url, file) tuples
        def _gen_result():
            named_files = []
            for future in futures.as_completed(future_to_url, timeout=60):
                url = future_to_url[future]
                if future.exception() is not None:
                    raise Exception("failed to fetch {}: e=".format(url, future.exception()))
                else:
                    yield (url, future.result())

        # return iterator
        return _gen_result()
