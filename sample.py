from __future__ import(division, absolute_import, print_function,
                       unicode_literals)

from pysimsearch.sim_index import SimpleMemorySimIndex
from pysimsearch import doc_reader
from pysimsearch import similarity

# Compare web-page similarities
similarity.pairwise_compare('http://www.stanford.edu/',
                            'http://www.berkeley.edu/',
                            'http://www.ucla.edu',
                            'http://www.mit.edu/')

# Create an in-memory index and query it
sim_index = SimpleMemorySimIndex()
sim_index.index_files(
    doc_reader.get_named_text_files('http://www.stanford.edu/',
                                    'http://www.berkeley.edu',
                                    'http://www.ucla.edu',
                                    'http://www.mit.edu'))
print(sim_index.postings_list('university'))
print(list(sim_index.docnames_with_terms('university', 'california')))

