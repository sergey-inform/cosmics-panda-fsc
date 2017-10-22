#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Average datapoints.
"""

import sys
import os
import numpy as np


# ------------ Parameters -----------------

COL_TS_IDX = 0  # which column contains timestamps, starting from 0
COL_CHAN_IDX = 1
COL_VAL_IDX = 2
COL_STD_IDX = 3

DATAPOINTS = 5000

# -----------------------------------------

if len(sys.argv) != 2:
    sys.stderr.write("USAGE: %s <data.txt>\n" % sys.argv[0])
    exit(1)

filename = sys.argv[1]
if not os.path.isfile(filename):
    sys.stderr.write("No such file: '%s'\n" % filename)
    exit(1)
    
dtype = np.dtype({
        'names': ['ts', 'chan', 'val', 'std'],
        'formats' : ['float', 'int', 'f','f'],
        })

usecols = (COL_TS_IDX, COL_CHAN_IDX, COL_VAL_IDX, COL_STD_IDX)
loaded = np.loadtxt(filename, dtype = dtype, usecols=usecols)

chans =  np.unique(loaded['chan'])

chunklen = len(loaded)/ len(chans) / DATAPOINTS  # assume same amount of data in all channels


data = dict( (c, []) for c in chans)
stddata = dict( (c, []) for c in chans)

for x in loaded:    
    ts, chan, val, std = x['ts'], x['chan'],x['val'], x['std']
    data[chan].append(val)
    stddata[chan].append(std)

    if len(data[chan]) >= chunklen:
        print '{:.0f} {} {:.2f} {:.2f}'.format(ts, chan, np.average(data[chan]), np.average(stddata[chan]))
        data[chan] = []
        stddata[chan] = []
