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

import numpy as np

CHAN_COL_IDX = 1  # if None, no channel filtering at all.
DATA_COL_IDX = 2


def print_err(format_str, *args, **kvargs):
	sys.stderr.write(str(format_str) + '\n', *args, **kvargs)


def sigint_handler(signal, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)


def parse_infile(_file, chans=None ):
	"""
	Parses a file with data records.
	
	chans:
		a list of channel names; if specified, skip channels not in list
	
	Returns a dict {channel_0: values_0, ... channel_N: values_N}
	"""
	lineno = 0
	ret = {}  
	
	for line in _file:
		lineno += 1

		fields = line.split()
		
		try:
			chan = fields[CHAN_COL_IDX] \
				if CHAN_COL_IDX is not None \
				else None
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

def plot(data, outprefix=None, bins=None, histopts={}):
	import matplotlib.pyplot as plt

	defaults = dict(
		
		)
	
	# set default values for missing options:
	histopts.update([(k,v) for k,v in defaults.items() if k not in histopts])
	
	
	for chan, chandata in data.items():
		
		fig = plt.figure()
		ax = fig.add_subplot(111)
		ax.grid(True)
		
		colors=cycle(['red','darkgreen','blue','black','brown','grey'])
		
		histdata = []
		
		for trigname, trigdata in sorted(chandata.items()):
			#http://stackoverflow.com/questions/5328556/histogram-matplotlib
			
			label = trigname 
			if 'normed' in histopts and histopts['normed']:
			#if 'density' in histopts and histopts['density']:  # use in future matplotlib versions
				label += r' (%d)' % len(trigdata)  # add a number of events
			
			
			if not bins:
				# optimize bin sizes
				bins = freedman_bin_width(trigdata)
				print 'nbins', bins
			
			n, bins_, patches = ax.hist(
				trigdata,
				bins,
				color=next(colors),
				label=label,
				**histopts
				)
			
			histdata.append( (n,bins_,patches) )
		
		plt.title('chan: %s' % str(chan))
		legend = plt.legend()
		plt.draw()
		
		if outprefix:
			fn = str(outprefix) + str(chan) + '.png'
			plt.savefig(fn)
		else:
			plt.show()
	

def freedman_bin_width(data):
	"""Return the optimal number of bins using the Freedman-Diaconis rule

	The Freedman-Diaconis rule is a normal reference rule like Scott's
	rule, but uses rank-based statistics for results which are more robust
	to deviations from a normal distribution.

	
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
	
	return nbins *2
	
	
	
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
			type=str, 
			metavar = 'N',
			default = CHAN_COL_IDX,
			help='an index of column with a channel name'
				';\n if None, all data belongs to the same channel'
				' (default: %d)' % CHAN_COL_IDX
			)
	parser.add_argument('--data-col',
			type=str, 
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
	
	# change default column indexes for channel names
	CHAN_COL_IDX = args.chan_col  # can be None
	
	# parse the channels
	chans = args.chan.split(',') if args.chan is not None else None
	if not args.quiet:
		print_err('chans: %s' %str(chans) )
		
	# create dir for output
	outpath = makedirs(args.output)
	
	# parse range
	_range = None
	try:
		if args.range:
			_range = map(float, args.range.split(':')[:2])
	
	except ValueError:
		print_err('wrong range value "%s" (should be two numbers, separated by ":")' % args.range)
		exit(1)
	
	# get a number of bins
	nbins = args.bins

	# Parse the data
	data = parse_infiles(args.infiles, chans=chans)  # { chan: [[values], ] ...}, ... }

	# Set default values
	for chan, val in data
	
	
	if _range is None:
		_range = auto_range()
	
	if bins is None:
		bins = auto_bins()

	histopts = dict(
		normed=args.normalize,  # replace with density=True in future matplotlib versions 
		range=_range,
		alpha=0.75,
		histtype='step',
		)

	chans = data.keys()  # channel names found
	
	exit(0)
	
	for chan in sorted(chans):  # TODO: numeric sort
		pass
	
	
	
	# todo: for chan in ... 
	# 		plot()
	
	# TODO: if --root-fit
	# try to fit with root_fit instead of plotting
	plot(data, bins = args.bins, outprefix = prefix, histopts=opts )
	
	
	# TODO: range_min, range_max = percentile[5, 85] 
	# range_min = 0 if range_min > 0 and range_min/range_max < 0.3
	# auto_range
	# auto_bins
	#
	
	#~ print('Press Ctrl+C')
	#~ signal.pause()


def auto_range(data):
	return (0,4000)
	
def auto_bins(datasets):
	
	dataiter = (d[:1000] for d in datasets)
	
	np.concatenate(dataiter)
	return 100
	


def parse_infiles(infiles, chans=None):
	"""
	Call parse_infile for each infile and merge the data by channel name.
	
	Return dict of lists of lists:
		{ channame: [[values], ...], ... }
	"""
	data = {}
	for fd in infiles:
		parsed = parse_infile(fd, chans=chans) 

		for channame, values in parsed.items():
			if channame not in data:
				data[channame] = []
				
			data[channame].append(values)
	
	return data
	
	
def makedirs(path):
	""" Create directories for path (like `mkdir -p ...`). """
	if not path:
		return

	folder = os.path.dirname(path)
	if folder and not os.path.exists(folder):
	    os.makedirs(folder)



if __name__ == "__main__":
    main()
