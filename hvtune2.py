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
import logging

from time import sleep
from collections import Counter
from collections import defaultdict

# https://github.com/sergey-inform/SIS3316
import sis3316

# https://github.com/sergey-inform/panda-fsc-hvctl
from hvctl import HVUnit

OUTDIR = "./hvtune_out/"
hv_range = range(2500, 3001, 100)
threshold_range = range(50, 120, 20)

EVENT_SZ = 35
#~ hv_addr = ('localhost', 2217)
HV_ADDR = ('172.22.60.202', 2217)
#~ adc_addr = ('10.0.0.1', 3344)
ADC_ADDR = ('172.22.60.202', 2222)

HV_CHANS = { # channel to HV channel
    0:  0,
    1:  8,
    2:  6,
    3:  14,
    4:  1,
    5:  9,
    6:  34,
    7:  35,
    8:  18,
    9:  19,
    10: 20,
    11: 21,
    12: 26,
    13: 27,
    14: 28,
    15: 29,
    }

HV_DELAY = 12  # sec, delay to let HV Unit to turn on/off

# /////////////////////////////////////////////

get_mtime = lambda: int(round(time.time() * 1000))
logger=None

def log_errors(f):
    def wrapper(self, *args, **kvargs):
        try:
            ret = f(self, *args, **kvargs)
        except Exception as e:
            self.logger.error("{}: {}".format(self.name, e) )
            raise
        return ret
    return wrapper

#https://gist.github.com/n1ywb/2570004
def retries(max_tries, delay=1, backoff=2, exceptions=(Exception,), hook=None):
    """Function decorator implementing retrying logic.
    delay: Sleep this many seconds * backoff * try number after failure
    backoff: Multiply delay by this factor after each failure
    exceptions: A tuple of exception classes; default (Exception,)
    hook: A function with the signature myhook(tries_remaining, exception);
          default None
    The decorator will call the function up to max_tries times if it raises
    an exception.
    By default it catches instances of the Exception class and subclasses.
    This will recover after all but the most fatal errors. You may specify a
    custom tuple of exception classes with the 'exceptions' argument; the
    function will only be retried if it raises one of the specified
    exceptions.
    Additionally you may specify a hook function which will be called prior
    to retrying with the number of remaining tries and the exception instance;
    see given example. This is primarily intended to give the opportunity to
    log the failure. Hook is not called after failure if no retries remain.
    """
    def dec(func):
        def f2(*args, **kwargs):
            if max_tries < 0:
                raise ValueError
            mydelay = delay
            tries = range(1+max_tries)
            
            for tries_remaining in tries:
                try:
                   return func(*args, **kwargs)
                except exceptions as e:
                    if tries_remaining > 0:
                        if hook is not None:
                            hook(tries_remaining, e, mydelay)

                        sleep(mydelay)
                        mydelay = mydelay * backoff
                    else:
                        #~ raise
                        exit(1)
                else:
                    break
        return f2
    return dec


class HV(object):
    ALL_CHANNELS = HV_CHANS.keys()

    def __init__(self, *params):
        self.dev = HVUnit(*params)
        self.logger = logger  # global
        self.name = 'HV Unit'
        self.values = defaultdict(None)
        
    def wait(self):
        self.logger.debug("wait {} seconds...".format(HV_DELAY))
        sleep(HV_DELAY)
    
    @retries(0)
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
            self.logger.debug("turn HV off.")
            hv.off()
            self.wait()

    @log_errors
    def on(self):
        hv = self.dev
        hv_voltage = int(hv.v()['V'])
        if hv_voltage < 80:
            self.logger.debug("turn HV on.")
            hv.on()
            self.wait()
            
    @log_errors
    def reset(self):
        self.logger.debug("reset all HV channels.")
        self.dev.cmd('z')
    
    @log_errors
    def set(self, chan, value):
        hv_chan = HV_CHANS[chan]
        self.logger.debug("set HV chan {} to {}".format(hv_chan, value))
        self.dev.set(hv_chan, value)
        self.values[chan] = value
    
    def set_all(self, value, channels=ALL_CHANNELS):
        """ Set initial HV value and turn HV on. """
        if value > 4000 or value < 1:
            raise ValueError("Wrong value %d." % value)
        
        self.off()
        self.reset()
        for chan in channels:
            self.set(chan, value)
        self.on()
        
    def incr_all(self, increment, channels=ALL_CHANNELS):
        """ Update value without turning HV off. """
        if abs(increment) > 100:
            raise ValueError("Not so fast!")
        
        for chan in channels: 
            if chan not in self.values:
                self.logger.error("can't increment: channel {} is not set.".format(chan) )
                continue
        
            prev = self.values[chan]
            self.set(chan, prev + increment)


class ADC(object):
    def __init__(self, addr, *params):
        self.dev = sis3316.Sis3316_udp(addr, *params)
        self.logger = logger  # global
        self.name = "ADC Unit {}.".format(addr)
    
    @log_errors
    def connect(self):
        """ Connect and read some status values. """
        adc = self.dev
        adc.open()   # enable network access.
        adc.configure()  # set channel numbers and so on.
        adc_response = "ADC  id: %s, serial: %s, temp: %d°C" % (
                str(adc.id),
                hex(adc.serno),
                adc.temp,
                )
        
        return adc_response
    
    @retries(10)
    @log_errors
    def set_thresholds(self, value, channels=range(0,16)):
        for ch in channels:
            self.dev.chan[ch].trig.threshold = 0x8000000 + value
    
    @retries(1)
    @log_errors
    def get_thresholds(self, value, channels=range(0,16)):
        return [(self.dev.chan[ch].trig.threshold - 0x8000000) for ch in channels]
    
    @retries(10)
    @log_errors   
    def measure_rates(self, channels=range(0,16)):
        adc = self.dev
        ts_summ = 0
        
        ts_prev = get_mtime()
        adc.mem_toggle()  # flush ADC memory
        
        sleep(30)  # TODO: estimate confidence of the measurement

        ts = get_mtime()
        adc.mem_toggle()
        
        ts_diff = ts - ts_prev
        byte_counts = adc.poll_act(channels)
        rates = []
        
        for bc in byte_counts:
            rate = 1000.0 * bc / EVENT_SZ / ts_diff
            rates.append(round(rate,2))
        
        return dict(zip(channels,rates))
        

def main():
    global logger
    parser = argparse.ArgumentParser(description=__doc__,
            formatter_class=argparse.RawTextHelpFormatter)
    # --channels
    channels = range(0,6)
    
    args = parser.parse_args()
    #~ print args
    
    makedirs(OUTDIR)
    logger = setLogging(logfile=OUTDIR+'/log.log')

    hv = HV(*HV_ADDR)
    adc = ADC(*ADC_ADDR)
    
    logger.info( hv.connect())
    logger.info( adc.connect())
    
    data = defaultdict(list)  # { (chan, threshold): [(hv, rate), ...] }
    plots = {}  # { chan: plot }
    
    # Start test
    hv_prev = hv_range[0]
    hv.set_all(hv_prev, channels=channels)
    
    adc.set_thresholds(50) #DELME
    exit(0)
    
    for hv_ in hv_range:
        incr = hv_ - hv_prev
    
        if incr:
            hv.incr_all(incr, channels=channels)
        
        
        for th_ in threshold_range:
            adc.set_thresholds(th_)
            logger.info('set {} threshold {}'.format(hv_, th_))

            rates = adc.measure_rates(channels)
            
            if all( [r < 0.1 for r in rates.values()]):
                # move to next HV
                break
            
            for chan, rate in rates.items():
                print chan, th_, hv_, rate
                sys.stdout.flush()
                data[(chan, th_)].append((hv_, rate))
            
        hv_prev = hv_
        
    hv.off()


def setLogging(logfile=""):
    
    logger = logging.getLogger('hvtune')
    
    console_hdlr = logging.StreamHandler()
    console_formatter = logging.Formatter('%(message)s')
    console_hdlr.setFormatter(console_formatter)
    #~ console_hdlr.setLevel(logging.WARNING)  # only warnings are printed to console
    console_hdlr.setLevel(logging.DEBUG) 
    logger.addHandler(console_hdlr)

    if logfile:
        file_hdlr = logging.FileHandler(logfile)
        file_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        file_hdlr.setFormatter(file_formatter)
        #~ file_hdlr.setLevel(logging.INFO)
        file_hdlr.setLevel(logging.DEBUG)
        logger.addHandler(file_hdlr)
   
    logger.setLevel(logging.DEBUG)  # catch em all
    return logger

def makedirs(path):
    """ Create directories for `path` (like 'mkdir -p'). """
    if not path:
        return
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)

if __name__ == "__main__":
    main()
