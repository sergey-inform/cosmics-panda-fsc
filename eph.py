#!/usr/bin/env python
""" Count events per hour for each channel in a sorted list of records.
	input columns: <timestamp> <chan> ...
	output columns: "<hour> <eph> ... <ephN>"
"""

import sys, os
import argparse
from collections import Counter

HZ = 250 * 1000 * 1000 # timestamp = HZ * seconds

def main():
	parser = argparse.ArgumentParser(description=__doc__,
		formatter_class=argparse.RawTextHelpFormatter,
		epilog='(c) Sergey Ryzhikov <sergey.ryzhikov@ihep.ru>, 2016.\nLicense: GPLv2')
	
	
	parser.add_argument( 'infile',
			type=argparse.FileType('r'),
			default=sys.stdin,
			help='data file (stdin by default)')
	
	args = parser.parse_args()
	
	ts_increment = HZ * 3600
	next_ts = ts_increment
	count = Counter()
	hr = 0
        lineno = 0
	channels = None
	
	for line in args.infile:
		
		if line[0] == '#':
			continue  # skip comments

                lineno +=1
		
		line = '\t'.join(line.split())
		ts, chan, rest = line[:-1].split('\t', 2)  #stip '\n' without making a copy of the string
		ts = float(ts)
		
		count[chan] += 1

		if ts > next_ts:
			hr +=1
			next_ts = ts + ts_increment
			
			if not channels:
				channels = sorted(count.keys())
				#print header
				print("\t".join(["hr\chan"] + channels) )
			
			#print the data
			values = [count[c] for c in channels]
			print('%d\t%s\t%d' % (hr, '\t'.join( map(str, values) ), lineno ) ) 
			
			count = Counter()
		
	
if __name__ == "__main__":
	main()
