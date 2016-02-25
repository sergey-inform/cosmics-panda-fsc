#!/usr/bin/env python
""" Count events per hour for each channel.
	input columns: timestamp chan trig ...
	output columns: "hour chan trig eph"
"""

import sys, os
import argparse

HZ = 250*1000*1000 

def main():
	parser = argparse.ArgumentParser(description=__doc__,
		formatter_class=argparse.RawTextHelpFormatter,
		epilog='(c) Sergey Ryzhikov <sergey.ryzhikov@ihep.ru>, 2016.\nLicense: GPLv2')
	
	
	parser.add_argument( 'infile',
			type=argparse.FileType('r'),
			default=sys.stdin,
			help='data file (stdin by default)')
	
	args = parser.parse_args()
	
	count_chan = {} #count events for only one channel for each trigger
	count = {}
	hr = 0
	ts_increment = HZ * 3600
	next_ts = ts_increment # to make thins faster we use one ts for all channels
	triggers = None
	
	for line in args.infile:
		ts, chan, trig, rest = line[:-1].split('\t', 3) #stip '\n' without making a copy of the strin
		ts = float(ts)
		
		if trig not in count_chan:
			count_chan[trig] = chan
			count[trig] = 0
		
		if chan == count_chan[trig]:
			count[trig] += 1
		
		if ts > next_ts:
			hr +=1
			next_ts = ts + ts_increment
			#print the data
			
			if not triggers:
				triggers = sorted(count)
				#print header
				print("\t".join(["hr"] + triggers) )
			
			values = [count[t] for t in triggers]
			print('%d\t%s' % (hr, '\t'.join( map(str, values) ) ) ) 
			
			count = {}
			count_chan = {}
		
	
if __name__ == "__main__":
	main()
