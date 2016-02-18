#!/usr/bin/env python
""" Plot a simple histogram using data in a text file."""

import sys, os
import argparse

CHAN_COL_NUM = 1
TRIG_COL_NUM = 2
DATA_COL_NUM = 3

def main():
	parser = argparse.ArgumentParser(description=__doc__,
		formatter_class=argparse.RawTextHelpFormatter,
		epilog='(c) Sergey Ryzhikov <sergey.ryzhikov@ihep.ru>, 2016.\nLicense: GPLv2')
	
	parser.add_argument( 'infile',
			type=argparse.FileType('r'),
			default=sys.stdin,
			help='data file (stdin by default)')
	
	parser.add_argument('-c','--chan',
			type=str,
			help='channel number')
			
	parser.add_argument('--fit', 
			type=bool,
			help='try to fit the data')
			
	args = parser.parse_args()
	
	count = 0
	skipped_count = 0
	data = {}
	
	for line in args.infile:
		columns = line[:-1].split('\t') #stip '\n' without making a copy of the strin
		chan = columns[CHAN_COL_NUM]
		
		if args.chan and chan != args.chan:
			skipped_count += 1
			continue
		
		val = float(columns[DATA_COL_NUM])
		trig = columns[TRIG_COL_NUM]
		
		if trig not in data:
			data[trig] = []
		
		data[trig].append(val)
		count +=1
	
	print "count", count
	print "skipped_count", skipped_count
	
	if not data:
		sys.stderr.write('NO DATA FOUND!\n')
		exit(0)
	
	## Draw histogram with ROOT
	if (args.fit):
		import test_fit0
		for trig in data:
			title = "chan %s trig %s"% (chan, trig)
			test_fit0.draw_fit_hist(data[trig],"", title= title)
	else:
		#plot hist with no fit
		import matplotlib.pyplot as plt
		import numpy as np
		
		for trig in data:
			arr = np.array(data[trig])
			
			
			mean = np.mean(arr)
			std = np.std(arr)
			min_ = np.percentile(arr, 1)
			max_ = np.percentile(arr, 80)
			range_ = (min_, max_)
			
			title = "chan %s trig %s"% (chan, trig)
			plt.hist(arr, 50, range=range_, histtype='step', facecolor='g', zorder=0)
			
			plt.title(title)
			plt.show(block=False)
if __name__ == "__main__":
	main()
