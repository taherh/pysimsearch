from distutils.core import setup
setup(
      name = "pysimsearch",
      packages = ["pysimsearch", "pysimsearch.test"],
      version = "0.20",
      description = "Similarity-search library",
      author = "Taher Haveliwala",
      author_email = "oss@taherh.org",
      url = "https://github.com/taherh/pysimsearch",
      download_url = "https://github.com/downloads/taherh/pysimsearch/pysimsearch-0.20.tar.gz",
      keywords = ["similarity"],
      requires = ["httplib2", "libxml"],
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
