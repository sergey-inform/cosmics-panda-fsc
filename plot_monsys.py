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
COL_VAL_IDX = 2
COL_STD_IDX = 4

# -----------------------------------------

if len(sys.argv) != 2:
    sys.stderr.write("USAGE: %s <fitres.log>\n" % sys.argv[0])
    exit(1)

filename = sys.argv[1]
if not os.path.isfile(filename):
    sys.stderr.write("No such file: '%s'\n" % filename)
    exit(1)

x, y, err = np.loadtxt(filename, usecols=(COL_TS_IDX, COL_VAL_IDX, COL_STD_IDX), unpack = True )

ts = [dt.datetime.utcfromtimestamp(_) for _ in x]

fig, ax = plt.subplots()

ax.errorbar(ts,y,err)

ymin, ymax = y[0] * 0.99, y[0] * 1.01
#~ ax.set_ylim([ymin,ymax])

plt.axhline(ymin, color='red')
plt.axhline(ymax, color='red')


#~ ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H'))
ax.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0,24,6)))

#~ fig.autofmt_xdate()

plt.xlabel('Hours')
plt.ylabel('Integral peak value')
ax.grid()
plt.show()


TODO: plot many
