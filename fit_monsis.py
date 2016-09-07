#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fit monitoring system data, find peak value.
(fits around the maximum)
"""

import sys
import os
import numpy as np
from scipy.optimize import curve_fit

# ------------ Parameters -----------------

THRESHOLD = 30 * 1000  # filter values less than threshold
COL_IDX = 2  # which column contains values, starting from 0
NBINS = 100  # a number of bins for the histogram

# -----------------------------------------

if len(sys.argv) != 2:
    sys.stderr.write("USAGE: %s <datafile.txt>\n" % sys.argv[0])
    exit(1)

filename = sys.argv[1]
if not os.path.isfile(filename):
    sys.stderr.write("No such file: '%s'\n" % filename)
    exit(1)
    
loaded = np.loadtxt(filename, usecols=(COL_IDX,) )
data = loaded[loaded>THRESHOLD]  # filter data

#~ print 'N:', len(data), 'FILTERED:', len(loaded) - len(data)
#~ del loaded  # free some memory

hist, bin_edges = np.histogram(data, bins=NBINS)
bin_centres = (bin_edges[:-1] + bin_edges[1:])/2
bin_cnt = len(bin_centres)
max_y = max(hist)
max_index = hist.argmax()
max_x = bin_centres[max_index]

#~ print 'max_x', max_x

# Filter the histogram 
bin_width = bin_cnt - max_index
bin_left = max_index - bin_width/6
hist2 = hist[bin_left: bin_cnt]
bin_centres2 = bin_centres[bin_left: bin_cnt]
bin_edges2 = bin_edges[bin_left: bin_cnt]

def gauss(x, *p):
    A, mu, sigma = p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))
    
# p0 is the initial guess for the fitting coefficients (A, mu and sigma above)
p0 = [max_y, max_x, 100.]

# Fit the histogram
coeff, var_matrix = curve_fit(gauss, bin_centres2, hist2, p0=p0)
var_error = np.sqrt(np.diag(var_matrix))

result = zip(coeff, var_error)
#~ print result
mpl, mpl_std = result[1]
mpl_str = u"{:.2f} ± {:.2f}".format(*result[1])
sigma_str = u"{:.2f} ± {:.2f}".format(*result[2])

print(u"{}\t{}\t{}".format(filename, mpl_str, sigma_str))

#: Uncomment to plot the histogram and the fit
import matplotlib.pyplot as plt
hist_fit = gauss(bin_centres2, *coeff)
plt.step(bin_centres, hist, where='mid', label='Data')
plt.plot(bin_centres2, hist_fit, label="Fit")
plt.axvline(mpl+mpl_std, color='red', label=u"Peak: %s" % mpl_str)

plt.axvline(mpl-mpl_std, color='red')
plt.title(filename)
plt.legend(loc='upper left')
plt.grid()
plt.show()
