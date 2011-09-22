from __future__ import(division, absolute_import, print_function,
                       unicode_literals)

from multiprocessing import Process
import time

from pprint import pprint

from pysimsearch.sim_index import MemorySimIndex
from pysimsearch.sim_index import RemoteSimIndex
from pysimsearch.sim_index import SimIndexCollection
from pysimsearch import similarity
from pysimsearch import sim_server

def sample_similarity():
    # Compare web-page similarities
    print()
    print("Printing pairwise similarities of university homepages")
    similarities = similarity.pairwise_compare(
        urls=['http://www.stanford.edu/',
              'http://www.berkeley.edu/',
              'http://www.ucla.edu',
              'http://www.mit.edu/'])
    pprint(similarities)

def sample_sim_index():            
    # Create an in-memory index and query it
    print()
    print("Creating in-memory index of university homepages")
    sim_index = MemorySimIndex()
    sim_index.index_urls('http://www.stanford.edu/',
                         'http://www.berkeley.edu',
                         'http://www.ucla.edu',
                         'http://www.mit.edu')
    
    print("Postings list for 'university':")
    pprint(sim_index.postings_list('university'))
    print("Pages containing terms 'university' and 'california'")
    pprint(list(sim_index.docnames_with_terms('university', 'california')))
    
    # Issue some similarity queries
    print()
    print("Similarity search for query 'stanford university' (simple scorer)")
    sim_index.set_query_scorer('simple_count')
    pprint(list(sim_index.query("stanford university")))
    
    print()
    print("Similarity search for query 'stanford university' (tf.idf scorer)")
    sim_index.set_query_scorer('tfidf')
    pprint(list(sim_index.query("stanford university")))
    
    # Save the index to disk, then load it back in
    print()
    print("Saving index to disk")
    with open("myindex.idx", "w") as index_file:
        sim_index.save(index_file)
    
    print()
    print("Loading index from disk")
    with open("myindex.idx", "r") as index_file:
        sim_index2 = MemorySimIndex.load(index_file)
    
    print()
    print("Pages containing terms 'university' and 'california' in loaded index")
    pprint(list(sim_index2.docnames_with_terms('university', 'california')))

def sample_sim_index_collection():
    # SimIndexCollection
    print()
    print("SimIndexCollection: build a collection, index some urls, and query it")
    indexes = (MemorySimIndex(), MemorySimIndex())
    index_coll = SimIndexCollection()
    index_coll.add_shards(*indexes)
    index_coll.set_query_scorer('tfidf')
    index_coll.index_urls('http://www.stanford.edu/',
                          'http://www.berkeley.edu',
                          'http://www.ucla.edu',
                          'http://www.mit.edu')
    
    pprint(index_coll.query('stanford university'))

def sample_remote_indexes():    
    print()
    print("SimIndexCollection with remote backend indexes")
    
    processes = []
    for i in range(2):
        port = 9000 + i
        process = Process(target=sim_server.start_sim_index_server,
                          kwargs={'port': port, 'logRequests': False})
        process.daemon = True
        processes.append(process)
        
    for process in processes:
        process.start()
        
    print("Waiting for servers to start")
    time.sleep(1)

    remote_index_coll = SimIndexCollection()        
    for i in range(2):
        port = 9000 + i
        remote_index_coll.add_shards(
            RemoteSimIndex("http://localhost:{}/RPC2".format(port)))
        
    remote_index_coll.set_query_scorer('tfidf')

    remote_index_coll.index_urls('http://www.stanford.edu/',
                                 'http://www.berkeley.edu',
                                 'http://www.ucla.edu',
                                 'http://www.mit.edu')
    
    pprint(remote_index_coll.query('stanford university'))
        
    for process in processes:
        process.terminate()

if __name__ == '__main__':
    sample_similarity()
    sample_sim_index()
    sample_sim_index_collection()
    sample_remote_indexes()
    pprint('done!')
