#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Find coincidential events in data stream (the lists of records with close timestamps).

input stream: a sequence of records ordered by timestamp.
	you can get it with `sort --numeric-sort --merge data1.txt data2.txt ...`

output: records with coincidental timestamps (one file per trigger). 

Author: Sergey Ryzhikov (sergey-inform@ya.ru), 2016
License: GPLv2
'''
import sys,os
import argparse
import io 

from collections import Counter


def print_err(*args, **kvargs):
	sys.stderr.write(*args, **kvargs)
	
conf = dict(
		prefix="coinc_",
		)


event_counter = Counter()
record_stats = Counter()


class Coinc(object):
	''' Read and parse iostream, yild lines with coincidential timestamps.
	'''
	
	def __init__(self, iostream, triggers, threshold = None):
		self.iostream = iostream
		
		self.reader = self._reader(self.iostream, threshold = threshold)
		
	
	
	def _reader(self, iostream, threshold=None, jitter=1.0, ts_col=0, val_col=2):
		''' Generator, yields next coincidential events in iostream.
			:threshold:	values less then `threshold` are ignored
			:jitter: 	allowed difference between timestamps in one event
			:ts_col:	an index of column with a timestamp
			:val_col:	an index of column with a value 
		'''
		lineno = 0
		event = [] # to be yielded
		first_line = (None, None) #ts_max, fields
		
		for line in iostream:
			lineno += 1
			
			fields = tuple(line.split())
			try:
				ts = float(fields[ts_col])
				val = float(fields[val_col])
		
			except IndexError:
				#TODO: do something clever
				raise
				
			except ValueError as e:
				print e
				print('line: %d' % (lineno, ))
				
			if threshold and val < threshold: 
				# ignore current line
				record_stats['nthreshold'] += 1
				continue
			
			if first_line[0] > ts:  # False for first_line[0] == None, since None is <= than any value
			 	# first_line in coincidence with current
			 	if not event: # start a new event
					event.append( first_line[1])
				event.append(fields)
				continue

			# first_line is not in coincidence with current
			first_line = (ts + 2 * jitter,  fields) # first_line = current

			if not event:  # nothing to yield
				continue
			else:
				yield event
				event_counter[len(event)] += 1
				event = []
				

		yield event # the last coincidential event in iostream


			
				
	def next(self):
		return next(self.reader)
		
	def __iter__(self): 	# make the object iterable
		return self
	
	__next__ = next 	# reqiured for Python 3


class Trigger():
	def __init__(self, name, channels, func=None):
		self.name = name
		self.channels = set(channels)
		if not func:
			self.func = self.subset_check
		else:
			self.func = func #TODO: check callable
		pass
		#~ self.outfile
	
	def subset_check(self, items):
		''' Check if all required channels are in `items`. '''
		if self.channels.issubset(set(channels)):
			return True
		return False
		
		
def main():
	
	infile = sys.stdin.fileno()
	
	iostream = io.open(infile, 'rb')
	trigger = None

	coinc = Coinc(iostream, trigger, threshold = 10)
	
	for a in coinc:
		print(len(a))
		
	print_err(str(record_stats))
	print_err(str(event_counter))
	
	
if __name__ == "__main__":
    main()
		
