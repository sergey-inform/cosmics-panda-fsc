#!/usr/bin/env python
"""
Split file on timestamp wrap.

"""

import os
import sys
import io

BUFSIZE = 1024 * 1024 * 4



def copypart(fn_from, fn_to, start, sz, bufsize = 1024*1024*4):
	""" Copy a part of file to another one """
	# TODO : use system `dd`
	length = sz
	with open(fn_from,'rb') as infile, open(fn_to, 'wb') as outfile:
		infile.seek(start)
		while length:
			chunk = min(bufsize,length)
			data = infile.read(chunk)
			outfile.write(data)
			length -= chunk

	return

def main():
	filename = sys.argv[1]
	_file = io.open(filename,'rb', buffering=1024*2024)
	
	lineno = 0
	
	fragment_start=0 # bytes
	fragment_end=0  # bytes
	
	fragment_count=0 
	ts_prev=None
	
	for line in _file:
		lineno += 1
		
		try:
			ts = int(line.split()[0])
		except ValueError:
			sys.stderr.write("lineno %d: Wrong ts: %s" % (lineno, line))
		
		if ts < ts_prev:  # ts wrap
			
			sys.stderr.write( "fragment %d, line %d: %s ..." % (fragment_count, lineno, line[:-1]) )
			fragment_count += 1
			
			# split files
			fn = str(fragment_count) + "_" + filename
			copypart(filename, fn, fragment_start, fragment_end-fragment_start)
			fragment_start = fragment_end
			sys.stderr.write('ok \n')
			
		
		ts_prev = ts
		fragment_end += len(line)
	
	# the last fragment		
	fn = str(fragment_count) + "_" + filename
	copypart(filename, fn, fragment_start, fragment_end-fragment_start)
	
if __name__ == "__main__":
	main()
