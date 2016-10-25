#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fit cosmics data with ROOT tools.

Input: a text files with data records.

Author: Sergey Ryzhikov (sergey-inform@ya.ru), 2016
License: GPLv2
"""

import sys
import os
import signal
import argparse
from itertools import cycle  # cycle facecolors
from itertools import chain
from collections import defaultdict

import logging
import numpy as np
    
from util import common_start
from util import natural_keys
from util import makedirs

try:
    import ROOT
    ROOT.PyConfig.IgnoreCommandLineOptions = True  # do not hijack
                                                    # cmdline options
    from rootpy.interactive import wait
    pass

except ImportError as e:
    print e
    sys.stderr.write("To run this script pyROOT and rootpy"
            " has to be properly installed.\n")
    exit(1)

import rootpy.compiled as C
pwd = os.path.dirname(__file__)
C.register_file( pwd + "/mylangaus.cxx", ["langaufun"])

CHAN_COL = 1
DATA_COL = 2

COLORS=[2,8,4,6,7,9]
colors = cycle(COLORS)


def parse_infile(infile, chans=None, chan_col = CHAN_COL, data_col = DATA_COL ):
    """ Parses a file with data records.
        chans:
            a list of channel names;
            if specified, skip channels which are not in list.
        Returns a dict {channel_0: values_0, ... channel_N: values_N}
    """
    ret = defaultdict(list) 
    
    for lineno, line in enumerate(infile):
        
        if line[0] == "#":  # ignore comments
            continue
        
        fields = line.split()
        try:
                chan = fields[chan_col]
                val = float( fields[data_col] )
                
        except IndexError as e:
            print_err('{} , line: {}', (e, lineno) )
            raise
        
        except ValueError as e:
            print_err('{} , line: {}', (e, lineno) )
            raise

        if chans and chan not in chans:
            continue  # skip non-listed channels
        
        ret[chan].append(val)

    return ret


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__,
            formatter_class=argparse.RawTextHelpFormatter)
            
    parser.add_argument( 'infiles',
            type=argparse.FileType('r'),
            nargs='+',
            default=[sys.stdin],
            help='the files with data records'
            )

    parser.add_argument( 'params',
            type = parse_fit_params,
            metavar = 'P1,P2,..P6', 
            help = 'initial fit parameters for langaus()',
            )

    parser.add_argument( '-c','--chan',
            type = parse_chans, 
            metavar = 'LIST',
            help='get data only for specified channel names'
                ' (separated by commas)'
            )

    parser.add_argument('-r', '--range',
            type = parse_range,
            metavar='A:B',
            help='set histogram range'
            )

    parser.add_argument('-b', '--bins',
            type = int,
            default = 50,
            help = 'set a number of bins'
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

    args = parser.parse_args()

    if not args.quiet:
        print_err(args)

    return args


def parse_chans(value):
    return value.split(',')


def parse_fit_params(value):
    sparams = value.split(',')
    if len(sparams) != 6:
        raise argparse.ArgumentTypeError(
                "need exactly 6 parameters for langaus function."
                )
    params = []
    fixed = []

    for idx, p in enumerate(sparams):
        if p[0] == '_':  # fixed parameter
            param = float(p[1:])
            fixed.append(idx)
        else:
            param = float(p)
        params.append(param)

    return params, fixed


def parse_range(value):
    try:
        _range = map(float, value.split(':')[:2])

    except ValueError:
        raise argparse.ArgumentTypeError('required one or two numbers separated by ":"')

    return _range


def main():
    signal.signal(signal.SIGINT, sigint_handler) # catch Ctrl-C
    
    args = parse_args()

    labels = [f.name for f in args.infiles]
    common_label = common_start(*labels)
    shortlabels = [l[len(common_label):] for l in labels]
        
    if args.output:
        makedirs(args.output)

    if not args.quiet:
        print_err('channels: {}', str(args.chan) )
        print_err('outpath: {}', args.output)

    # 
    data = defaultdict(dict)

    for idx, fd in enumerate(args.infiles):
        parsed = parse_infile(fd, chans=args.chan) 
        
        for chan, vals in parsed.items():
            key = shortlabels[idx]
            data[chan][key] = np.array(vals)
    
    if not data and args.chan:
        print_err('No data for that channels')
        exit(0)

    #
    
    for chan in sorted(data, key=natural_keys):
       
        cdata = data[chan]
        if not cdata:
            continue

        title = "Chan {} ({})".format(chan, common_label)
        outfile = "./{}/{}.png".format(args.output, chan) \
                if args.output else None
        
        hists = {}
    
        _range=args.range
        
        fit_params, fit_fixed = args.params

        if not _range:
            _range = (0, fit_params[1] * 2)

        if len(_range) == 1:
            _range = (_range[0], fit_params[1] * 2)

        for key, vals in cdata.items():
            hists[key] = root_hist(vals, args.bins, _range)

        #fit_start = initial_params[1]/2  # MPL/2
        fit_start = _range[0] + 100
        fitrange = (fit_start, _range[1])

        fitfuncs = {}
        fitresults = {}

        for k in sorted(hists):
            fitfunc, fitres = langaus_fit(hists[k], 
                                        fitrange,
                                        fit_params,
                                        fixed=fit_fixed)

            fitfuncs[k] = fitfunc
            fitresults[k] = fitres
            strparams = '\t'.join( ['{:.2f}'.format(p) for p in fitres.Parameters()] )
            print '{} chan {}\t {}\tMPL {:.2f} ' \
                    '±{:.2f}\tchi2 {:.2f}\tndf {:.2f}\tparams {}' \
                    ''.format(
                            common_label,  # run
                            chan,
                            k,  # trig
                            fitres.Parameter(1),
                            fitres.ParError(1),
                            fitres.Chi2(),
                            fitres.Ndf(),
                            strparams
                            )

        root_plot(hists, fitfuncs, outfile=outfile, title=title)
            

def root_plot(hists, fitfuncs={}, outfile=None, title=''):
    if not hists:
        print_err('No hists to plot')
        return

    single = len(hists) is 1

    ROOT.gROOT.Reset()
    c1 = ROOT.TCanvas('c1', str(title) , 200, 10, 700, 500 )
    c1.SetGrid()
    legend = ROOT.TLegend(0.5, 0.8, 0.9,0.9)
    
    if not single:
        ROOT.gStyle.SetOptStat(0)  # Hide statistics
    
    for idx, k in enumerate(sorted(hists)):
        hist = hists[k]

        hist_color = next(colors)
        hist.SetLineColor(hist_color);
        
        if idx == 0:
            hist.Draw('HIST')
        else:
            hist.Draw('HIST SAMES')

        legend.AddEntry(hist, str(k), "f")   
        
        if k in fitfuncs:
            fitfunc = fitfuncs[k]

            fitfunc.SetLineColor(hist_color);
            fitfunc.Draw('same')

    
    if not single:
        legend.Draw()
        
    c1.Update()
    wait(True)

def hist_idx(start=0):
    idx = start
    while True:
        idx += 1
        yield idx

_idx = hist_idx()


def root_hist(vals, nbins=None, range_=None):
    """ Create root histogram.
    """
    if vals is None:
        return

    if not nbins:
        nbins = freedman_bin_width(vals)

    if not range_:
        range_ = auto_range(vals)
    
    idx = next(_idx)
    hist = ROOT.TH1F("hist"+str(idx), "myhist"+str(idx), nbins, range_[0], range_[1])
    [hist.Fill(_) for _ in vals]
    
    ## Normalize the histogram
    integral = hist.Integral()
    if integral > 0:
        hist.Scale(1/integral) 
    
    return hist


# misc

def print_err(format_str, *args, **kvargs):
    sys.stderr.write(str(format_str).format( *args, **kvargs))
    sys.stderr.write('\n')


def sigint_handler(signal, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)
    
    
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
    

def langaus_fit(hist, fitrange, parameters, fixed=[]):
    """ Fit a ROOT TH1 with langauss + exponential noize. 
    
        Return the fit function and a fit result object.
    """
    fitXmin = fitrange[0]
    fitXmax = fitrange[1]

    langaufun = ROOT.TF1( 'langaufun', C.langaufun, fitXmin, fitXmax )
    
    fitfunc = ROOT.TF1( 'fitfunc', 'langaufun(&x,[0],[1],[2],[3]) + 0.001*[4]*exp(-0.0001*[5]*x)', fitXmin, fitXmax )
    fitfunc.SetParNames ('Langaus Width Landau','Langaus MPL','Langaus Area','Langaus Width Gauss','expA','expB')
    fitfunc.SetParameters(*parameters)
    
    for i in fixed:
        fitfunc.FixParameter(i, parameters[i])

    # SQMRN = S(ave fitres), Quiet, More (improve results), Range (of the function), No (drawing)
    fitres = hist.Fit(fitfunc, "SQMRN+" )
    return fitfunc, fitres

if __name__ == "__main__":
    main()


