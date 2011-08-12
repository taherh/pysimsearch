PySimSearch
===========

Python library for indexing and similarity-search.

This library is primarily for pedagogical purposes, not production usage.  The
code here is meant to illustrate the basic workings of similarity and indexing
engines, without worrying about scalability.  Although scalability is essential
for any real indexing engine, the additional complexity that introduces often
obscures the simple concepts that drive modern information retrieval systems.
Although it is currently for Python 2.7 series, we use `__future__` imports
to match Python 3 as closely as possible.

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
    
    from pysimsearch.sim_index import SimpleMemorySimIndex
    from pysimsearch import doc_reader
    from pysimsearch import similarity
    from pysimsearch import query_scorer
    
    # Compare web-page similarities
    print("Printing pairwise similarities of university homepages")
    similarity.pairwise_compare('http://www.stanford.edu/',
                                'http://www.berkeley.edu/',
                                'http://www.ucla.edu',
                                'http://www.mit.edu/')
    
    # Create an in-memory index and query it
    print("Creating in-memory index of university homepages")
    sim_index = SimpleMemorySimIndex()
    sim_index.index_files(
        doc_reader.get_named_text_files('http://www.stanford.edu/',
                                        'http://www.berkeley.edu',
                                        'http://www.ucla.edu',
                                        'http://www.mit.edu'))
    print("Postings list for 'university':")
    print(sim_index.postings_list('university'))
    print("Pages containing terms 'university' and 'california'")
    print(list(sim_index.docnames_with_terms('university', 'california')))
    
    # Issue some similarity queries
    print("Similarity search for query 'stanford university'")
    sim_index.set_query_scorer(query_scorer.SimpleCountQueryScorer())
    print(list(sim_index.query(
        doc_reader.term_vec_from_string("stanford university"))))