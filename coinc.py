#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Find coincidential events in data stream (the lists of records with close timestamps)
and filter the list with a trigger (optional).

input stream: a sequence of records ordered by timestamp.
	you can get it with `sort --numeric-sort --merge data1.txt data2.txt ...`

output: records with coincidental timestamps (one file per channel). 

Author: Sergey Ryzhikov (sergey-inform@ya.ru), 2016
License: GPLv2
"""
import sys,os
import argparse
import io 

from collections import Counter
import logging


def print_err(format_str, *args, **kvargs):
	sys.stderr.write(format_str + '\n', *args, **kvargs)
	
conf = dict(
		prefix='coinc_',
		)

cluster_sz_counter = Counter() # cluster width (last_ts - first_ts)


class Coinc(object):
	""" Read and parse sorted iostream, 
	yield clusters of lines with coincidential timestamps.
	"""
	stats = Counter() # events per cluster
	counts = Counter() # various counters
	
	def __init__(self, iostream, **params):
		
		self.iostream = iostream
		self.reader = self._reader(self.iostream, **params)
		
	def _reader(self, iostream, threshold = None, jitter=1.0, ts_col=0, val_col=2 ):
		""" 
		:threshold: 	- if set, records with values less
				than `threshold` are ignored;
		:jitter: 	- maximum diff of timestamps;
		:ts_col:	- an index of column with a timestamp;
		:val_col:	- an index of column with a value.
		
		Yields one cluster at a time.
		"""
		
		counts = self.counts
		stats = self.stats
		
		lineno = 0
		cluster = [] # to be yielded
		
		prev_ts = None
		prev_fields = None
		
		for line in iostream:
			lineno += 1
			
			fields = tuple(line.split())
			try:
				ts = float( fields[ts_col] )
				val = float( fields[val_col] )
		
			except IndexError as e:
				logging.error('%s , iostream line: %d' % (e, lineno) )
				raise
			
			except ValueError as e:
				logging.error('%s , iostream line: %d' % (e, lineno) )
				raise
			
			if ts < prev_ts:
				raise ValueError('input is not sorted, iostream line: %d' % lineno,)
			
			if threshold is not None:
				if val < threshold: 
					counts['nthreshold'] += 1
					continue # just ignore current line

			if ts - jitter >= prev_ts:  # True for `prev_ts is None`, since `None` < any value
			 	# not in the same cluster
				prev_ts = ts
				prev_fields = fields

				if cluster:
					stats[len(cluster)] += 1
					yield cluster 
					cluster = []
			else:
				# same cluster
				if not cluster: # start a new one
					cluster.append( prev_fields)
				cluster.append(fields)
				
				prev_ts = ts
				prev_fields = fields
			
		if cluster:
			yield cluster # the last coincidential cluster in iostream

	def next(self):
		return next(self.reader)
		
	def __iter__(self): 	# make the object iterable
		return self

	__next__ = next 	# reqiured for Python 3


class CombinationsTrigger(object):
	
	def _trigger(self, _reader, trigger_func, trigger_data, ts_col=0, chan_col=1):
		""" Generator, gets a next cluster of records from _reader. 
		Get a list of fired triggers for each record.
		Yield a list of tuples [(record_fields, triggers), ]. 
		"""
		for cluster in self.reader:
			records = [ dict(
					ts = float(rec[ts_col]),
					chan = int(rec[chan_col])
					) for rec in cluster ]
			triggers = trigger_func(records, trigger_data)
			yield zip(cluster, triggers)



def triggfunc_coinc( records, trigger_data, jitter=1.0):
	""" A simple trigger function, which finds coincidence 
	in channels according to predefined patterns.
	
	:records:   a list of tuples (ts, chan)
	:trigger_data:  dict (trig_name: [channels])
	:jitter: 	permitted jitter of timestamps
	
	Return a list with the same length as data_list, 
	[set(trigger_names), ...]
	"""
	ret = []
	
	for rec in records:
		trigs = set()
		
		adj_records = [r for r in records if abs(r['ts'] - rec['ts']) < jitter]
		adj_chans = set([r['chan'] for r in adj_records])
	
		for trig_name, trig_chans in trigger_data.iteritems():
			if set(trig_chans).issubset(adj_chans):
				trigs.add(trig_name)
			
		ret.append(trigs)
	return ret
	

def main():
	
	infile = sys.stdin.fileno()
	
	iostream = io.open(infile, 'rb')
	
	trigger_func = triggfunc_coinc
	trigger_data = dict(
			A = (0,1),
			B1 = (0,8),
			B2 = (1,8),
			C = (0,1,8),
			) 

	coinc = Coinc(iostream, threshold = 10)
	
	for a in coinc:
		#~ print(a)
		print(len(a))
		
	print_err(str(coinc.counts))
	print_err(str(coinc.stats))
	
	
if __name__ == "__main__":
    main()
		
