#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Plot csv data.

Inuput fields:
    <A> -- plot name (output file)
    <B> -- graph name (on the same plot)
    <X> -- x-coordinate
    <Y> -- y-coordinate or a value to histogram
"""

import os
import sys
import argparse

import graph

from collections import defaultdict
from util import natural_keys


GRAPH_COL_INDEXES = (0, 1, 2, 3)  # A, B, X, Y
HIST_COL_INDEXES = (0, None, 2)  # A, B, Y;  None will be replaced with a filename



def parse_args():
    parser = argparse.ArgumentParser(description=__doc__,
            formatter_class=argparse.RawTextHelpFormatter)
    
    subparsers = parser.add_subparsers() #https://docs.python.org/3/library/argparse.html#sub-commands
    
    parser_graph = subparsers.add_parser('graph', help='X-Y graph.')
    parser_hist  = subparsers.add_parser('hist', help='histogram.')
    
    # Graph
    parser_graph.add_argument( 'infiles',
            type=argparse.FileType('r'),
            nargs='*',
            default=[sys.stdin],
            help='the files with data records'
            )

    
    
    return parser.parse_args()


def parse_input(infiles, indexes = GRAPH_COL_INDEXES):
    """ Generator, yields data form files.
        Parses a file with data records, yields fields with specified indexes.
    """
    
    for idx, fd in enumerate(infiles):
        filename = fd.name

        for line in fd:
            if line[0] == "#":  # ignore comments
                continue

            fields = line.split()
            
            try:
                yield tuple([ fields[idx] if idx is not None else filename for idx in indexes])
            
            except IndexError as e:
                #~ logging.error('%s , line: %d' % (e, lineno) )
                raise


def get_data(files, columns):
    """ Convert records to dict of dicts.
    """
    indexes = (0,1,2,3)  # A,B,X,Y
    parser = parse_input(files, indexes)
    
    data = dict()
    for vals in parser:
        
        A, B, X, Y = vals
        
        try:
            data[A][B][0].append(X)
            data[A][B][1].append(Y)

        except KeyError:
            if A not in data:
                data[A] = dict()
            if B not in data[A]:
                data[A][B] = ([],[])
            
            data[A][B][0].append(X)
            data[A][B][1].append(Y)

    return data

def main():
    args=parse_args()
    #~ print args
    
    indexes = GRAPH_COL_INDEXES
    data = get_data(args.infiles, indexes)
    
    keys = sorted(data.keys(), key=natural_keys )
    
    for key in keys:
        plot_data = data[key]
        opts= dict(title='Channel {}'.format(key))
        plot = graph.Plot(plot_data, opts)
        plot.show()
    
if __name__ == "__main__":
    main()
