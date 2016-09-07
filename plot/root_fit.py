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
from ROOT.Math import WrappedTF1
from ROOT.Math import BrentRootFinder

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
            #~ if median * 3 < range_[1]:
                #~ range_ = range_[0], median * 2
        
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
        xaxis = hist.GetXaxis()
        
        maxima, minima = maxmin_smooth(data, range_, nminima=1, nmaxima=2)
        
        fitrange = guess_cosmics_fitrange(range_, maxima, minima)
        
        #TODO: FAST AND WRONG
        if len(maxima) < 2:
            fitrange = guess_threshold_bin(*hist_to_xy(hist)), fitrange[1]
            
        initial_params = guess_cosmics_fitparams(hist, maxima, minima)
        
        print "MINIMA {} MAXIMA {}".format(minima, maxima)
        print "FITRANGE {} INITIAL {}".format(fitrange, initial_params)
       
        fitfunc, fitres = langaus_fit(hist, fitrange, initial_params)
        
        print 'RESULT {} {} MPL={:.2f} +- {:.2f} chi2/ndf={:.2f}'.format(title, label, fitres.Parameter(1), fitres.ParError(1), fitres.Chi2()/fitres.Ndf() ) # TODO: error
        
        if not quiet:
            fitres.Print()
        print "----"
        
        ## Plot the fit
        if gui:
            fitfunc.SetLineColor(hist_color);
            fitfunc.Draw('SAME')
        
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

def hist_extrema_smooth(hist, nminima, nmaxima, smooth_max=100, smooth_step=1):
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
    
    
#peakdetect soluthons:
# https://gist.github.com/sixtenbe/1178136
# https://blog.ytotech.com/2015/11/01/findpeaks-in-python/
# https://gist.github.com/endolith/250860 (matlab script converted)
    
def maxmin_smooth(data, range_, nminima, nmaxima):
    """ Smooth the data with Kernel Density Estimation and
        find so many local extrema (maxima and minima).
    """
    # Increase factor value (smooth harder)
    # until get desired number of max and min points.
    
    factors = np.linspace(0.05,0.09,40,endpoint=True)
    
    for factor in factors:
        
        maxima, minima = maxmin_kde(data, range_, factor)
        
        print 'FACTOR', factor, maxima, minima
        
        if len(maxima) <= nmaxima and len(minima) <= nminima:
            break
    
    return maxima, minima
    
def maxmin_kde(data, range_, factor=0.05):
    """ find minima and maxima of probability density
    """
    from scipy.stats import gaussian_kde
    from scipy.signal import argrelmax, argrelmin
    
    n = len(data)
    
    # Get probability density (a smooth function)
    kernel = gaussian_kde(data, bw_method=factor)
    
    r_left = range_[0]
    r_right = range_[1]
    r_step = (r_right-r_left)/1000
   
    positions = np.arange(r_left,r_right,r_step)
    kde_values = kernel(positions)

    maxima = argrelmax(kde_values)[0].tolist()
    minima = argrelmin(kde_values)[0].tolist()
    
    vmaxima = [positions[_] for _ in maxima]
    vminima = [positions[_] for _ in minima]
    
    
    
    #~ # plot the thing for debug
    #~ import matplotlib.pyplot as plt
    #~ plt.plot(positions, kde_values)
    #~ for m in vmaxima:
        #~ plt.axvline(m, color='red')
    #~ for m in vminima:
        #~ plt.axvline(m)
    #~ plt.show()
    
    return vmaxima, vminima
    
def langaus_fit(hist, fitrange, parameters, fix_parameters=[]):
    """ Fit a ROOT TH1 with langauss + exponential noize. 
    
        Return the fit function and a fit result object.
    """
    fitXmin = fitrange[0]
    fitXmax = fitrange[1]

    langaufun = TF1( 'langaufun', C.langaufun, fitXmin, fitXmax )
    
    fitfunc = TF1( 'fitfunc', 'langaufun(&x,[0],[1],[2],[3]) + 0.001*[4]*exp(-0.0001*[5]*x)', fitXmin, fitXmax )
    fitfunc.SetParNames ('Langaus Width Landau','Langaus MPL','Langaus Area','Langaus Width Gauss','expA','expB')
    fitfunc.SetParameters(*parameters)
    
    #TODO: fixed parameters

    # SQMRN = S(ave fitres), Quiet, More (improve results), Range (of the function), No (drawing)
    fitres = hist.Fit(fitfunc, "SQMRN+" )
    return fitfunc, fitres
    
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


def guess_cosmics_fitrange(range_, maxima, minima):
    """ Choose a range for fittig.
    """
    fit_left = range_[0]
    fit_right = range_[1]
    
    nmax = len(maxima)
    nmin = len(minima)
    
    if nmax == 2 and nmin == 1: # normal case
        # start fit between minima and first maxima
        fit_left = (minima[0] + maxima[0]) /2
        fit_right = maxima[1] * 2
        
    elif nmax == 1 and nmin in (0,1): # no noize peak
        # fit from a half of maximum
        fitleft =  maxima[0]/2
        fit_right = maxima[0] * 2
    
    return fit_left, fit_right

def guess_cosmics_fitparams(hist, maxima, minima):
    from collections import OrderedDict
   
    # Defaults
    params = OrderedDict([
        ('wlandau', 50.0),  # Width Landau
        ('mpl', 1000),  # MPL
        ('area', 20),  # Area
        ('wgauss', 50.0),  # Width Gauss (set smaller than WidthLandau)
        ('expa', 30),  #expA
        ('expb', 10),  # expB
        ])
        
        
    # MPL
    nmax = len(maxima)
    if nmax == 1:
        params['mpl'] = maxima[0]
    elif nmax == 2:
        params['mpl'] = maxima[1]
    
    
    params['wlandau'] = params['mpl']/10
    params['wgauss'] = params['wlandau']/2
    
    return params.values()

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


if __name__ == "__main__":
    main()
