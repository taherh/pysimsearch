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
ConcurrentSimIndex

Wrapper to allow concurrent SimIndex access

Sample usage::

    from pysimsearch.sim_index import MemorySimIndex, ConcurrentSimIndex

    index = ConcurrentSimIndex(MemorySimIndex())
    index.index_urls('http://www.stanford.edu/', 'http://www.berkeley.edu')
    print(list(index.query('stanford')))

'''

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from concurrent import futures
import threading

from . import SimIndex

class ConcurrentSimIndex(object):
    '''Proxy to a :class:`pysimsearch.sim_index.SimIndex` that allows
    concurrent access.
    
    ``ConcurrentSimIndex`` is compatible with the :class:`SimIndex` interface.
    We use ``concurrent.futures`` to allow some basic concurrency for indexing
    and querying.  In particular, calls to ``index_urls()`` are executed in a
    nonblocking manner.
    '''

    READ_METHODS = {'name_to_docid',
                    'docid_to_name',
                    'postings_list',
                    'docids_with_terms',
                    'docnames_with_terms',
                    'query',
                    'get_local_N',
                    'get_local_df_map',
                    'get_name_to_docid_map',
                    'config'}
    
    WRITE_METHODS = {'set_query_scorer',
                     'set_global_N',
                     'set_global_df_map',
                     'load_stoplist',
                     'set_config',
                     'update_config',
                     'index_string_buffers',
                     'index_files',
                     'del_docids',
                     }
    
    # Note:  assume that index_urls() is implemented by calling index_files()
    #        so that the write-lock will be acquired at the time index_files()
    #        is called.  We don't want to acquire a lock on index_urls()
    #        directly, as we'd like allow at least the url fetches to occur
    #        concurrently.
    #
    # TODO: re-implement index_urls() here to ensure the assumption is true?
    NONBLOCKING_METHODS = { 'index_urls' }

    
    def __init__(self, sim_index):
        '''Initialize with ``sim_index``
        
        Params:
            sim_index: A :class:`SimIndex` instance.
        '''
        self._sim_index = sim_index
        self._executor = futures.ThreadPoolExecutor(max_workers=10)
        self._lock = threading.RLock()  # TODO: use a Read-Write Lock
        self._futures = set()
    
    def acquire_read_lock(self):
        '''Acquire read lock'''
        self._lock.acquire()
    
    def release_read_lock(self):
        '''Release read lock'''
        self._lock.release()
    
    def acquire_write_lock(self):
        '''Acquire write lock'''
        self._lock.acquire()
        
    def release_write_lock(self):
        '''Release write lock'''
        self._lock.release()
        
    def _read_decorator(self, func):
        '''Wrap func with read_lock protection'''
        def wrapper(*args, **kwargs):
            self.acquire_read_lock()
            try:
                return func(*args, **kwargs)
            finally:
                self.release_read_lock()
        return wrapper

    def _write_decorator(self, func):
        '''Wrap func with write_lock protection'''
        def wrapper(*args, **kwargs):
            self.acquire_write_lock()
            try:
                return func(*args, **kwargs)
            finally:
                self.release_write_lock()
        return wrapper
    
    def _nonblocking_decorator(self, func):
        '''
        Wrap func with non-blocking futures call.
        Return value of ``func`` is ignored.
        '''
        def wrapper(*args, **kwargs):
            future = self._executor.submit(func, *args, **kwargs)
            self._futures.add(future)
        return wrapper

    def _futures_wait(self):
        if len(self._futures) > 0:
            r = futures.wait(self._futures)
            for future in r.done:
                if future.exception() is not None:
                    raise future.exception()
        self._futures = set()

    def __getattr__(self, name):
        func = getattr(self._sim_index, name)
        
        if name in self.READ_METHODS:
            # wait for any outstanding non-blocking calls to complete
            self._futures_wait()
            return self._read_decorator(func)
        elif name in self.WRITE_METHODS:
            # wait for any outstanding  non-blocking calls to complete
            return self._write_decorator(func)
        elif name in self.NONBLOCKING_METHODS:
            return self._nonblocking_decorator(func)
        else:
            raise Exception("Unsupported method: {}".format(name))

# ConcurrentSimIndex is a subtype of SimIndex    
SimIndex.register(ConcurrentSimIndex)
