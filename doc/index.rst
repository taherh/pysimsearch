.. PySimSearch documentation master file, created by
   sphinx-quickstart on Mon Jul 25 22:06:33 2011.

pysimsearch 1.2.5 documentation
=======================================

Python library for indexing and similarity-search.

This library is primarily for pedagogical purposes, not production usage.  The
code here is meant to illustrate the basic workings of similarity and indexing
engines, without worrying about scalability.  Although scalability is essential
for any real indexing engine, the additional complexity that introduces often
obscures the simple concepts that drive modern information retrieval systems.
Although it is currently for Python 2.7 series, we use `__future__` imports
to match Python 3 as closely as possible.

Quickstart:
-----------

*Quick sample:*

>>> from pprint import pprint
>>> from pysimsearch import sim_index, doc_reader
>>> index = sim_index.SimpleMemorySimIndex()
>>> index.index_filenames('http://www.stanford.edu/',
		          'http://www.berkeley.edu/',
		          'http://www.ucla.edu',
		          'http://www.mit.edu')
>>> pprint(index.postings_list('university'))
[(0, 3), (1, 1), (2, 1)]
>>> pprint(list(index.docnames_with_terms('university', 'california')))
['http://www.stanford.edu/', 'http://www.ucla.edu']
>>> index.set_query_scorer('tfidf')
>>> pprint(list(index.query_by_string("stanford university")))
[('http://www.stanford.edu/', 0.5827172819606118),
 ('http://www.ucla.edu', 0.05801461340864149),
 ('http://www.berkeley.edu/', 0.025725104682131295)]

View a larger :doc:`sample`
    
API:
----

.. toctree::
   :maxdepth: 2

   sim_index
   similarity
   doc_reader
   freq_tools
   sim_server
   query_scorer
   term_vec

.. automodule:: pysimsearch
   :members:




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

