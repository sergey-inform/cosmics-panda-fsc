#!/usr/bin/env python
""" Plot the histograms and try to fit the data in a palin text file.
  
Histograms are plotted and fitted per trigger for each channel.

The input file columns:
<timestamp:float> <channel:int> <trigger:str> <data:float> <...>
"""

import sys, os
import argparse
import operator
from scipy.optimize import curve_fit
from numpy.random import normal as gauss
import numpy as np

TS_COL_NUM   = 0	# timestamp (float)
CHAN_COL_NUM = 1	# channel  (int)
TRIG_COL_NUM = 2	# trigger (str)
VAL_COL_NUM  = 3	# value (float)

RANGE = (0,2500)
BINS = 50

EXCLUDE_TRIG=['ALL', ]


def parse_cmdline():
	''' 
	Parse command line arguments 
	Return argparse.namespace object.
	'''
	parser = argparse.ArgumentParser(description=__doc__,
		formatter_class=argparse.RawTextHelpFormatter,
		epilog='(c) Sergey Ryzhikov <sergey.ryzhikov@ihep.ru>, 2016.\nLicense: GPLv2')
	
	parser.add_argument( 'infile',
			type=argparse.FileType('r'),
			help='the data file ("-" for stdin)')
	
	parser.add_argument('-o','--output',
			type=str,
			default=None,
			metavar="prefix",
			help='a file prefix for the plot(s)')
	
	parser.add_argument('-c','--chan',
			type=int,
			metavar='N',
			default=None,
			help='channel number')
			
	parser.add_argument('--fit', 
			action='store_true',
			help='try to fit the data with the "fitfunc()"')

	parser.add_argument('--batch', 
		action='store_true',
		help='do not try to display GUI')
	
	return parser.parse_args()


def parse_infile(infile, chan=None):
	'''
	Parse input file.
	Return {channel=>{trigger=>[values]}} ditctionary.
	'''
	data = {}
	lcount = 0 #line counter
	lcount_skipped = 0 #skipped lines
	
	
	if chan is None: #Get all channels
		pass
	
	for line in infile:
		lcount += 1
		cols = line[:-1].split() #stip '\n' without making a copy of the string
		
		try:
			ch, tr, val =	int(cols[CHAN_COL_NUM]),\
					cols[TRIG_COL_NUM],\
					float(cols[VAL_COL_NUM])
		
		except IndexError as e:
			sys.stderr.write("Wrong input format (not enougth columns) in line %d \n" % (lcount, ))
			exit(1)
		
		except ValueError as e:
			sys.stderr.write("Wrong data in line %d: %s\n" % (lcount, str(e)) )
			exit(1)
			
		if tr in EXCLUDE_TRIG:
			continue
		
		if ch < 0:
			sys.stderr.write("Wrong data in line %d, channel number < 0\n" % (lcount,) )
			exit(1)
	
		if chan is not None and ch != chan: #skip data for all channels except chan 
			lcount_skipped += 1 
			continue
		
		try:
			data[ch][tr].append(val)
			
		except KeyError:
			if ch not in data:
				data[ch] = {}
			if tr not in data[ch]:
				data[ch][tr] = []
			
			data[ch][tr].append(val)
		
	sys.stderr.write("* lines count: %d (skipped:%d, processed:%d) \n" %(lcount, lcount_skipped, lcount-lcount_skipped))
	return data


def gauss_expnoise(x, A, mu, sigma, exp_const, exp_curv):
	return A*np.exp(-(x-mu)**2/(2.*sigma**2)) + np.exp(exp_const + x * exp_curv)

def fit_many(ndata, bins, fitfunc):
	''' Fit 1D data with some function.
	Return fit parameters.
	'''
	
	xdata = bins[:-1] #FIXME: set x'es to the middles of the bins
	
	# 1. Concat data
	data_concat = map(operator.add, *ndata)

	# 2. Fit concatenated data 
	
	p0 = [100, 1000, 100, 200, -0.001] 
	lbounds = [10, 800, 10, 10, -0.000000001]
	ubounds = [1000, 1200, 1000, 1000, -0.1]
	popt, pcov = curve_fit(gauss_expnoise, xdata, data_concat, p0 = p0, bounds = (lbounds, ubounds))
	print 'popt', popt
	return popt, popt
	

def plot_many(ndata, title, fitfunc=None, outfn=None):
	'''
	Plot data histograms in a window (or to a file if outfn is set).
	If fit is set, fit data first and plot fit function.
	
	trdata: {str(Name)=>[data]}
	#~ fitfunc: func(x)
	outfn: str
	'''
	
	import matplotlib.pyplot as plt #the backend had been choosen in main()
	
	fig = plt.figure()
	
	ntitles = ["%s %d"%(str(k), len(ndata[k])) for k in ndata.keys()]
	nvals, bins, npatches = plt.hist(ndata.values(), bins=BINS, range=RANGE, histtype='step', label=ntitles)
	
	nparams = fit_many(nvals, bins, gauss_expnoise)
	
	for n in range(0,len(nparams)):
		print 'fit', ntitles[n], ': ', nparams[n]
		yvals = [gauss_expnoise(_, *nparams[n]) for _ in bins]
		plt.plot(bins, yvals, 'r-')
	
	plt.title(title)
	plt.legend()
	
	if outfn:
		plt.savefig(outfn)
		return
	
	plt.show()
		
		
	
def main():
	
	args = parse_cmdline()

	# check DISPLAY variable.
	# if None, force batch mode
	
	if os.environ.get('DISPLAY') is None:
		args.batch = True
		sys.stderr.write("No $DISPLAY. So running in batch mode.\n")
	#~ print args

	# We must choose pyplot backend before importing pyplot
	import matplotlib as mpl
	if args.output or args.batch:
		mpl.use('agg') # output to file
	else:
		mpl.use('WXAgg') # output in window
	import matplotlib.pyplot as plt
	
	
	data = parse_infile(args.infile, chan=args.chan)
	#~ print sorted(data.keys())
	
	if not data:
		sys.stderr.write('NO DATA FOUND for selected channels!\n')
		exit(0)
	
	for ch in data:
		outfile = None
		if args.output:
			outfile = os.path.splitext(args.output)[0]+'_ch%d.png'%(ch,)
		#~ print outfile
		
		title = outfile if outfile else "channel %s" % str(ch)
		plot_many(data[ch], title, outfn=outfile)
		
if __name__ == "__main__":
	main()
