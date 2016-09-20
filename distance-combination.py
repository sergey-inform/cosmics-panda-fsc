#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility to calculate distance for each combination of triggers.

infiles:
	distances.txt
	combinations.txt

output:
	For each run in 'distances.txt' calculate the distance
	between trigger points, specified in 'combinations.txt'
"""
import sys
import os


cfile = open('combinations.txt', 'ro')
dfile = open('distances.txt', 'ro')

DELIM = '\t'
MISSING = '-'

# the first line in 'distances.txt' is a header with the names of points.

points = next(dfile)[:-1].upper().split(DELIM)[1:]
print 'POINTS:', points

clines = [line for line in cfile]

for dline in dfile:
	dline = dline[:-1]  # strip \n
	dsplit = dline.split(DELIM)
	
	run = dsplit[0]

	values = [float(v) if v != MISSING else None for v in dsplit[1:] ]

	if len(points) != len(values):
		sys.stdout.write("wrong number of values"
			" in line: {}\n".format(line))
		exit(1)
	
	points_values = dict(zip(points, values))
	
	for cline in clines:
		cline = cline[:-1]  # strip \n
		cline = '\t'.join(cline.split())  #replace spaces with tabs if any

		A, B = cline.split(DELIM)
		
		tA, tB = A.upper(), B.upper()

		if tA[0] == tB[0]:  # the same first letter
			vA = points_values[tA[1]]
			vB = points_values[tB[1]]

		elif tA[1] == tB[1]:
			vA = points_values[tA[0]]
			vB = points_values[tB[0]]
		
		else:
			sys.stderr.write("combination {} {}"
				" seems to be wrong".format(tA, tB))
			exit(1)

		if vA is None or vB is None:
			continue

		distance = abs(vA - vB)

		print run, A, B, distance
