#!/usr/bin/env python
"""
Plot the output of fit-coeff.py.

"""

import os
import sys
import numpy as np
from matplotlib import pyplot as plt

from collections import OrderedDict

file = open(sys.argv[1], 'rt')

data = OrderedDict()

for line in file:
    if line[0] == "#":
        continue
#    chan, val, dist, run, trig1, trig2 = line.split('\t')
    run, chan, dist, trig1, trig2, val, err = line.split()
     
    chan = int(chan)
    if chan not in data:
        data[chan] = {}   

    dist = float(dist)
    if dist not in data[chan]:
        data[chan][dist] = []

    data[chan][dist].append( float(val))

results = OrderedDict()

exit(0)


for chan, distval in data.items():
        results[chan] = {}

        for dist, values in distval.items():
 
            results[chan][dist] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'max': max(values),
                    'min': min(values),
                    'values': values,
            }
            
            #~ print chan, dist, results[chan][dist]

for chan, cresult in sorted(results.items()):
    plt.cla()
    keys = sorted(cresult.keys())
    x = keys
    y = [ cresult[k]['mean'] for k in keys ]
    data = [ np.array(cresult[k]['values']) for k in keys ]
    err = [cresult[k]['std'] for k in keys ]
    high = [ cresult[k]['max'] for k in keys ]
    low = [ cresult[k]['min'] for k in keys ]
        
    plt.errorbar(x, y, yerr = err, label = chan, fmt="s--")
    #boxdata = np.concaddtenate( data )
    #plt.boxplot(boxdata)

    plt.title("chan %s" % chan)
    plt.xlabel("distance from far end")
    #plt.legend(loc="upper left", bbox_to_anchor=(1,1))
    plt.grid()
    plt.show()
#    plt.savefig("{}.png".format(chan))
