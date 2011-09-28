pysimsearch
===========

Python library for indexing and similarity-search.

Full documentation is at http://taherh.github.com/pysimsearch/

This library is primarily meant to illustrate the basic workings of similarity
and indexing engines, without focusing heavily on optimization.  Certain
patterns used for scaling indexes (e.g., distributed indexes) are included.

Although the code is currently for Python 2.7 series, we use ``__future__``
imports to match Python 3 as closely as possible.

If you are interested in learning more about search and information retrieval,
I highly recommend the following two books:

* [Managing Gigabytes](http://amzn.to/qg6Zhe), by Witten, Moffat, and Bell
* [Introduction to Information Retrieval](http://amzn.to/oz2O27), by Manning, Schütze, and Raghavan

Sample command-line usage
-------------------------

Compute pair-wise similarity of 3 webpages:

    bash$ python pysimsearch/similarity.py http://www.stanford.edu/ http://www.berkeley.edu/ http://www.mit.edu/
    Comparing files ['http://www.stanford.edu/', 'http://www.berkeley.edu/', 'http://www.mit.edu/']
    sim(http://www.stanford.edu/,http://www.berkeley.edu/)=0.322771960247
    sim(http://www.stanford.edu/,http://www.mit.edu/)=0.142787018368
    sim(http://www.berkeley.edu/,http://www.mit.edu/)=0.248877629741

Sample API usage
----------------

    from __future__ import(division, absolute_import, print_function,
                           unicode_literals)
    
    from pprint import pprint
    from pysimsearch.sim_index import MemorySimIndex
    from pysimsearch import doc_reader
    from pysimsearch import similarity
        
    # Compare web-page similarities
    print("Printing pairwise similarities of university homepages")
    pprint(similarity.pairwise_compare(urls=['http://www.stanford.edu/',
                                             'http://www.berkeley.edu/',
                                             'http://www.ucla.edu',
                                             'http://www.mit.edu/']))
    
    # Create an in-memory index and query it
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
    print("Similarity search for query 'stanford university'")
    sim_index.set_query_scorer('simple_count')
    pprint(list(sim_index.query('stanford university')))


Sample Client/Server Usage via JSON api
---------------------------------------

*Server*

    bash$ ./sim_server.py sim_index -p 9001
    Use Control-C to exit

*Client*

    >>> from pprint import pprint
    >>> import jsonrpclib
    >>> server = jsonrpclib.Server('http://localhost:9001/RPC2')
    >>> server.sim_index.index_urls('http://www.stanford.edu/', 'http://www.berkeley.edu', 'http://www.ucla.edu')
    >>> pprint(server.sim_index.query('stanford university'))
    [[u'http://www.stanford.edu', 0.4396892551666724],
     [u'http://www.berkeley.edu', 0.0],
     [u'http://www.ucla.edu', 0.0]]


Sample SimIndexCollection Usage
-------------------------------

*Server*

    bash$ ./sim_server.py sim_index -p 9001 &
    bash$ ./sim_server.py sim_index -p 9002 &

*SimIndexCollection*

    >>> from pprint import pprint
    >>> from pysimsearch.sim_index import SimIndexCollection
    >>> from pysimsearch.sim_index import RemoteSimIndex
    >>> servers = [
                    RemoteSimIndex('http://localhost:9001/RPC2'),
                    RemoteSimIndex('http://localhost:9002/RPC2')
                  ]
    >>> index_coll = SimIndexCollection()
    >>> index_coll.add_shards(*servers)
    >>> index_coll.set_query_scorer('tfidf')
    >>> index_coll.index_urls('http://www.stanford.edu/',
                              'http://www.berkeley.edu',
                              'http://www.ucla.edu',
                              'http://www.mit.edu')
    >>> pprint(index_coll.query("stanford university"))
    [[u'http://www.stanford.edu/', 0.5836102697341475],
     [u'http://www.ucla.edu', 0.012839879268194701],
     [u'http://www.berkeley.edu', 0.005337522642134812]]
