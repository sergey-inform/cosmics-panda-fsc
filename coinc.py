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
from collections import namedtuple
import logging


def print_err(format_str, *args, **kvargs):
	sys.stderr.write(format_str + '\n', *args, **kvargs)

	
conf = dict(
		prefix='out/coinc_',
		)


Record = namedtuple('Record', 'ts, chan, val, raw')


class Coinc(object):
	""" Read and parse sorted iostream, 
	yield clusters of lines with coincidential timestamps.
	"""
	stats = Counter() # events per cluster
	counts = Counter() # various counters
	
	def __init__(self, iostream, **params):
		
		self.iostream = iostream
		self.reader = self._reader(self.iostream, **params)
		
	def _reader(self, iostream, threshold = None, jitter=1.0, ts_col=0, chan_col=1, val_col=2 ):
		""" 
		:threshold: 	- if set, records with values less
				than `threshold` are ignored;
		:jitter: 	- maximum diff of timestamps;
		:ts_col:	- an index of column with a timestamp;
		:chan_col:	- 
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
			
			fields = line.split()
			try:
				ts = float( fields[ts_col] )
				chan = fields[chan_col]
				val = float( fields[val_col] )
				
				record = Record( ts, chan, val, line)
		
			except IndexError as e:
				logging.error('%s , iostream line: %d' % (e, lineno) )
				raise
			
			except ValueError as e:
				logging.error('%s , iostream line: %d' % (e, lineno) )
				raise
			
			if ts < prev_ts:
				raise ValueError('input is not sorted, iostream line: %d' % lineno,)
			
			if val < threshold:	# always false if threshold is None
				counts['nthreshold'] += 1
				continue # just ignore current line

			if ts - jitter >= prev_ts:  # true if prev_ts is None, since None is < than any value
			 	# not in the same cluster
				prev_ts = ts
				prev_rec = record

				if cluster:
					stats[len(cluster)] += 1
					yield cluster 
					cluster = []
			else:
				# same cluster
				if not cluster: # start a new one
					cluster.append( prev_rec)
				cluster.append(record)
				
				prev_ts = ts
				prev_rec = record
			
		if cluster:
			yield cluster # the last coincidential cluster in iostream

	def next(self):
		return next(self.reader)
		
	def __iter__(self): 	# make the object iterable
		return self

	__next__ = next 	# reqiured for Python 3


class CombinationsTrigger(object):
	
	def __init__(self, _conf):
		# TODO: Check _conf
		# TODO: map trig names to str()
		self.conf = _conf
		pass
	
	def check(self, rec_list, jitter=1.0):
		"""
		Get all fired triggers for each record.
		Return a list of sets of triggers.
		
		"""
		ret = [set()] * len(rec_list)
		
		for idx, rec in enumerate(rec_list):
			adj_records = [r for r in rec_list if abs(r.ts - rec.ts) < jitter]
			adj_chans = set([r.chan for r in adj_records])
		
			for trig_name, trig_chans in self.conf.iteritems():
				if set(trig_chans).issubset(adj_chans):
					ret[idx].add(trig_name)
		return ret
		
		
def main():
	
	infile = sys.stdin.fileno()
	
	iostream = io.open(infile, 'rb', buffering=1024*1024)
	
	trigger_conf = dict(
			A = ('0','1'),
			B1 = ('0','8'),
			B2 = ('1','8'),
			C = ('0','1','8'),
			) 

	outstreams = {}
	
	#create out dir
	folder = os.path.dirname(conf['prefix'])
	if not os.path.exists(folder):
	    os.makedirs(folder)

	for trig_name in trigger_conf.keys():
		fn = conf['prefix'] + trig_name + '.txt'
		#TODO: check file not exists
		outstreams[trig_name] = io.open(fn, 'wb')
		
	print_err(str(outstreams))
		
	
	coinc = Coinc(iostream, threshold = 10)
	trig = CombinationsTrigger(trigger_conf)
	
	
	for cluster in coinc:
		triggers = trig.check(cluster)

		print(len(cluster))
		#~ print(triggers)
		
		for idx, trigs in enumerate(triggers):
			for tr in trigs:
				outstreams[tr].write(cluster[idx].raw)

		
	print_err(str(coinc.counts))
	print_err(str(coinc.stats))
	
	
if __name__ == "__main__":
    main()
		
