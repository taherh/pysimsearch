#!/usr/bin/env python

# Copyright (c) 2011, Taher Haveliwala <oss@taherh.org>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#         * Redistributions of source code must retain the above copyright
#           notice, this list of conditions and the following disclaimer.
#         * Redistributions in binary form must reproduce the above copyright
#           notice, this list of conditions and the following disclaimer in the
#           documentation and/or other materials provided with the distribution.
#         * The names of project contributors may not be used to endorse or
#           promote products derived from this software without specific
#           prior written permission.
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
Similarity index module.

Sample usage::

    from pysimsearch.sim_index import SimpleMemorySimIndex
    from pysimsearch import doc_reader

    sim_index = SimpleMemorySimIndex()
    sim_index.index_filenames('http://www.stanford.edu/',
                              'http://www.berkeley.edu',
                              'http://www.ucla.edu',
                              'http://www.mit.edu')
    print(sim_index.postings_list('university'))
    print(list(sim_index.docnames_with_terms('university', 'california')))
    
    sim_index.set_query_scorer('simple_count')
    print(list(sim_index.query_by_string("stanford university")))

'''

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

import abc
import io
import itertools
import operator
from pprint import pprint
import sys
import types

import jsonrpclib as rpclib
#import xmlrpclib as rpclib

from .sim_index import SimIndex

class RemoteSimIndex(object):
    '''Proxy to a remote ``SimIndex``
    
    ``RemoteSimIndex`` is compatible with the ``SimIndex`` interface,
    and provides access to a remote index.  We use this in place of
    directly using a jsonrpclib.Server() object because we need an object
    that acts like type ``SimIndex``.
    
    Instantiate a ``RemoteSimIndex`` as follows:
    
    >>> remote_index = RemoteSimIndex('http://localhost:9001/RPC2')
    >>> remote_index.query_by_string('university')
    ...
    
    '''
    
    def __init__(self, server_url):
        '''Initialize with server_url
        
        Params:
            server_url: url for remote ``SimIndex`` server
        '''
        from .. import sim_server
        self.PREFIX = sim_server.SimIndexService.PREFIX
        self.EXPORTED_METHODS = sim_server.SimIndexService.EXPORTED_METHODS
        self._server = rpclib.Server(server_url)
        
    def __getattr__(self, name):
        if name in self.EXPORTED_METHODS:
            func = getattr(self._server,
                           self.PREFIX + '.' + name)
            return func

# RemoteSimIndex is a subtype of SimIndex    
SimIndex.register(RemoteSimIndex)


