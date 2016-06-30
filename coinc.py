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


def print_err(*args, **kvargs):
	sys.stderr.write(*args, **kvargs)
	
conf = dict(
		prefix='coinc_',
		)


cluster_counter = Counter() # events per cluster
cluster_sz_counter = Counter() # cluster width (last_ts - first_ts)
record_stats = Counter()


class Coinc(object):
	""" Read and parse iostream, yild lines with coincidential timestamps.
	"""
	
	def __init__(self, iostream, triggers, threshold = None):
		self.iostream = iostream
		self.reader = self._reader(self.iostream, threshold = threshold)
		self.trigger = self._trigger(self.reader, None)
		
	
	
	def _reader(self, iostream, threshold=None, jitter=1.0, ts_col=0, val_col=2):
		""" Generator, splits iostream into clusters of records,
		intervals between timestamps of adjaсent records within
		cluster are less than jitter. 
		
		:threshold: 	- if set, records with values less
				than `threshold` are ignored;
		:jitter: 	- maximum diff of timestamps;
		:ts_col:	- an index of column with a timestamp;
		:val_col:	- an index of column with a value.
		
		Yields one cluster at a time.
		"""
		lineno = 0
		cluster = [] # to be yielded
		prev_ts = None
		prev_fields = None
		
		for line in iostream:
			lineno += 1
			
			fields = tuple(line.split())
			try:
				ts = float(fields[ts_col])
				val = float(fields[val_col])
		
			except IndexError:
				#TODO: do something clever
				print_err('err line: %d' % (lineno, ))
				raise
			except ValueError as e:
				print_err('err line: %d' % (lineno, ))
				raise
				
			if threshold is not None and val < threshold: 
				record_stats['nthreshold'] += 1
				continue # just ignore current line
			
			if prev_ts >= ts - jitter:  # False for `prev_ts is None`, since `None` < any value
			 	# records are in the same cluster
			 	if not cluster: # start a new cluster
					cluster.append( prev_fields)
				cluster.append(fields)
				continue

			prev_ts = ts
			prev_fields = fields

			if not cluster:  # nothing to yield
				continue
			else:
				yield cluster 
				cluster_counter[len(cluster)] += 1
				cluster = []
				
		if cluster:
			yield cluster # the last coincidential cluster in iostream


	#~ def _trigger(self, _reader, triggers, jitter=1.0, chan_col = 1):
		#~ """ Gets next cluster of records from _reader. 
		#~ Check each record if it satisfies some of the triggers.
		#~ Yield a list of tuples [(record_fields, triggers), ]. 
		#~ """
		#~ if not triggers:
			#~ raise ValueError('No triggers to match')
		#~ 
		#~ for cluster in self.reader:
			#~ for rec in cluster:
				#~ for trig in triggers:
					#~ trig.check(
					
			
			
				
	def next(self):
		#~ return next(self.reader)
		return next(self.trigger)
		
	def __iter__(self): 	# make the object iterable
		return self
	
	__next__ = next 	# reqiured for Python 3


def main():
	
	infile = sys.stdin.fileno()
	
	iostream = io.open(infile, 'rb')
	trigger = None

	coinc = Coinc(iostream, trigger, threshold = 0)
	
	for a in coinc:
		print(a)
		
	print_err(str(record_stats))
	print_err(str(cluster_counter))
	
	
if __name__ == "__main__":
    main()
		
