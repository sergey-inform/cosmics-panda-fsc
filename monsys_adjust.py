#!/usr/bin/env python
"""
Adjust values according to monitoring system data.

"""

import sys
import numpy as np

MFILE_TS_COL = 0
MFILE_CHAN_COL = 1
MFILE_VAL_COL = 2

MBACKLOG = 100

DFILE_TS_COL = 0
DFILE_CHAN_COL = 1
DFILE_VAL_COL = 2


def get_mondata(fd):
    """ Generator. Next data from mfile.
    """
    data = {}
    ts_prev = None

    for line in fd:
        vals = line.split()
        ts = float(vals[MFILE_TS_COL])
        chan = vals[MFILE_CHAN_COL]
        val = float(vals[MFILE_VAL_COL])

        if ts_prev is not None and ts != ts_prev:
            yield ts, data
            data = {}

        data[chan] = val
        ts_prev = ts


def avg_mondata(fd):
    """ Generator. Moving average for mondata.
        Average MBACKLOG values.
    """
    md = get_mondata(fd)
    
    data = {}
    for ts, mdata in md:
        for chan, val in mdata.items():
            try:
                data[chan].append(val)
            except KeyError:
                data[chan] = []
                data[chan].append(val)

            if len(data[chan]) > MBACKLOG:
                data[chan].pop(0)

        yield ts, dict( [ (chan, sum(vals)/len(vals)) for chan, vals in data.items()])

dfile = open(sys.argv[1], 'ro')
mfile = open(sys.argv[2], 'ro')

md = get_mondata(mfile)


mts, mdata = next(md)

mdata0 = mdata

for line in dfile:
    vals = line.split()
    ts = float(vals[DFILE_TS_COL])
    chan = vals[DFILE_CHAN_COL]
    val = float(vals[DFILE_VAL_COL])
    
    while ts > mts:
        mts, mdata = next(md)

#    print "TS {:.0f} {:.0f} {:.0f}".format(ts, mts, mts-ts)

    if chan in mdata and chan in mdata0:
        adjval = val * mdata[chan]/mdata0[chan]
        print '{:.0f} {} {:.2f} {:.2f}'.format(ts, chan, adjval, val)
