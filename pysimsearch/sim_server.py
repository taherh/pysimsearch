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
SimServer

Server wrapper for pysimsearch modules.  Currently, only provides access
to sim_index.

*Sample session:*

**Server**
::

    bash$ ./sim_server.py sim_index -p 9001
    Use Control-C to exit

**jsonrpclib Client**

>>> from pprint import pprint
>>> import jsonrpclib
>>> server = jsonrpclib.Server('http://localhost:9001/RPC2')
>>> server.sim_index.index_urls('http://www.stanford.edu/', 'http://www.berkeley.edu', 'http://www.ucla.edu')
>>> pprint(server.sim_index.query('university'))
[[u'http://www.stanford.edu/', 0.10469570845856098],
 [u'http://www.ucla.edu', 0.04485065887313478],
 [u'http://www.berkeley.edu', 0.020464326883958977]]

** pysimsearch Client **
>>> from pysimsearch import sim_index
>>> index = sim_index.RemoteSimIndex('http://localhost:9001/RPC2')
>>> index.index_urls('http://www.stanford.edu/', 'http://www.berkeley.edu', 'http://www.ucla.edu')
>>> pprint(index.query('university'))
[[u'http://www.stanford.edu/', 0.10469570845856098],
 [u'http://www.ucla.edu', 0.04485065887313478],
 [u'http://www.berkeley.edu', 0.020464326883958977]]

'''

from __future__ import (division, absolute_import, print_function,
        unicode_literals)

# boilerplate to allow running as script
if __name__ == "__main__" and __package__ is None:
    import sys, os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    import pysimsearch
    __package__ = str("pysimsearch")
    del sys, os
    
# external modules
import argparse
import logging
import traceback
import types

from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer as SimpleRPCServer
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCRequestHandler as SimpleRPCRequestHandler

#from SimpleXMLRPCServer import SimpleXMLRPCServer as SimpleRPCServer
#from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler as SimpleRPCRequestHandler

# our modules
from . import sim_index, query_scorer

class SimIndexService(object):
    '''Provide access to sim_index as an RPC service'''

    PREFIX = 'sim_index'
    EXPORTED_METHODS = {'index_urls',
                        'index_string_buffers',
                        'docid_to_name',
                        'name_to_docid',
                        'postings_list',
                        'docids_with_terms',
                        'docnames_with_terms',
                        'set_query_scorer',
                        'query',
                        'set_global_N',
                        'get_local_N',
                        'set_global_df_map',
                        'get_global_df_map',
                        'get_local_df_map',
                        'get_name_to_docid_map',
                        'config',
                        'set_config',
                        'update_config'}
    
    def __init__(self):
        self._sim_index = sim_index.MemorySimIndex()
        self._sim_index.set_query_scorer(query_scorer.TFIDFQueryScorer())
    
    def _dispatch(self, method, params):
        if not method.startswith(self.PREFIX + '.'):
            raise Exception('method "{}" is not supported: bad prefix'.format(method))

        method_name = method.partition('.')[2]

        logging.info('_dispatch: {}'.format(method))
        
        if method_name not in self.EXPORTED_METHODS:
            raise Exception('method "{}" is not supported'.format(method_name))
            
        func = getattr(self._sim_index, method_name)
        try:
            if type(params) is types.ListType:
                r = func(*params)
            else:
                r = func(**params)
            # if we got back a generator, then let's materialize a list so it
            # can serialize properly
            if isinstance(r, types.GeneratorType):
                r = list(r)
            return r
        except Exception as e:
            logging.error(traceback.format_exc())
            raise e

# Restrict to a particular path.
class RequestHandler(SimpleRPCRequestHandler):
    rpc_paths = ('/RPC2',)

def start_sim_index_server(port, logRequests = True):
    server = SimpleRPCServer(('localhost', port),
                             logRequests = logRequests,
                             requestHandler = RequestHandler)
    
    server.register_instance(SimIndexService())

    try:
        print('Use Control-C to exit')
        server.serve_forever()
    except KeyboardInterrupt:
        print('Exiting')


# --- main() ---

def main():
    parser = argparse.ArgumentParser(
        description='Start a pysimsearch server')
    parser.add_argument('command',
                        choices=['sim_index'],
                        help='Specify the pysimsearch service to start')
    parser.add_argument('-p', '--port', nargs='?', default=9001, type=int,
                        help='Specify server port')

    args = parser.parse_args()

    if args.command == 'sim_index':
        start_sim_index_server(args.port)
    else:
        raise Exception('Unknown command: {}'.format(args.command))
        
if __name__ == '__main__':
    main()
    
