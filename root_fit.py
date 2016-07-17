#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fit data with a custom function.

Author: Sergey Ryzhikov (sergey-inform@ya.ru), 2016
License: GPLv2
"""
import sys
from ROOT import TH1F, TF1, TCanvas, gROOT, gStyle
from rootpy.interactive import wait
#~ from rootpy.plotting import Hist
import numpy as np

import rootpy.compiled as C
C.register_file("mylangaus.C", ["langaufun"])

	#TODO:
			# RUN ROOT interactive with Python
			# 1. fit with simple function.
			# 2. autoguess fit parameters.
			# 3. fit multiple at once


def root_fit(datasets, **params):
	hists = [] 
	
	
	gROOT.Reset()
	c1 = TCanvas( 'c1', 'Example', 200, 10, 700, 500 )
	c1.SetGrid()

	gStyle.SetOptFit(1111)
	langaufun = TF1( 'langaufun', C.langaufun, 500, 2500 )
	fitfunc = TF1( 'fitfunc', 'langaufun(&x,[0],[1],[2],[3]) + exp([4]-0.001*[5]*x)', 500, 2500 )
	
   #~ //par[0]=Width (scale) parameter of Landau density
   #~ //par[1]=Most Probable (MP, location) parameter of Landau density
   #~ //par[2]=Total area (integral -inf to inf, normalization constant)
   #~ //par[3]=Width (sigma) of convoluted Gaussian function
	
	for dataset in datasets:
		
		#~ hist = Hist(50, 0, 2500)
		hist = TH1F("hist","myhist",50, 0, 2500)
		[hist.Fill(_) for _ in dataset]
		
		integral = hist.Integral()
		if integral > 0:
			hist.Scale(1/integral)

		fitfunc.SetParameters(  100.0, 1000.0, 10.0, 150.0, -3.0,2.0)
		#SetParNames
		fitres = hist.Fit('fitfunc', "QSR" )
		
		#~ hist.SetFillColor(2)
		#~ hist.SetBarWidth(1.0)
		hist.Draw('HIST')
		
		#~ fitfunc.SetLineColor(4)
		fitfunc.Draw('SAME')
		
		c1.Update()
		wait(True)


if __name__ == "__main__":
	main()
