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
from itertools import cycle # cycle facecolors

CHAN_COL_IDX = 1
DATA_COL_IDX = 2


def print_err(format_str, *args, **kvargs):
	sys.stderr.write(str(format_str) + '\n', *args, **kvargs)


def sigint_handler(signal, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)

def parse_input(_file, chans=None ):

	lineno = 0
	ret = {}  # {chan: np.array, ...}
	for line in _file:
		lineno += 1

		fields = line.split()
		try:
			chan = fields[CHAN_COL_IDX]
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

		except KeyError:
			ret[chan] = []
			ret[chan].append(val)

	return ret


def plot(data, outprefix=None, bins=50, histopts={}):
	import matplotlib.pyplot as plt

	defaults = dict(
		alpha=0.75,
		range=(0,4000),
		normed=True, # replace with density=True in future matplotlib versions 
		histtype='step',
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
			
			n, bins, patches = ax.hist(
				trigdata,
				bins,
				color=next(colors),
				label=label,
				**histopts
				)
			
			histdata.append( (n,bins,patches) )
		
		plt.title('chan: %s' % str(chan))
		legend = plt.legend()
		plt.draw()
		
		if outprefix:
			fn = str(outprefix) + str(chan) + '.png'
			plt.savefig(fn)
		else:
			plt.show()
	
	

def main():
	global CHAN_COL_IDX
	global DATA_COL_IDX
	
	signal.signal(signal.SIGINT, sigint_handler)
	
	parser = argparse.ArgumentParser(description=__doc__,
			formatter_class=argparse.RawTextHelpFormatter)
			
	parser.add_argument( 'infiles', type=argparse.FileType('r'),
			nargs='*',
			default=[sys.stdin],
			help='data files')

	parser.add_argument('-r', '--range', type=str,
			metavar='N:M',
			default='0:2000',
			help='a range of histogram values')
	
	parser.add_argument('--normalize', action='store_true',
			help="normalize histograms (show density)")
	
	parser.add_argument('-b', '--bins', type=int, default=100,
			help='a number of bins in the histogram')
			
	parser.add_argument('-c','--chan', type=str, 
			metavar = 'LIST',
			help='a list of channel names, separated by commas')
	
	parser.add_argument('--chan-col', type=str, 
			metavar = 'N',
			help='an index of column with a channel name')

	parser.add_argument('--data-col', type=str, 
			metavar = 'N',
			help='an index of column with a data')

	parser.add_argument('-o','--output', type=str, default=None,
			metavar='PATH',
			help="a path for output, one image per channel.")
	
	parser.add_argument('--debug', action='store_true',
			help="be verbose")
	
	args = parser.parse_args()
	#~ print_err(args)
	
	if args.data_col:
		DATA_COL_IDX = args.data_col
	if args.chan_col:
		CHAN_COL_IDX = args.chan_col
		
	_range = map(float, args.range.split(':')[0:2]) #TODO: catch errors

	#create out dir
	prefix = args.output
	if prefix:
		folder = os.path.dirname(args.output)
		if folder and not os.path.exists(folder):
		    os.makedirs(folder)
	
	data={} # { channame: {filename: [values], ...}, ... }
	
	
	# Parse the data
	chans = args.chan.split(',') if args.chan is not None else None
	
	print 'chans', chans
	
	for infile in args.infiles:
		filename = infile.name
		parsed = parse_input(infile, chans=chans) 

		for channame, values in parsed.items():
			if channame not in data:
				data[channame] = {}
				
			data[channame][filename] = values
		
			
	opts = dict(
		normed = args.normalize,
		range=_range,
		)
	
	plot(data, bins = args.bins, outprefix = prefix, histopts=opts )
	
	#~ print('Press Ctrl+C')
	#~ signal.pause()
	
if __name__ == "__main__":
    main()
