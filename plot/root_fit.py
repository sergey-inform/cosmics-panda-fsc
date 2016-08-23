#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fit data with a custom function.

Author: Sergey Ryzhikov (sergey-inform@ya.ru), 2016
License: GPLv2
"""
import sys
import os
from ROOT import TH1F, TF1, TCanvas, TLegend, gROOT, gStyle, TGraph
from rootpy.interactive import wait
from itertools import cycle 
import numpy as np
import copy

from util import movingaverage

from array import array

COLORS=[2,8,4,6,7,9]
DEFAULT_HIST_RANGE = (0, 2500)
DEFAULT_BINS_NUMBER = 50

colors = cycle(COLORS)

import rootpy.compiled as C
pwd = os.path.dirname(__file__)
C.register_file( pwd + "/mylangaus.cxx", ["langaufun"])

    
def root_fit(data, labels, title=None, outfile=None, bins=None, histopts={}, gui=True, quiet=False):
    
    single = False  # Only one histogram given
    
    if sum(x is not None for x in data) == 1:  # a number of not empty sets
        single = True
        
    if len(labels) != len(data):
        raise ValueError("the number of labels doesn't match the number of datasets.")
    
    if gui:
        gROOT.Reset()
        c1 = TCanvas( 'c1', str(title) , 200, 10, 700, 500 )
        c1.SetGrid()
        legend = TLegend(0.5, 0.8, 0.9,0.9)
        
        if not single:
            gStyle.SetOptStat(0)  # Hide statistics

    if hasattr(histopts, 'range'):
        range_ = histopts.range
    else:
        range_ = DEFAULT_HIST_RANGE
    
    if not bins:
        bins = DEFAULT_BINS_NUMBER
    
    for idx, data in enumerate(data):
    
        if data is None:
            continue
        
        label = labels[idx]
        
        # Histogram data
        hist = TH1F("hist" + str(idx) ,"myhist" + str(idx), bins, range_[0], range_[1])
        [hist.Fill(_) for _ in data]
        
        # Normalize the histogram
        integral = hist.Integral()
        if integral > 0:
            hist.Scale(1/integral) 
        
        ## Fit the histogram
        fitfunc, fitres = langaus_fit(hist)
        
       
    
        print 'RESULT {} {} MPL={:.2f} chi2={:.2f} ndf={}'.format(title, label, fitres.Parameter(1), fitres.Chi2(), fitres.Ndf() ) # TODO: error
        if not quiet:
            fitres.Print()
            print "----"
        
        
        #~ print 'prob=%.2f' % fitres.Prob()

        ## Plot the histogram (and the fit)
        if gui:
            color = next(colors)
            hist.SetLineColor(color);
            fitfunc.SetLineColor(color);
            
            if idx == 0:
                hist.Draw('HIST')
            else:
                hist.Draw('HIST SAMES')

            fitfunc.Draw('SAME')
            legend.AddEntry(hist, label, "f")   

    #TODO: Fit Precise (with fixed parameters)

    if gui:
        if not single:
            legend.Draw()
        
        c1.Update()
        wait(True)
    
    if outfile:
        pass
        #~ c1.SaveAs?
        #~ c1.Print("c1.pdf", "pdf");


def langaus_fit(hist, fix_parameters=[]):
    """ Fit a ROOT TH1 with langauss + exponential noize. 
    
        Return the fit function and a fit result object.
    """
    
    xaxis = hist.GetXaxis()
    hist_Xmin, hist_Xmax = xaxis.GetXmin(), xaxis.GetXmax()

    langaufun = TF1( 'langaufun', C.langaufun, hist_Xmin, hist_Xmax )
    
    # Smooth the histogram.
    smooth_xy = maw_hist(hist)
    
    initial_langaus_params = guess_langaus_params(*smooth_xy)
    initial_noize_params = guess_noize_params(*smooth_xy)
    threshold = guess_threshold_bin(*smooth_xy)
    
    
    
    
    # Check a number of minima and maxima in the histogram
    histvals = [ hist.GetBinContent(n) for n in range(1,hist.GetSize()-1) ]
    max_loc, min_loc = window_extrema(histvals, nmax=2, nmins=1) # looking for one minimum and one or two maximums
    
    if max_loc:
        max_idx = max_loc[-1]  # the last element
        max_x, max_y = hist.GetBinCenter(max_idx), hist.GetBinContent(max_idx)
        
        initial_langaus_params[1] = max_x
        
        # Fix maximum (without noize)
        hist.SetMaximum(max_y * 1.5)
    
    #~ print 'initial_params', initial_langaus_params, initial_noize_params
     
    fitXmax = hist_Xmax
    # Set fitXmin as a middle between minimum and threshold    
    
    if min_loc:
        min_val = hist.GetBinCenter(min_loc[0])
    else:
        min_val = threshold
    
    if min_val >= threshold:
        fitXmin = (min_val + threshold) / 2
        #~ fitXmin = max_x/2
    else:
        fitXmin = threshold
    
    fitXmin = threshold
    
    #~ print '\nFIT RANGE',  fitXmin, fitXmax
    
    fitfunc = TF1( 'fitfunc', 'langaufun(&x,[0],[1],[2],[3]) + 0.001*[4]*exp(-0.001*[5]*x)', fitXmin, fitXmax )
    fitfunc.SetParNames ('Langaus Width Landau','Langaus MPL','Langaus Area','Langaus Width Gauss','expA','expB')
    fitfunc.SetParameters(*(initial_langaus_params + initial_noize_params))

    #TODO: fixed parameters

    # SQMRN = S(ave fitres), Quiet, More (improve results), Range (of the function), No (drawing)
    fitres = hist.Fit(fitfunc, "SQMRN+" )
    return fitfunc, fitres


# DELME
    #~ print 'nbins', hist.GetSize()  # Nbins + Underflow + Overflow
    #~ print 'integral', hist.Integral(0,20)
    #~ print 'max', hist.GetMaximumBin()
    #~ print 'values', [round(hist.GetBinContent(n)*100, 2) for n in range(1, hist.GetSize()-1)]

def maw_hist(hist, window = 3):
    nbins = hist.GetSize() # Underflow + Nbins + Overflow
    values = [ hist.GetBinContent(n) for n in range(1,nbins-1) ]
    avg_values = movingaverage(values, 3)
    x, y = [], []
    
    for idx, val in enumerate(avg_values):
        x.append(hist.GetBinCenter(idx+1))
        y.append(val)
        
    return x,y
    

def extrema(arr):
    """ Find all entries in the 1d array smaller and higher than their neighbors.
    """
    gradients=np.diff(arr)
    maxima_num=0
    minima_num=0
    max_loc=[]
    min_loc=[]
    
    count=0
    
    for i in gradients[:-1]:
        count+=1

        if ((cmp(i,0)>0) & (cmp(gradients[count],0)<0) & (i != gradients[count])):
            maxima_num+=1
            max_loc.append(count)     

        if ((cmp(i,0)<0) & (cmp(gradients[count],0)>0) & (i != gradients[count])):
            minima_num+=1
            min_loc.append(count)

    return maxima_num, minima_num, max_loc, min_loc


def window_extrema(yvals, nmins=1, nmax=2):
    """ Find so many local extrema (maxima and minima).
    """
    nvals = len(yvals)
    maxwindow = 2*int(nvals**0.5) 
    maxloc, minloc = [], []
    
    for window in range(1, maxwindow+1):
        smooth_vals = movingaverage(yvals, window)
        maxn, minn, maxloc, minloc = extrema(np.array(smooth_vals))
        
        print window, maxn, minn, maxloc, minloc
        
        if nmins >= minn and nmax >= maxn:
            break
        
    return maxloc, minloc
    
    
    
    
def guess_threshold_bin(xvals, yvals):
    """ Guess histogram threshold (the left edge).
        Return a center of the threshold bin.
    """
    if len(xvals) != len(yvals):
        raise ValueError('x and y lenghts are not the same.')
    
    for idx, x in enumerate(xvals):
        y = yvals[idx]
        if idx and y < prev_y:
            prev_x = xvals[idx-1]
            xstep = x - prev_x
            return prev_x - xstep/2
        prev_y = y


def guess_noize_params(xvals, yvals):
    
    #FIXME
    return [50.0,  # expA
            2.0,  # expB
        ]


def accumulate(vals):
    total = 0
    for x in vals:
        total += x
        yield total

def guess_langaus_params(xvals, yvals):
    
    #FIXME
    
    # MPL
    halfsum = sum(yvals)/2
    for idx, val in enumerate(accumulate(yvals)):
        mpl = xvals[idx]
        if val > halfsum:
            break
    
    
    return [100.0,  # Width Landau
            mpl,  # MPL
            10.0,  # Area
            30.0,  # Width Gauss (set smaller than WidthLandau)
        ]

def root_refit_avg():
    """ Fit again, but average and fix common parameters. """
    pass

if __name__ == "__main__":
    main()
