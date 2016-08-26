#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fit data with a custom function.

Author: Sergey Ryzhikov (sergey-inform@ya.ru), 2016
License: GPLv2
"""
import sys
import os
from ROOT import TH1F, TF1, TCanvas, TLegend, gROOT, gStyle, TGraph, TKDE
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


#TODO: use KDE for smoothing histograms https://root.cern.ch/root/html/tutorials/math/exampleTKDE.C.html



#TODO: rename to rootfit_langaus
def root_fit(datasets, labels, title=None, outfile=None, bins=None, histopts={}, gui=True, quiet=False):
    """
    Main fit function.
    Fit data, draw a plot with histograms and fit-functions.
    Print fit results.
    """
    if sum(x is not None for x in datasets) == 1:  # a number of not empty sets
        single = True  # Only one histogram given
    else:
        single = False  
        
    if len(labels) != len(datasets):
        raise ValueError("the number of labels doesn't match the number of datasets.")
    
    if gui:
        gROOT.Reset()
        c1 = TCanvas( 'c1', str(title) , 200, 10, 700, 500 )
        c1.SetGrid()
        legend = TLegend(0.5, 0.8, 0.9,0.9)
        
        if not single:
            gStyle.SetOptStat(0)  # Hide statistics
    
    ## Set Range
    if 'range' in histopts:
        range_ = histopts['range']
    else:
        range_ = DEFAULT_HIST_RANGE
    
    ## Bin count
    if not bins:
        bins = DEFAULT_BINS_NUMBER
    
    for idx, data in enumerate(datasets):
    
        if data is None:
            continue
            
        median = np.median(data)
        if median * 3 < range_[1]:
            range_ = range_[0], median * 2
        
        label = labels[idx]

        ## Histogram the data
        hist = TH1F("hist" + str(idx) ,"myhist" + str(idx), bins, range_[0], range_[1])
        [hist.Fill(_) for _ in data]
        
        ## Normalize the histogram
        integral = hist.Integral()
        if integral > 0:
            hist.Scale(1/integral) 

        ## Plot the histogram
        if gui:
            hist_color = next(colors)
            hist.SetLineColor(hist_color);
            
            if idx == 0:
                hist.Draw('HIST')
            else:
                hist.Draw('HIST SAMES')

            legend.AddEntry(hist, label, "f")   

        ## Fit the histogram
        maxloc, minloc, shist= hist_extrema(hist, nminima=1, nmaxima=2)
        fitrange, initial_params = guess_langaus_fit_params(hist, maxloc, minloc)
        
        print "FITRANGE {} INITIAL {}".format(fitrange, initial_params)
        fitfunc, fitres = langaus_fit(hist, fitrange, initial_params)
        
        #~ print 'RESULT {} {} MPL={:.2f} chi2={:.2f} ndf={}'.format(title, label, fitres.Parameter(1), fitres.Chi2(), fitres.Ndf() ) # TODO: error
        
        if not quiet:
            fitres.Print()
            print "----"
        
        ## Plot the fit
        if gui:
            fitfunc.SetLineColor(hist_color);
            fitfunc.Draw('SAME')
        shist.Draw('SAME')
        
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


def hist_extrema(hist, nminima, nmaxima, smooth_max=100, smooth_step=1):
    """ Smooth the copy of the histogram and
        find so many local extrema (maxima and minima).
        
        hist: ROOT TH1 object
        nminima: expected number of minima
        nmaxima: expected number of maxima
    """
    shist = hist.Clone()
    
    for n in range(0, smooth_max +1, smooth_step):
        if n:
            shist.Smooth()
        
        x, y = hist_to_xy(shist)

        maxn, minn, maxloc, minloc = extrema(np.array(y))
        #TODO: if not quiet or if verbose:
        print 'SMOOTH', n, maxn, minn, maxloc, minloc
        
        if nminima >= minn and nmaxima >= maxn:
            break
        
    return maxloc, minloc, shist
    
    
    
def langaus_fit(hist, fitrange, parameters, fix_parameters=[]):
    """ Fit a ROOT TH1 with langauss + exponential noize. 
    
        Return the fit function and a fit result object.
    """
    fitXmin = fitrange[0]
    fitXmax = fitrange[1]

    langaufun = TF1( 'langaufun', C.langaufun, fitXmin, fitXmax )
    
    # Smooth the histogram.
    #~ x, y = hist_to_xy(hist)
    #~ initial_langaus_params = guess_langaus_params()
    #~ initial_noize_params = guess_noize_params()
    #~ threshold = guess_threshold_bin(x, y)
    
    
    # Check a number of minima and maxima in the histogram
    #~ histvals = [ hist.GetBinContent(n) for n in range(1,hist.GetSize()-1) ]
    #~ max_loc, min_loc = window_extrema(histvals, nmax=2, nmins=1) # looking for one minimum and one or two maximums
    #~ 
    #~ if max_loc:
        #~ max_idx = max_loc[-1]  # the last element
        #~ max_x, max_y = hist.GetBinCenter(max_idx), hist.GetBinContent(max_idx)
        #~ 
        #~ initial_langaus_params[1] = max_x
        #~ 
        #~ # Fix maximum (without noize)
        #~ hist.SetMaximum(max_y * 1.5)
    #~ 
    #~ print 'initial_params', initial_langaus_params, initial_noize_params
     #~ 
    #~ fitXmax = hist_Xmax
    #~ # Set fitXmin as a middle between minimum and threshold    
    #~ 
    #~ if min_loc:
        #~ min_val = hist.GetBinCenter(min_loc[0])
    #~ else:
        #~ min_val = threshold
    #~ 
    #~ if min_val >= threshold:
        #~ fitXmin = (min_val + threshold) / 2
        #~ fitXmin = max_x/2
    #~ else:
        #~ fitXmin = threshold
    #~ 
    #~ fitXmin = threshold
    #~ 
    #~ print '\nFIT RANGE',  fitXmin, fitXmax
    
    
    
    fitfunc = TF1( 'fitfunc', 'langaufun(&x,[0],[1],[2],[3]) + 0.001*[4]*exp(-0.001*[5]*x)', fitXmin, fitXmax )
    fitfunc.SetParNames ('Langaus Width Landau','Langaus MPL','Langaus Area','Langaus Width Gauss','expA','expB')
    fitfunc.SetParameters(*parameters)

    #TODO: fixed parameters

    # SQMRN = S(ave fitres), Quiet, More (improve results), Range (of the function), No (drawing)
    fitres = hist.Fit(fitfunc, "SQMRN+" )
    return fitfunc, fitres
    
    
# DELME
    #~ print 'nbins', hist.GetSize()  # Nbins + Underflow + Overflow
    #~ print 'integral', hist.Integral(0,20)
    #~ print 'max', hist.GetMaximumBin()
    #~ print 'values', [round(hist.GetBinContent(n)*100, 2) for n in range(1, hist.GetSize()-1)]
    
    
    
def hist_to_xy(hist):
    """ Get x,y values from ROOT histogram object.
    """
    nbins = hist.GetSize() # Underflow + Nbins + Overflow
    values = [ hist.GetBinContent(n) for n in range(1,nbins-1) ]
    x, y = [], []

    for idx, val in enumerate(values):
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


def guess_langaus_fit_params(hist, maxloc, minloc):
    
    x,y = hist_to_xy(hist)
    threshold = guess_threshold_bin(x, y)
    
    if minloc:
        firstmin = hist.GetBinCenter(minloc[0])
    else:
        firstmin = threshold
    
    if maxloc:
        firstmax = hist.GetBinCenter(maxloc[0])
    else:
        firstmax = 0
    
    xaxis = hist.GetXaxis()
    histXmin, histXmax = xaxis.GetXmin(), xaxis.GetXmax()
    
    fitstart = (threshold + firstmin*2)/3
    fitrange = (fitstart, histXmax)
    
        # MPL
    #~ halfsum = sum(yvals)/2
    #~ for idx, val in enumerate(accumulate(yvals)):
        #~ mpl = xvals[idx]
        #~ if val > halfsum:
            #~ break
    
    #MPL
     
    
    params = [
        400.0,  # Width Landau
        firstmax,  # MPL
        20.0,  # Area
        100.0,  # Width Gauss (set smaller than WidthLandau)
        50.0,  # expA
        0.4,  # expB
        ]
    
    return fitrange, params

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


#~ 
#~ def accumulate(vals):
    #~ total = 0
    #~ for x in vals:
        #~ total += x
        #~ yield total


if __name__ == "__main__":
    main()
