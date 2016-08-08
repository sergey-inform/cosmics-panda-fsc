#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fit data with a custom function.

Author: Sergey Ryzhikov (sergey-inform@ya.ru), 2016
License: GPLv2
"""
import sys
import os
from ROOT import TH1F, TF1, TCanvas, TLegend, gROOT, gStyle
from rootpy.interactive import wait
#~ from rootpy.plotting import Hist
import numpy as np
import copy

COLORS=[2,8,4,6,7,9]

import rootpy.compiled as C
pwd = os.path.dirname(__file__)
print pwd
C.register_file( pwd + "/mylangaus.cxx", ["langaufun"])

    #TODO:
    # RUN ROOT interactive with Python
    # 1. fit with simple function.
    # 2. autoguess fit parameters.
    # 3. fit multiple at once


def root_fit(data_tuples, title=None, outfile=None, bins=None, histopts={}, gui=True, quiet=False):
    
    if gui:
        gROOT.Reset()
        gStyle.SetOptFit(0)
        gStyle.SetOptStat(0)
        c1 = TCanvas( 'c1', title , 200, 10, 700, 500 )
        c1.SetGrid()
        legend = TLegend(0.5, 0.8, 0.9,0.9)
    
    langaufun = TF1( 'langaufun', C.langaufun, 250, 2500 )
    
    # Copy() generates Segfault for some reason, so make dummy copies of function:
    fitfuncs = []
    for i in range(0,len(data_tuples)):
        func = TF1( 'fitfunc', 'langaufun(&x,[0],[1],[2],[3]) + 0.001*[4]*exp(-0.001*[5]*x)', 250, 2500 )
        func.SetParNames ('Langaus Width Landau','Langaus MPL','Langaus Area','Langaus Width Gauss','expA','expB')
        fitfuncs.append(func)
    
    for idx, (label, data) in enumerate(data_tuples):
    
        if data is None:
            continue
        
        hist = TH1F("hist" + str(idx) ,"myhist" + str(idx) ,50, 0, 2500)
        [hist.Fill(_) for _ in data]
        
        integral = hist.Integral()
        if integral > 0:
            hist.Scale(1/integral)

        # Fit Histogram
        fitfunc = fitfuncs[idx]
        fitfunc.SetParameters(  50.0, 1000.0, 20.0, 100.0, 30, 0.8)
        
        # SQMRN = S(ave fitres), Quiet, More (improve results), Range (of the function), No (drawing)
        fitres = hist.Fit(fitfunc, "SQMRN+" )
        
        if not quiet:
            fitres.Print()
    
        print 'val= %f' % fitres.Parameter(1) # TODO: error
        print 'prob=%.2f' % fitres.Prob()

        if gui:
            hist.SetLineColor(COLORS[idx]);
            fitfunc.SetLineColor(COLORS[idx]);
            
            if idx == 0:
                hist.Draw('HIST')
            else:
                hist.Draw('HIST SAMES')

            fitfunc.Draw('SAME')
            legend.AddEntry(hist, label, "f")   

    if gui:
        legend.Draw()
        c1.Update()
        wait(True)
    
    #~ c1.SaveAs?
    #~ c1.Print("c1.pdf", "pdf");


if __name__ == "__main__":
    main()
