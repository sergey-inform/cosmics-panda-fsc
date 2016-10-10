#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Find the most probable values for given dataset
using Kernel Density Estimation technique:
http://www.mvstat.net/tduong/research/seminars/seminar-2001-05/

If several maximums found, print them all.
"""

import sys
import os
import numpy as np
from matplotlib import pyplot as plt
from scipy.stats import gaussian_kde
from scipy.signal import argrelmax
from scipy.optimize import fmin
from util import natural_keys

VALUE_COLUMN = 2  # a column number with the value 
CHANNEL_COLUMN = 1  # a column number for channel, None if not the case

gui = False
gui = True

threshold = 200

def common_start(*strings):
    """ Returns the longest common substring
        from the beginning of the `strings`
    """
    def _iter():
        for z in zip(*strings):
            if z.count(z[0]) == len(z):  # check all elements in `z` are the same
                yield z[0]
            else:
                return

    return ''.join(_iter())


def parse_values(fileobjects, channels=set()):
    """ Parse datafile.
    Return a dict of ditcts of lists: {chanel: { filename : [values]} }.
    """
    data = {}

    for fileobj in fileobjects:
        filename = fileobj.name

        filedata = {}
        for line in fileobj: 
            line = '\t'.join(line.split())  # join consecutive spaces
            sline = line.split('\t')
            value = float(sline[VALUE_COLUMN])
            chan = sline[CHANNEL_COLUMN] if CHANNEL_COLUMN is not None else None
            
            try:
                filedata[chan].append(value)
            except KeyError:
                filedata[chan] = []
                filedata[chan].append(value)
            
        for chan, values in filedata.items():
            if channels and chan not in channels:
                pass

            if chan not in data:
                data[chan] = {}
            data[chan][filename] = np.array(values)
    
    return data

def fit_cosmics(title, cdata):
    """

    """
    
    if gui:
        fig, ax = plt.subplots()

    common_name = os.path.commonprefix(cdata.keys())
    dir_len  = len(os.path.dirname(common_name))
    common_len = max(dir_len, common_name.find('_',dir_len))
    common_name = common_name[:common_len+1]

    hist_maxscale = 0

    for name, data in sorted(cdata.items()):
        label = name[len(common_name):]
        label = os.path.splitext(label)[0]
        
        data = data[data > threshold]

        median = np.median(data)
        minpercent = np.percentile(data, 25)
        maxpercent = np.percentile(data, 75)
        hist_minrange = min( median / 4.0, minpercent)
        hist_maxrange = max( median * 2.0, maxpercent)

        hist_range = (hist_minrange, hist_maxrange )
        hist_bins = 50   # binsize is 1% of the median 
        
        data_hist = data[(data> hist_range[0]) &(data < hist_range[1])]

        vals, bins, patches = plt.hist(
            data_hist,
            bins = hist_bins,
            range = hist_range,
            histtype = 'step',
            normed = True,
            label = label,  # strip common part
        )

        hist_maxscale = max( hist_maxscale, max(vals))
            
        color = patches[0].get_edgecolor()

        #get kde parameter  
        
        kde = gaussian_kde(data_hist)
        kde_vals = kde(bins)
        maxima_idx = argrelmax(kde_vals)[0]
        maxima_x = [bins[i] for i in maxima_idx]
        
        def minfunc(x, *args):
            return -kde(x)[0]

        # impove_results
        maxima_x_optim = []
        
        for x0 in maxima_x:
            maxima_x_optim.extend(fmin(minfunc,x0,disp=False))

        if len(maxima_x_optim) == 1:
            result =  maxima_x_optim[0]
     
        elif len(maxima_x_optim) > 1:
            # choose the right one maximum
            pairs = [(kde(m), m) for m in maxima_x_optim]

            top_two = sorted(pairs, reverse=True)[0:2]  # last two
           
            # if difference is not too big, choose the right one:
            if top_two[0][0]/2 > top_two[1][0]:
                result = top_two[0][1]
            else:
                result = max(top_two[0][1], top_two[1][1])  #FIXME: too tired to write normal code              
        else:
            result = None

        if result:
            result = "{:.2f}".format(result)

        print '{} {} {} {}'.format(title, name, label, result)

        plt.plot(bins, kde_vals, '-', color= color)

    if gui:
        fig.canvas.set_window_title(common_name)
        plt.title(title)
        plt.legend()
        plt.grid()
        ax.set_ylim(0,hist_maxscale)
        plt.show()

def nsort(dic):
    for key in sorted(dic, key=natural_keys):
        yield (key, dic[key])

def main():
    filenames = sys.argv[1:]
    infiles = [open(fn, 'ro') for fn in filenames]
    data = parse_values(infiles)

    for chan, cdata in nsort(data):
        fit_cosmics(chan, cdata)

if __name__ == "__main__":
    main()
