#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Plot a simple histogram of data in a text file.

Input: a text files with data records.

Output: histogram data and image.

Example:
    `./hist.py data_triA.txt data_trigB.txt --range 0:2000 --bins 100 --chan 1`
    - will plot a histograms of data for channel 1, one histogram per input file.

Author: Sergey Ryzhikov (sergey-inform@ya.ru), 2016
License: GPLv2
"""

import sys
import os
import signal
import argparse
from itertools import cycle  # cycle facecolors
from itertools import chain
import logging

import numpy as np

from util import common_start
from util import natural_keys


CHAN_COL_IDX = 1  # if None, no channel filtering at all.
DATA_COL_IDX = 2


def parse_infile(_file, chans=None ):
    """ Parses a file with data records.
        chans:
            a list of channel names;
            if specified, skip channels which are not in list.
        Returns a dict {channel_0: values_0, ... channel_N: values_N}
    """
    lineno = 0
    ret = {} 
    chan = None  # default if no channel filtering
    
    for line in _file:
        lineno += 1
        
        if line[0] == "#":  # ignore comments
            continue
        
        fields = line.split()
        try:
            if CHAN_COL_IDX is None:
                val = float( fields[DATA_COL_IDX] )
            else:
                chan = fields[CHAN_COL_IDX]
                val = float( fields[DATA_COL_IDX] )
                
        except IndexError as e:
            logging.error('%s , line: %d' % (e, lineno) )
            raise
        
        except ValueError as e:
            logging.error('%s , line: %d' % (e, lineno) )
            raise

        if chans and chan not in chans:
            continue  # skip non-listed channels
        
        try:
            ret[chan].append(val)

        except KeyError:  # haven't seen this channel before
            ret[chan] = []
            ret[chan].append(val)
    
    return ret



#TODO: plot( data={trig: values, trig2: values2...

def plot(data, labels, title='', outfile=None, bins=None, histopts={}):
    """
    
    """
    import matplotlib.pyplot as plt

    if len(labels) != len(data):
        raise ValueError("the number of labels doesn't match the number of datasets.")
        
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.grid(True)
    
    colors=cycle(['red','darkgreen','blue','black','brown','grey'])
    
    opts = histopts.copy()
    
    guess_range = True if 'range' not in opts or opts['range'] is None \
            else False
    
    for idx, data in enumerate(data):
        #http://stackoverflow.com/questions/5328556/histogram-matplotlib
        
        label = labels[idx]
        
        if data is None:
            continue
        
        if ('normed' in histopts and histopts['normed']) or \
            ('density' in histopts and histopts['density']):  # normed deprecated in future matplotlib versions
            label += r' (%d)' % len(data)  # add a number of events
        
        
        if not bins:
            # optimize bin sizes
            bins = freedman_bin_width(data)
            print 'nbins', bins
            
        if guess_range:
            opts['range'] = auto_range(data)
            print 'range', opts['range']
        
            
        n, bins_, patches = ax.hist(
            data,
            bins,
            color=next(colors),
            label=label,
            **opts
            )
        
    plt.title(title)
    legend = plt.legend()
    plt.draw()
    
    if outfile:
        plt.savefig(outfile)
    else:
        plt.show()
    

def main():
    global CHAN_COL_IDX
    global DATA_COL_IDX
    
    signal.signal(signal.SIGINT, sigint_handler) # catch Ctrl-C
    
    parser = argparse.ArgumentParser(description=__doc__,
            formatter_class=argparse.RawTextHelpFormatter)
            
    parser.add_argument( 'infiles',
            type=argparse.FileType('r'),
            nargs='*',
            default=[sys.stdin],
            help='the files with data records'
            )
    parser.add_argument( '-c','--chan',
            type=str, 
            metavar = 'LIST',
            help='get data only for specified channel names'
                ' (separated by commas)'
            )
    parser.add_argument( '--normalize',
            action='store_true',
            help="normalize histograms (plot density)"
            )
    parser.add_argument('-r', '--range',
            type=str,
            metavar='A:B',
            help='set histogram range'
            )
    parser.add_argument('-b', '--bins',
            type=int,
            help='set a number of bins'
            )
    parser.add_argument('--chan-col',
            type=int, 
            metavar = 'N',
            default = CHAN_COL_IDX,
            help='an index of column with a channel name'
                ';\n if None, all data belongs to the same channel'
                ' (default: %d)' % CHAN_COL_IDX
            )
    parser.add_argument('--data-col',
            type=int, 
            metavar = 'N',
            help='an index of column with a data'
                ' (default: %d)' % DATA_COL_IDX
            )
    parser.add_argument('-o','--output',
            type=str,
            metavar='PATH',
            help="a path for output, one file per channel."
            )
    parser.add_argument('-q','--quiet',
            action='store_true',
            help="minimize output to stderr"
            )
    
    parser.add_argument('--debug',
            action='store_true',
            help="be verbose"
            )
    parser.add_argument('--root-fit',
            action='store_true',
            help="instead of plotting fit the histograms with root_fit"
            )
    parser.add_argument('--root-gui',
            action='store_true',
            help="show ROOT graphical interface"
            )
    
    args = parser.parse_args()
    print_err(args)

    # --root-fit
    if args.root_fit:
        import root_fit
    
    # --chan-col
    CHAN_COL_IDX = args.chan_col  # can be None
    
    # --data-col
    if args.data_col is not None:
        DATA_COL_IDX = args.data_col
    
    # --chans
    chans = args.chan.split(',') if args.chan is not None else None
    if not args.quiet:
        print_err('chans: %s' %str(chans) )
        
    # --range
    _range = None
    try:
        if args.range:
            _range = map(float, args.range.split(':')[:2])
    except ValueError:
        print_err('wrong range value "%s" (should be two numbers, separated by ":")' % args.range)
        exit(1)
    
    # --bins
    bins = args.bins

    # --output
    outpath = args.output
    makedirs(outpath)

    # infiles
    infiles = args.infiles

    # Parse the data
    data = {}  # {chan1: [values_file1, ... values_fileN], chan2: ... }
    
    for idx, fd in enumerate(infiles):
        parsed = parse_infile(fd, chans=chans) 
        
        for chan, vals in parsed.items():
            if chan not in data:  # met channel the first time
                data[chan] = [None] * len(infiles)  # [None, None, ...]
            data[chan][idx] = np.array(vals)
    
    
    histopts = dict(
            normed = args.normalize,   # replace with density for future matplotlib versions
            #~ density = args.normalize, 
            alpha = 0.75,
            histtype = 'step',
            range=_range,
            )
             
    labels = [f.name for f in infiles]

    # Strip common part from labels and make it a title
    common_part = common_start(*labels)
    common_len = len(common_part)
    shortlabels = [l[common_len:] for l in labels]
    
    for chan in sorted(data.keys(), key=natural_keys ):  # TODO: numeric sort
        
        title = "chan %s" % str(chan)
        if common_part:
            title += ' (%s)' % common_part
        
        outfile = outpath + str(chan) + '.png' if args.output else None
        
        if args.root_fit:
            # try to fit with root_fit
            root_fit.root_fit(data[chan], shortlabels,
                title=title,
                bins=bins,
                outfile=outfile,
                histopts=histopts,
                quiet=args.quiet,
                gui=args.root_gui,
                )
                
        else:
            # plot the data
            plot( data[chan], shortlabels,
                title=title,
                bins=bins,
                outfile=outfile,
                histopts=histopts,
                )
    
# UTILS

def print_err(format_str, *args, **kvargs):
    sys.stderr.write(str(format_str) + '\n', *args, **kvargs)


def sigint_handler(signal, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)
    
    
def makedirs(path):
    """ Create directories for `path` (like 'mkdir -p'). """
    if not path:
        return
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)


def auto_range(data):
    """ Return the optimal range for a histogram.
    """
    data = np.asarray(data)
    _min = data.min()
    percentile = np.percentile(data, 99)
    _range = [_min, percentile]
    
    if _min > 0 and _min/percentile < 0.3:
        _range[0] = 0
    
    return _range
    

def freedman_bin_width(data):
    """Return the optimal number of bins using the Freedman-Diaconis rule.

    The Freedman-Diaconis rule is a normal reference rule like Scott's
    rule, but uses rank-based statistics for results which are more robust
    to deviations from a normal distribution.
    
    Return a recommended number of bins for a `data` set.
    
    http://astropy.readthedocs.io/en/latest/_modules/astropy/stats/histogram.html#freedman_bin_width
    """
    
    data = np.asarray(data)
    if data.ndim != 1:
        raise ValueError("data should be one-dimensional")

    n = data.size
    if n < 4:
        raise ValueError("data should have more than three entries")

    v25, v75 = np.percentile(data, [25, 75])
    dx = 2 * (v75 - v25) / (n ** (1 / 3))
    
    dmin, dmax = data.min(), data.max()
    nbins = max(1, np.ceil((dmax - dmin) / dx))
    
    return nbins
    

if __name__ == "__main__":
    main()
