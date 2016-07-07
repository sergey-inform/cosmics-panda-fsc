#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Find coincidential events in data stream (by timestamps) which match specified trigger.

Input: a sequence of records ordered by timestamp.
	format: <timestamp> <channel> <value> <...>
	You can join multiple input files with `sort --numeric-sort --merge data1.txt data2.txt ...`

Triggers:
	combinations_trigger - channels match specified pattern
	...

Output: records with coincidental timestamps (one file per channel). 

Example:
  `pv -c ../sorted.txt | ./coinc.py -p triggers.txt --jitter=2.0 --stats --progress

Author: Sergey Ryzhikov (sergey-inform@ya.ru), 2016
License: GPLv2
"""
import sys,os
import argparse
import signal
import io
import re # to parse cmdline arguments

from collections import Counter
from collections import namedtuple
import logging


TS_COL = 0
CHAN_COL = 1
VAL_COL = 2

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
		
	def _reader(self, iostream, threshold = None, jitter=1.0, ts_col=TS_COL, chan_col=CHAN_COL, val_col=VAL_COL ):
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

			if ts - jitter > prev_ts:  # true if prev_ts is None, since None is < than any value
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
	""" Channels are match specified pattern.
	"""
	def __init__(self, _conf):
		self.conf = {}
		for name, chans in _conf.iteritems():
			self.conf[name] = map(str, set(chans))
	
	def check(self, rec_list, jitter=1.0):
		""" 
		Returns a set of fired triggers for each record. """
		ret = [set() for _ in rec_list]
		
		for idx, rec in enumerate(rec_list):
			
			# select adjacent records
			adj_records = [r for r in rec_list if abs(r.ts - rec.ts) <= jitter]
			adj_chans = set([r.chan for r in adj_records])
			
			
			# check all triggers
			for trig_name, trig_chans in self.conf.iteritems():
				
				if set(trig_chans).issubset(adj_chans): #trig fired

					if rec.chan in trig_chans: # event in trigger

						ret[idx].add(trig_name)
		return ret
		

#///////////////////////////////////////////////////////////////////////

def print_err(format_str, *args, **kvargs):
	sys.stderr.write(str(format_str) + '\n', *args, **kvargs)


def fin(signal=None, frame=None):
	if signal == 2:
		print_err('\nYou pressed Ctrl+C!')
	sys.exit(0)	


def parse_chan_patterns(lines):
	""" Parse CombinationsTrigger configuration lines. """
	_conf = {}
		
	lines = [re.sub(r"\s+", "", line, flags=re.UNICODE) for line in lines] #strip whitespace
	lines = [line.partition('#')[0] for line in lines] 	#strip comments
	lines = filter(None, lines)	#remove empty strings
	
	for line in lines:
		try:
			name, chans = line.split(':')
		except ValueError:
			raise ValueError('can\'t parse pattern "%s"' %line)
			
		chan_set = set( chans.split(',') )
		 
		if name and chan_set:
			_conf[name] = chan_set
	return _conf

	
def main():
	signal.signal(signal.SIGINT, fin)
	
	parser = argparse.ArgumentParser(description=__doc__,
			formatter_class=argparse.RawTextHelpFormatter)
	
	parser.add_argument('-f','--file', type=str, default=sys.stdin.fileno(),
			help="input from a file (stdin by default)")
		
	parser.add_argument('-o','--output', type=str, default="out/coinc_",
			metavar='PATH',
			help="a path for output, one file per trigger. ('out/coinc_' by default)")
		
	parser.add_argument('-c', '--chan-pattern', type=str, action='append', default=[],
			metavar='PATTERN',
			help="a rule for combinations trigger (when channels in cluster match specified pattern)" '\n'
			"Pattern format: <name>:<ch1>,<ch2>,...<chN>" '\n'
			"for example:  'trigA':1,2,8,9 ")
	
	parser.add_argument('-p', '--pattern-file', type=argparse.FileType('r'),
			metavar='FILE',
			help="read channel patterns from a file"
			" (lines in the file should have the same format"
			" as in --chan-pattern option).")
	
	parser.add_argument('-j', '--jitter', type=float, default = 1.0,
			metavar='DIFF',
			help="maximal timestamp difference in coincidence (default: 1.0)")
			
	parser.add_argument('--threshold', type=float, default = None,
			metavar='VALUE',
			help="skip line when value is less then threshold")
		
	parser.add_argument('--stats', action='store_true',
			help="print some counters afterwards")
			
	parser.add_argument('--progress', action='store_true',
			help="print some progress")
		
	parser.add_argument('--debug', action='store_true',
			help="be verbose")
	
	parser.add_argument('--coinc', action='store_true',
			help="in debug mode print clusters of events with close timestamps, --debug required, options -o, -c, -p will be ignored")
	
	
	args = parser.parse_args()
	#~ print_err(args)
	
	debug = args.debug
	
	iostream = io.open(args.file, 'rb', buffering=1024*1024)
	
	trigrules = []
	if args.pattern_file:
		trigrules.extend( args.pattern_file.read().splitlines())
	
	if args.chan_pattern:
		trigrules.extend(args.chan_pattern)

	trigger_conf = parse_chan_patterns(trigrules)
	#~ trigger_conf = dict(
			#~ A = ('0','1'),
			#~ B1 = ('0','8'),
			#~ B2 = ('1','8'),
			#~ C = ('0','1','8'),
			#~ )
			
	outstreams = {}
	
	#create out dir
	prefix = args.output
	folder = os.path.dirname(args.output)
	if folder and not os.path.exists(folder):
	    os.makedirs(folder)
	
	if debug:
		print_err('infile: %s' % (iostream.name if iostream.fileno() != 0 else '<stdin>'))
		
	if iostream.isatty():
		print_err('You are trying to read data from a terminal!')
		exit(1)
	
	for trig_name in trigger_conf.keys():
		fn = prefix + trig_name + '.txt'
		#TODO: check file not exists
		outstreams[trig_name] = io.open(fn, 'wb')

	if debug:
		outfiles = [_file.name for _file in outstreams.itervalues()]
		print_err('outfiles:\n\t%s' % '\n\t'.join(outfiles))

	
	if debug:
		patterns = '\n\t'.join( [k + '-> ' + ' '.join(sorted(v)) for k,v in trigger_conf.iteritems()] )
		print_err('channel patterns: \n\t%s' % patterns )
	

	# Finally do the Job:
	coinc = Coinc(iostream, threshold = args.threshold, jitter=args.jitter)
	trig = CombinationsTrigger(trigger_conf)
	
	count = 0
	for cluster in coinc:
		
		if debug and args.coinc: 
			for record in cluster:
				sys.stdout.write(record.raw)
			print('--')
			continue
		
		triggers = trig.check(cluster, jitter = args.jitter)

		for idx, trigs in enumerate(triggers):
			for tr in trigs:
				outstreams[tr].write(cluster[idx].raw)
				count +=1
				if args.progress and count % 2000 == 0:
					sys.stderr.write(str(coinc.stats) + '\r')

	if debug or args.stats:
		print_err('')
		print('counters: %s' % str(coinc.counts))
		print('cluster size stats: %s' %str(coinc.stats))
	
	
if __name__ == "__main__":
    main()
		
