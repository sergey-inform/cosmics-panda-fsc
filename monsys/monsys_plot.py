#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Plot monitoring system data.
"""

import sys
import os
import numpy as np
import datetime as dt

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# ------------ Parameters -----------------

COL_TS_IDX = 0  # which column contains timestamps, starting from 0
COL_CHAN_IDX = 1
COL_VAL_IDX = 2
COL_STD_IDX = 3

HZ = 250 * 1000*1000
# -----------------------------------------

if len(sys.argv) != 2:
    sys.stderr.write("USAGE: %s <fitres.log>\n" % sys.argv[0])
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
#converters = {0: datestr2num}
#

chans =  np.unique(loaded['chan'])
print 'Chans: {}'.format(chans)

fig, ax = plt.subplots()

for chan in chans:
    data = loaded[loaded['chan'] == chan]
    val_normed =  data['val'] / data['val'][0]
    std_normed =  data['std'] / data['val'][0]
    ts = data['ts']
    if ts[-1] > 1500000000:
        ts = ts/HZ
    #~ ts = data['ts'] - data['ts'].min(axis=0)
    #~ ts = ts/3600  # sec -> hrs
    dtts = [dt.datetime.utcfromtimestamp(_) for _ in ts]
    #ax.errorbar(dtts, val_normed, std_normed, label=str(chan))
    ax.plot(dtts,val_normed, label=str(chan))
    #ax.errorbar(dtts, data['val'], data['std'], label=chan)

ax.xaxis_date()
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H'))
ax.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0,24,2)))

fig.autofmt_xdate()

#~ start, end = ax.get_xlim()
#~ stepsize = 4
#~ ax.xaxis.set_ticks(np.arange(start, end, stepsize))

#yticks = ax.get_yticks()
#ax.set_yticklabels(['{:3.3f}%'.format(_*100) for _ in yticks])

plt.xlabel('Hours')
plt.ylabel('Baseline value (normalized)')
ax.grid()
ax.legend(loc="upper left", bbox_to_anchor=(1,1))
plt.show()


