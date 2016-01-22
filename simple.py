#!/usr/bin/env python
'''________________________________________________________________________

  Analyze data file in plain text format.
  Data format:
    <timestamp> <channel number> <trigger> <data> <...>
  
  For each combination of a channel number and event selector (trigger)
  plot the data histograms and find the most probable values.
    
  Plots will be saved in the directory "<infile>_plots".
________________________________________________________________________
'''

import os, sys
import argparse
from operator import itemgetter

from matplotlib	import pyplot as plt
import numpy
from numpy import diff, sign


def parse_cmdline_args():
	''' Parse command line arguments or print usage information. '''
	parser = argparse.ArgumentParser(description=__doc__,
			formatter_class=argparse.RawTextHelpFormatter,
			epilog='(c) Sergey Ryzhikov <sergey.ryzhikov@ihep.ru>, 2016.\nLicense: GPLv2')
	
	parser.add_argument( 'infile',
			type=argparse.FileType('r'),
			default=sys.stdin,
			help='data file (stdin by default)')
	
	parser.add_argument('-d', '--delimiter',
			type=str,
			default='\t',
			metavar='DELIM',
			help='use DELIM instead of TAB for field delimiter')
			
	parser.add_argument('-f', '--fields',
			type=str,
			metavar='N1,N2,N3,N4',
			default='0,1,2,3',
			dest='fieldnums',
			help='a list of field numbers for <ts> <chan> <trig> <val>'
			'\n0,1,2,3 by default\n\n')	
			
	parser.add_argument('--debug',
			action='store_true',
			help='show debug messages')
	
	args = parser.parse_args()
	
	#Field numbers
	try:
		args.fieldnums = [int(item) for item in args.fieldnums.split(',')]
		
	except ValueError:
		sys.stderr.write("Wrong field numbers: '%s'\n" % args.fieldnums)
		exit(1)
		
	if len(args.fieldnums) != 4:
		sys.stderr.write("waiting 4 field numbers, got %d: '%s'\n" % (len(args.fieldnums), args.fieldnums))
		exit(1)
	
	return args


def smooth(x):
	""" Smooth data """
	window = 20
	s=numpy.r_[x[window-1:0:-1],x,x[-1:-window:-1]] #prevent edge effects
	#~ print s
	#~ w=numpy.ones(window,'d')
	w=numpy.hanning(window)
	return numpy.convolve(w/w.sum(),s,mode='same')[window-1:-window+1]
	
	
	

def main():
	# 1. Read command line arguments
	args = parse_cmdline_args()
	
	# 2. Parse the input file, get the data for the histograms
	infile = args.infile
	delim = args.delimiter
	fieldnums = args.fieldnums
	linecount = 0
	
	data = {}
	
	for line in infile.readlines():
		linecount +=1
		
		fields = line[:-1].split(delim) #stip '\n' without making a copy of the string
		try:
			ts, chan, trig, val = itemgetter(*fieldnums)(fields) #http://stackoverflow.com/a/6632205
			ts = float(ts)
			chan = int(chan)
			val = float(val)
			
		except IndexError as e:
			sys.stderr.write('Error: '+ str(e) + '\n')
			sys.stderr.write('Values: ' + str(fields) + '\n')
			sys.stderr.write('field numbers to nupack: ' + str(fieldnums)  + '\n')
			exit(-1)
	
		#save values 
		try:
			data[(chan,trig)].append(val)
		except KeyError:
			data[(chan,trig)] = [val]
	
	
	# 3. Create a subdirectory for plots in current/working directory
	filename = os.path.basename(infile.name)
	plotdir_name = os.path.splitext(filename)[0] + '_plots'
	
	if not os.path.exists(plotdir_name):
		if args.debug:
			sys.stderr.write('* Creating directory "%s".\n' % plotdir_name)
		os.makedirs(plotdir_name)
	
	
	# 4. Plot the histograms
	channels, triggers = map(set, zip(*data))
	histograms = {}
	opts = {'range':(200,10000), 'bins':100, 'alpha':0.9, 'normed': 1,  'histtype':'step'}
	exclude = 'ALL',
	
	for chan in channels:
		filename = plotdir_name + '/chan%d.png'%chan
		plt.clf()
		
		for trig in triggers:
			if (chan,trig) in data and trig not in exclude:
				values = data[(chan,trig)]
				nevents = len(values)
				
				label = str(trig) + ': ' + str(nevents)	
				
				n, bins, patches =  plt.hist(values, label=label, **opts)
				histograms[(chan,trig)]  = n, bins
				
				## Find local maximum
				
				n_smooth =  smooth(n) #smooth data
				plt.plot(bins[1:],n_smooth)
				
				range_ = [2, 60]
				
				n_smooth_range = n_smooth[range_[0]: range_[1]]
				
				min_ = (diff(sign(diff(n_smooth_range))) > 0).nonzero()[0] + 1 # local min
				max_ = (diff(sign(diff(n_smooth_range))) < 0).nonzero()[0] + 1 # local max
				
				if min_:
					min_ = min_[0] + range_[0]
				else:
					min_ = 0
				
				max_ = max_[-1]
				
				print chan, trig, 'min', min_, 'max', max_
					
			#crop the data by y value at min.
			
			#fit with exponential + gauss
				
		ax = plt.gca()
		ax.set_ylim([0,0.00030])
		
		plt.legend()
		plt.savefig(filename)
		
	
	


if __name__ == "__main__":
    main()
