#!/usr/bin/env python

# Set HV on HVCTL Unit
# (values are given via stdin)

import sys
from time import sleep

def prerr(*args, **kvargs):
	sys.stderr.write(*args,**kvargs)

HV_HOST = 'localhost'
HV_PORT = 2217
HV_ONOFF_DELAY = 15  # sec

chans = {  # chan, hv_chan
        0:0,
        1:8,
        2:6,
        3:14,
        4:1,
        5:9,
        6:34,
        7:35,
        8:18,
        9:19,
        10:20,
        11:21,
        12:26,
        13:27,
        14:28,
        15:29,
        }


prerr("waiting lines in stdin...\n")
values = []

# Read values
for line in sys.stdin:
	chan, val = map(int, line.split()[0:2])
	if chan < 0 or chan > 15:
		prerr("channel is integer [0..15], but %d given\n" % chan)
		exit(1)
	if val < 0 or val > 4000:
		prerr("value is integer [0..4000], but %d given\n" % val)
		exit(1)
		
	values.append( (chan, val))

prerr("got %d lines \n" % len(values))

# Set values
from hvctl import HVUnit
hv = HVUnit(host = HV_HOST, port = HV_PORT)

prerr("turning HV off (wait %d seconds)...\n" % HV_ONOFF_DELAY)
hv.off()
sleep(HV_ONOFF_DELAY)
resp = hv.cmd('v')
prerr(resp)

prerr("reset HV ('z' command)\n")
hv.cmd('z')

for chan, val in values:
	hv_chan = chans[chan]
	prerr("set HV code %d for ADC channel %d (hv chan: %d)...\n" % (val, chan, hv_chan))
	hv.set(hv_chan, val)

prerr("turning HV on (wait %d seconds)...\n" % HV_ONOFF_DELAY)
hv.on()
sleep(HV_ONOFF_DELAY)
resp = hv.cmd('v')
prerr(resp)
