#!/usr/bin/env python

import sys
import numpy as np

filename = sys.argv[1]

if filename != "-":
	fd = open(filename,'ro')
else:
	fd = sys.stdin

TS_COL, CHAN_COL, VAL_COL = 0, 1, 2

HZ = 250*1000*1000  # ts = time * HZ
TS_GAP = 1 * HZ  # sec. (minimal gap between series of pulses)
THRESHOLD = 800

data = {}

def print_data(ts, data):
    tssec = ts/HZ

    #if len(data) < 6: 
    #    return 

    for chan, values in data.items():

        if len(values) > 150 or len(values) < 50:
            continue
        arr = np.array(values)
        range_ = np.percentile(arr, [10 ,90])
        rarr = arr[(arr> range_[0]) & (arr<range_[1])]

       
        if len(rarr):
            #print '{:.0f} {} {:.2f} {:.3f} {}'.format(ts, chan, np.average(rarr), np.std(rarr), len(rarr))
            print '{:.0f} {} {:.2f} {:.3f} {}'.format(ts, chan, np.average(rarr), np.std(rarr), len(rarr))


ts_prev = None

for line in fd:
    
    values = line.split()

    try:
        ts = int(values[TS_COL])
        chan = values[CHAN_COL]
        val = float(values[VAL_COL])
    except:
        continue



    if val < THRESHOLD:
        continue

    try:
        data[chan].append(val)
    except KeyError:
        data[chan] = []
        data[chan].append(val)

    if ts_prev and ts - ts_prev > TS_GAP:
        # a new series of pulses 
		#print 'PRDATA', ts, data.keys()
        print_data(ts, data)
        data = {}

    ts_prev = ts

