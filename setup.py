from distutils.core import setup
setup(
      name = "pysimsearch",
      packages = ["pysimsearch", "pysimsearch.test"],
      version = "0.15",
      description = "Similarity-search library",
      author = "Taher Haveliwala",
      author_email = "oss@taherh.org",
      url = "http://code.google.com/p/pysimsearch/",
      download_url = "http://pysimsearch.googlecode.com/files/pysimsearch-0.1.tar.gz",
      keywords = ["similarity"],
      requires = ["httplib2", "libxml"],
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
