#!/usr/bin/env python
""" Plot the histograms and try to fit the data in a palin text file.
  
Histograms are plotted and fitted per trigger for each channel.

The input file columns:
<timestamp:float> <channel:int> <trigger:str> <data:float> <...>
"""

import sys, os
import argparse

TS_COL_NUM   = 0	# timestamp (float)
CHAN_COL_NUM = 1	# channel  (int)
TRIG_COL_NUM = 2	# trigger (str)
VAL_COL_NUM  = 3	# value (float)

EXCLUDE_TRIG=['ALL', ]

def hist(data, title, outfn=None, histopts={}):
	import matplotlib as mpl
	mpl.use('Agg')
	import matplotlib.pyplot as plt
	import numpy as np

	if not outfn:
		plt.switch_backend('WX')

	arr = np.array(data)
	
	print 'arr'

	mean = np.mean(arr)
	std = np.std(arr)
	min_ = np.percentile(arr, 1)
	max_ = np.percentile(arr, 80)
	range_ = (min_, max_)

	print 'stat'
	
	plt.hist(arr, 50, range=range_, histtype='step', facecolor='g', zorder=0, label=title)
	plt.title(title)
	plt.legend()

	print 'hist'	
	plt.xlim(0.0, plt.xlim()[1]) #begin x from 0
	plt.xlim( plt.xlim()[0], 2500.0) #set x max

	if not outfn:
		fig =plt.gcf()
		fig.set_tight_layout(True)	
		plt.show()
	else:
		plt.savefig(outfn)
	
	
	print 'done'


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
			
		if ch < 0:
			sys.stderr.write("Wrong data in line %d, channel number < 0\n" % (lcount,) )
			exit(1)
	
		if chan is not None and ch != chan: #skip data for all channels except chan 
			lcount_skipped += 1 
			continue
		
		try:
			data[ch][tr] = val
			
		except KeyError:
			if ch not in data:
				data[ch] = {}
			if tr not in data[ch]:
				data[ch][tr] = []
			
			data[ch][tr] = val
	
	sys.stderr.write("* lines count: %d (skipped:%d, processed:%d) \n" %(lcount, lcount_skipped, lcount-lcount_skipped))
	return data
		
def main():

	args = parse_cmdline()

	# check DISPLAY variable.
	# if None, force batch mode
	
	if os.environ.get('DISPLAY') is None:
		args.batch = True
		sys.stderr.write("No $DISPLAY. So running in batch mode.\n")
	#~ print args
	
	data = parse_infile(args.infile, chan=args.chan)
	#~ print sorted(data.keys())
	
	if not data:
		sys.stderr.write('NO DATA FOUND for selected channels!\n')
		exit(0)
	
	
	# Make the histograms
	
	for ch in data:
		outfile = None
		if args.output:
			outfile = os.path.splitext(args.output)[0]+'_ch%d.png'%(ch,)

		#~ print outfile
	
	
	exit(0)
	
		
			
if __name__ == "__main__":
	main()
