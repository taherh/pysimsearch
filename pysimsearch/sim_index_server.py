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
SimIndexServer
=========

Server wrapper for sim_index

'''

from __future__ import (division, absolute_import, print_function,
        unicode_literals)

import collections

from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCRequestHandler

# Restrict to a particular path.
class RequestHandler(SimpleJSONRPCRequestHandler):
    rpc_paths = ('/RPC2',)
    
server = SimpleJSONRPCServer(('localhost', 9001),
                            logRequests = True,
                            requestHandler = RequestHandler)

SimpleJSONRPCServer.allow_none = True

from . import sim_index, query_scorer

class SimIndexService(object):
    '''Dispatches RPC requests to a SimpleMemorySimIndex'''

    PREFIX = 'sim_index'
    _SUPPORTED_METHODS = {'index_filenames',
                          'docid_to_name',
                          'name_to_docid',
                          'postings_list',
                          'docids_with_terms',
                          'docnames_with_terms',
                          'query',
                          'query_by_string'}
    def __init__(self):
        self._sim_index = sim_index.SimpleMemorySimIndex()
        self._sim_index.set_query_scorer(query_scorer.CosineQueryScorer())
    
    def _dispatch(self, method, params):
        print(str(params))
        if not method.startswith(self.PREFIX + '.'):
            raise Exception('method "{}" is not supported: bad prefix'.format(method))
        
        method_name = method.partition('.')[2]
        if method_name not in self._SUPPORTED_METHODS:
            raise Exception('method "{}" is not supported'.format(method_name))
            
        func = getattr(self._sim_index, method_name)
        r = None
        try:
            r = func(*params)
        except Exception as e:
            print('e={}'.format(str(e)))
        if isinstance(r, collections.Iterable):
            r = list(r)
        print('returning {}'.format(str(r)))
        return r

server.register_instance(SimIndexService())

try:
    print('Use Control-C to exit')
    server.serve_forever()
except KeyboardInterrupt:
    print('Exiting')
