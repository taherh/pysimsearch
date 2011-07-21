PySimSearch

Python library for indexing and similarity-search.
This library is primarily for pedagogical purposes, not production usage.  The
code here is meant to illustrate the basic workings of similarity and indexing
engines, without worrying about scalability.  Although scalability is essential
for any real indexing engine, the additional complexity that introduces often
obscures the simple concepts that drive modern information retrieval systems.

See sample.py for sample api usage

Sample command-line usage
--------------------------

Compute pair-wise similarity of 3 webpages:
bash$ python pysimsearch/similarity.py http://www.stanford.edu/ http://www.berkeley.edu/ http://www.mit.edu/
Comparing files ['http://www.stanford.edu/', 'http://www.berkeley.edu/', 'http://www.mit.edu/']
sim(http://www.stanford.edu/,http://www.berkeley.edu/)=0.322771960247
sim(http://www.stanford.edu/,http://www.mit.edu/)=0.142787018368
sim(http://www.berkeley.edu/,http://www.mit.edu/)=0.248877629741

--
