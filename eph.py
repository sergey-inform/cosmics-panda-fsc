#!/usr/bin/env python
""" Count events per hour for each channel in a sorted list of records.
	input columns: <timestamp> <chan> ...
	output columns: "<hour> <eph> ... <ephN>"
"""

import sys, os
import argparse

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
	count = {}  # {chan: count,}
	hr = 0
	channels = None
	
	for line in args.infile:
		ts, chan, rest = line[:-1].split('\t', 2) #stip '\n' without making a copy of the strin
		ts = float(ts)
		
		if chan not in count:
			count[chan] = 0
		
		count[chan] += 1
		

		if ts > next_ts:
			hr +=1
			next_ts = ts + ts_increment
			
			if not channels:
				channels = sorted(count)
				#print header
				print("\t".join(["hr"] + channels) )
			
			#print the data
			values = [count[c] for c in channels]
			print('%d\t%s' % (hr, '\t'.join( map(str, values) ) ) ) 
			
			count = {}
		
	
if __name__ == "__main__":
	main()
