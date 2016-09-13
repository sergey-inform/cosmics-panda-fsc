#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Find the most probable values for given dataset
using Kernel Density Estimation technique:
http://www.mvstat.net/tduong/research/seminars/seminar-2001-05/

If several maximums found, print them all.
"""

import sys
import os
import numpy as np
from matplotlib import pyplot as plt
from scipy.stats import gaussian_kde
from scipy.signal import argrelmax
from scipy.optimize import fmin
from util import natural_keys

VALUE_COLUMN = 2  # a column number with the value 
CHANNEL_COLUMN = 1  # a column number for channel, None if not the case


def common_start(*strings):
    """ Returns the longest common substring
        from the beginning of the `strings`
    """
    def _iter():
        for z in zip(*strings):
            if z.count(z[0]) == len(z):  # check all elements in `z` are the same
                yield z[0]
            else:
                return

    return ''.join(_iter())


def parse_values(fileobjects, channels=set()):
	""" Parse datafile.
	Return a dict of ditcts of lists: {chanel: { filename : [values]} }.
	"""
	data = {}

	for fileobj in fileobjects:
		filename = fileobj.name

		filedata = {}
		for line in fileobj: 
			line = '\t'.join(line.split())  # join consecutive spaces
			sline = line.split('\t')
			value = float(sline[VALUE_COLUMN])
			chan = sline[CHANNEL_COLUMN] if CHANNEL_COLUMN is not None else None
			
			try:
				filedata[chan].append(value)
			except KeyError:
				filedata[chan] = []
				filedata[chan].append(value)
			
		for chan, values in filedata.items():
			if channels and chan not in channels:
				pass

			if chan not in data:
				data[chan] = {}
			data[chan][filename] = np.array(values)
	
	return data

def fit_cosmics(title, cdata):
	"""

	"""
	
	hist_scale = 2

	fig, ax = plt.subplots()

	common_name = os.path.commonprefix(cdata.keys())
	dir_len  = len(os.path.dirname(common_name))
	common_len = max(dir_len, common_name.find('_',dir_len))
	common_name = common_name[:common_len+1]

	for name, data in sorted(cdata.items()):
		label = name[len(common_name):]
		label = os.path.splitext(label)[0]
		median = np.median(data)
		
		hist_range = (0, median * hist_scale)
		hist_bins = 50 * hist_scale  # binsize is 1% of the median 
		vals, bins, patches = plt.hist(
			data,
			bins = hist_bins,
			range = hist_range,
			histtype = 'step',
			normed = True,
			label = label,  # strip common part
		)
			
		color = patches[0].get_edgecolor()

		#get kde parameter	
		data_thresh = data[data < hist_range[1]]
		
		kde = gaussian_kde(data_thresh)
		kde_vals = kde(bins)
		maxima_idx = argrelmax(kde_vals)[0]
		maxima_x = [bins[i] for i in maxima_idx]
		
		def minfunc(x, *args):
			return -kde(x)[0]

		# impove_results
		maxima_x_optim = []
		
		for x0 in maxima_x:
			maxima_x_optim.extend(fmin(minfunc,x0,disp=False))

		print '{} {} {:.2f}'.format(title, label, maxima_x_optim[1])

		plt.plot(bins, kde_vals, '-', color= color)

	fig.canvas.set_window_title(common_name)
	plt.title(title)
	plt.legend()
	plt.grid()
	plt.show()

def nsort(dic):
	for key in sorted(dic, key=natural_keys):
		yield (key, dic[key])

def main():
	filenames = sys.argv[1:]
	infiles = [open(fn, 'ro') for fn in filenames]
	data = parse_values(infiles)

	for chan, cdata in nsort(data):
		title = 'chan {}'.format(chan)
		fit_cosmics(title, cdata)

if __name__ == "__main__":
	main()

# try out scipy kde first
# Randomly generate some langauss data, compare found peak with the true maximum.
# choose bandwidth https://github.com/Daniel-B-Smith/KDE-for-SciPy/blob/master/kde.py
