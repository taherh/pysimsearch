from distutils.core import setup
setup(
      name = "pysimsearch",
      packages = ["pysimsearch", "pysimsearch.sim_index", "pysimsearch.test"],
      version = "0.32",
      description = "Similarity-search library",
      author = "Taher Haveliwala",
      author_email = "oss@taherh.org",
      url = "https://github.com/taherh/pysimsearch",
      download_url = "https://github.com/downloads/taherh/pysimsearch/pysimsearch-0.32.tar.gz",
      keywords = ["similarity"],
      requires = ["httplib2", "lxml", "jsonrpclib", "futures"],
      license = "BSD License",
      classifiers = [
                     "Programming Language :: Python",
                     "License :: OSI Approved :: BSD License",
                     "Operating System :: OS Independent"
                     ],
      long_description = '''\
Similarity-Search Library
-------------------------

Requires Python v2.7.1 or higher
Library for measuring textual similarity of files and web pages and
building similarity indexes.  Primarily for pedagogical purposes.
'''
      )
