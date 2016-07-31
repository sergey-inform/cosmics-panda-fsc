#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Find optimal HV value for detector's PMTs in cosmics setup.
Read out SIS3316 ADC while changing HV value in specified range,
plot HV vs Rate and find a plato.
"""

import sys
import os
import argparse
import time


from time import sleep 

OUTDIR = "./hvtune_out/"
hv_range = range(2000, 3100, 100)
channels = range(0,6)

EVENT_SZ = 35
#~ hv_addr = ('localhost', 2217)
HV_ADDR = ('172.22.60.202', 2217)
#~ adc_addr = ('10.0.0.1', 3344)
ADC_ADDR = ('172.22.60.202', 2222)

HV_CHANS = { # channel to HV channel
	0:	0,
	1:	8,
	2:	6,
	3:	14,
	4:	1,
	5:	9,
	6:	34,
	7:	35,
	8:	18,
	9:	19,
	10:	20,
	11:	21,
	12:	26,
	13:	27,
	14:	28,
	15:	29,
	}

HV_DELAY = 12  # sec, delay to let HV Unit to turn on/off

# /////////////////////////////////////////////

get_mtime = lambda: int(round(time.time() * 1000))
logger=None

def log_errors(f):
    def wrapper(self, *args, **kvargs):
        try:
            ret = f(self, *args, **kvargs)
        Exception as e:
            logger.error("%s: %s" % map(str, (self.name, e)) )
            raise
        return ret
    return wrapper


class HV(object):
    ALL_CHANNELS = HV_CHANS.keys()

	def __init__(self, *params):
        self.dev = HVUnit(*params)
        self.name = 'HV Unit'
        self.values = defaultdict(None)
    
    @log_errors
    def connect(self):
        """ Try to get some data """
        hv_responce = self.dev.cmd('v')[:-1]  # trim \n
        return hv_responce
    
    @log_errors
	def off(self):
        hv = self.dev
        hv_voltage = int(hv.v()['V'])
        if hv_voltage > 1:
            hv.off()
            sleep(HV_DELAY)

    @log_errors
    def on(self):
        hv = self.dev
        hv_voltage = int(hv.v()['V'])
        if hv_voltage < 80:
            hv.on()
            sleep(HV_DELAY)
            
    @log_errors
    def reset(self):
        self.dev.cmd('z')
    
    @log_errors
    def set(self, chan, value):
        hv_chan = HV_CHANS[chan]
        self.dev.set(hvchan, value)
    
    def set_all(self, value, channels=ALL_CHANNELS):
        """ Set initial HV value and turn HV on. """
        if value > 4000 or value < 1:
            raise ValueError("Wrong value %d." % value)
        
        self.off()
        self.reset()
        for chan in channels:
            self.set(chan, value)
            self.values[chan] = value
        self.on()
        
    def incr_all(self, increment, channels=ALL_CHANNELS):
        """ Update value without turning HV off. """
        if abs(increment) > 100:
            raise ValueError("Not so fast!")
        
        for chan in channels:
            prev = self.values[chan]
            if prev is None:
                continue
            self.set(chan, prev + increment)
    

class ADC(object):
	def __init__(self,):
        
        #~ self.dev = 
        
    def set_threshold(self, value, channels=range(0,16)):
        pass
        
    def measure_rates(self, channels=range(0,16)):
        ts_summ = 0
        
        ts_prev = get_mtime()
        dev.mem_toggle()  # flush ADC memory
        
        sleep(5)  # TODO: estimate confidence of the measurement

        ts = get_mtime()
        dev.mem_toggle()

        byte_counts = poll_act(channels)
        ts_diff = ts - ts_prev
        rates = [ 1000.0 * byte_counts/EVENT_SZ/ts_diff for cnt in counts]

        return dict(zip(channels,rates))

def main():
    global logger
    parser = argparse.ArgumentParser(description=__doc__,
            formatter_class=argparse.RawTextHelpFormatter)
    # --channels

    args = parser.parse_args()
    #~ print args
    
    makedirs(OUTDIR)
    logger = setLogging(logfile=OUTDIR+'/log.log')

    hv = HV(*HV_ADDR)
    adc = ADC(*ADC_ADDR)
    
    hv.connect()
    adc.connect()
    
    #~ hv.prepare()
    #~ adc.prepare()
    
    data = {}  # { (chan, threshold): [(hv, rate), ...] }
    plots = {}  # { chan: plot }
    
    # Start test
    for hv_ in hv_range:
        hv.set_all(hv_)
        
        for th_val in threshold_range:
            adc.set_threshold(th_)
            rates = adc.measure_rates(channels)
            
            for chan, rate in rates.items():
                data[(chan, th_)].append((hv_, rate))
            
        
        print data
        # Update plots
        #~ for chan, plot in plots.items():
            #~ pass
            #saveplot    
                
    #~ hv.off()


def setLogging(logfile=""):
    
    logger = logging.getLogger('hvtune')
    
    console_hdlr = logging.StreamHandler()
    console_formatter = logging.Formatter('%(message)s')
    console_hdlr.setFormatter(console_formatter)
    #~ console_hdlr.setLevel(logging.WARNING)  # only warnings are printed to console
    console_hdlr.setLevel(logging.INFO) 
    logger.addHandler(console_hdlr)

    if logfile:
        file_hdlr = logging.FileHandler(logfile)
        file_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        file_hdlr.setFormatter(file_formatter)
        file_hdlr.setLevel(logging.INFO)
        logger.addHandler(file_hdlr)
   
    logger.setLevel(logging.DEBUG)  # catch em all
    return logger


if __name__ == "__main__":
    main()
