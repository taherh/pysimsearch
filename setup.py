from distutils.core import setup
setup(
      name = "pysimsearch",
      packages = ["pysimsearch", "pysimsearch.test"],
      version = "0.1",
      description = "Similarity-search library",
      author = "Taher Haveliwala",
      url = "http://code.google.com/p/pysimsearch/",
      keywords = ["similarity"],
      classifiers = [
                     "Programming Language :: Python",
                     "License :: OSI Approved :: BSD License",
                     "Operating System :: OS Independent"
                     ],
      long_description = '''\
Similarity-Search Library
-------------------------

Utilities for measuring textual similarity of files and web pages.               
'''
      )
