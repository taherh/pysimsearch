from __future__ import(division, absolute_import, print_function,
                       unicode_literals)

from pprint import pprint

from pysimsearch.sim_index import SimpleMemorySimIndex
from pysimsearch.sim_index import SimIndexCollection
from pysimsearch import doc_reader
from pysimsearch import similarity
from pysimsearch import query_scorer

## pysimsearch.similarity

# Compare web-page similarities
print()
print("Printing pairwise similarities of university homepages")
similarities = similarity.pairwise_compare_filenames('http://www.stanford.edu/',
                                                     'http://www.berkeley.edu/',
                                                     'http://www.ucla.edu',
                                                     'http://www.mit.edu/')
pprint(similarities)

## pysimsearch.sim_index

# Create an in-memory index and query it
print()
print("Creating in-memory index of university homepages")
sim_index = SimpleMemorySimIndex()
sim_index.index_filenames('http://www.stanford.edu/',
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
pprint(list(sim_index.query(
    doc_reader.term_vec_from_string("stanford university"))))

print()
print("Similarity search for query 'stanford university' (tf.idf scorer)")
sim_index.set_query_scorer('tfidf')
pprint(list(sim_index.query(
    doc_reader.term_vec_from_string("stanford university"))))

# Save the index to disk, then load it back in
print()
print("Saving index to disk")
with open("myindex.idx", "w") as index_file:
    sim_index.save(index_file)

print()
print("Loading index from disk")
with open("myindex.idx", "r") as index_file:
    sim_index2 = SimpleMemorySimIndex.load(index_file)

print()
print("Pages containing terms 'university' and 'california' in loaded index")
pprint(list(sim_index2.docnames_with_terms('university', 'california')))

# SimIndexCollection
print()
print("SimIndexCollection")
index1 = SimpleMemorySimIndex()
index2 = SimpleMemorySimIndex()
index_coll = SimIndexCollection()
index_coll.add_shards(index1, index2)
index_coll.set_query_scorer('tfidf')
index_coll.index_string_buffers((('d1', 'hello there'),
                                 ('d2', 'what are you'),
                                 ('d3', 'ok thats enough'),
                                 ('d4', 'wait what hello')))

pprint(index_coll.query_by_string('hello ok enough'))
