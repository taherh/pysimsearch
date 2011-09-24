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
RemoteSimIndex

Sample usage:

**Server**
::

    bash$ pysimsearch/sim_server.py sim_index -p 9001
    Use Control-C to exit


** pysimsearch Client **

>>> from pprint import pprint
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

import jsonrpclib as rpclib
#import xmlrpclib as rpclib

from . import SimIndex

class RemoteSimIndex(object):
    '''Proxy to a remote :class:`pysimsearch.sim_index.SimIndex`
    
    ``RemoteSimIndex`` is compatible with the :class:`SimIndex` interface,
    and provides access to a remote index.  We use this in place of
    directly using a jsonrpclib.Server() object because we need an object
    that acts like type :class:`SimIndex`.
    
    Instantiate a ``RemoteSimIndex`` as follows:
    
    >>> remote_index = RemoteSimIndex('http://localhost:9001/RPC2')
    >>> remote_index.query('university')
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
        else:
            raise Exception("Unsupported method: {}".format(name))

# RemoteSimIndex is a subtype of SimIndex    
SimIndex.register(RemoteSimIndex)


