#!/usr/bin/env python

# Copyright (c) 2010, Taher Haveliwala <oss@taherh.org>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * The names of project contributors may not be used to endorse or
#       promote products derived from this software without specific
#       prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''
Sample usage as a script::

    $ python freq_tools --list doc_list -o output.df
    Processing...
'''

from __future__ import (division, absolute_import, print_function,
    unicode_literals)

# boilerplate to allow running as script
if __name__ == "__main__" and __package__ is None:
    import sys, os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    import pysimsearch
    __package__ = str("pysimsearch")
    del sys, os

# external modules
import argparse
import sys

# our modules
from .exceptions import *
from . import doc_reader

def read_df(df_file):
    '''
    Reads a document frequency file for use in applying df term weighting
    Returns a dictionary of the form {term: doc_freq}
    '''
    df_dict = {}
    for line in df_file:
        ln_list = line.split()
        if len(ln_list) == 0:
            continue  # skip blank lines without warning
        if len(ln_list) != 2:   # raise exception if there were not exactly
                                # two entries in the line
            raise FileFormatException(
                'Bad line in doc freq file ({0} entries, expecting 2): {1}'.
                format(len(ln_list), line))
        (term, df) = ln_list
        df_dict[term] = int(df)
    return df_dict

def write_df(df_dict, df_file):
    '''
    Writes the document frequency data structure to file
    df_dict is a dictionary of the form {term: doc_freq}
    
    TODO: sort order?
    '''
    for (term, df) in df_dict.items():
        df_file.write(u'{0}\t{1}\n'.format(term, df))
    
def compute_df(files):
    '''
    Computes document frequency counts by processing a collection of files
    Returns a dictionary of the form {term: doc_freq}
    '''
    df_dict = {}
    for file in files:
        term_seen = set()
        for line in file:
            for term in line.split():
                if term not in term_seen:
                    if term not in df_dict:
                        df_dict[term] = 0
                    df_dict[term] += 1
                    term_seen.add(term)
                    
    return df_dict
    
# --- main() ---

def main():
    '''Commandline interface for generating document frequency indexes'''
    parser = argparse.ArgumentParser(
        description='Compute document frequencies of terms in of input '
                    'documents')
    parser.add_argument('doc', nargs='*', help='a document filename')
    parser.add_argument('-l', '--list', nargs='?',
                        help='file containing list of input documents')
    parser.add_argument('-o', '--output', nargs='?',
                        help='output file (default: stdout)')

    args = parser.parse_args()

    output_file = sys.stdout
    if args.output != None:
        output_file = open(args.output, "w")
        
    doc_list = []
    if args.list != None:
        try:
            with open(args.list) as input_docnames_file:
                doc_list = [line.strip() for line in
                            input_docnames_file.readlines()]
        except IOError:
            print("Sorry, could not open " + args.list)

    doc_list.extend(args.doc)

    print("Processing {}".format(str(doc_list)))
    
    if len(doc_list) == 0:
        raise Error("Sorry, you must specify at least one document.")  

    df_dict = compute_df(doc_reader.get_text_files(*doc_list))
    for key in df_dict:
        print('{}\t{:>20}'.format(key, df_dict[key]), file=output_file)

    if output_file != sys.stdout:
        output_file.close()

if __name__ == '__main__':
    main()

