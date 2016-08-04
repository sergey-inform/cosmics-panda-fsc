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
from collections import Counter
from collections import defaultdict

from util import makedirs
from util import setlog#, log_errors
from util import retry

# https://github.com/sergey-inform/SIS3316
import sis3316

# https://github.com/sergey-inform/panda-fsc-hvctl
from hvctl import HVUnit

OUTDIR = "./hvtune_out/"
hv_range = range(2200, 3001, 100)
threshold_range = range(50, 101, 10)

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

# /////////////////////////////////////////////

get_mtime = lambda: int(round(time.time() * 1000))
logger=None  # will be instantiated by setlog() 


def err_exit(f):
    """ Just log the error and exit. """
    def wrapper(self, *args, **kvargs):
        global logger
        try:
            ret = f(self, *args, **kvargs)
        except Exception as e:
            logger.error("{}: {}".format(self.name, e) )
            exit(e.errno)
        return ret
    return wrapper


def myretry(*args, **kvargs):
    """ Log error and how many retries is remaining. """
    def log_retries(tries_remaining, exception, delay):
        global logger
        logger.warn('{}; retry {} more times, next in {} sec.'\
            .format(
                str(exception),
                tries_remaining,
                delay
            )
        )
    kvargs['hook']=log_retries
    return retry(*args, **kvargs)


class HV(object):
    """A wrapper object for HV setup implementation.
    """
    HV_DELAY = 15  # a delay to let HV Unit to turn on/off, seconds.
    MAX_STEP = 100 # do not allow to change HV at this step without turning HV off
    ALL_CHANNELS = HV_CHANS.keys()
    name = 'HV Unit'
    
    @err_exit
    def __init__(self, *params):
        global logger
        self.dev = HVUnit(*params)
        self.logger = logger
        self.memory = dict()

    def connect(self):
        """ Check the unit is responding. """
        hv_responce = self.dev.cmd('v')[:-1]  # trim \n
        return hv_responce

    # Interface
    @myretry(10)
    def is_on(self):
        hv = self.dev
        hv_voltage = int(hv.v()['V'])
        if hv_voltage > 1:
            return True
    
    @myretry(10)
    def off(self):
        hv = self.dev
        if self.is_on():
            self.logger.debug("turn HV off.")
            hv.off()
            self.wait()

    @myretry(10)
    def on(self):
        hv = self.dev
        if not self.is_on():
            self.logger.debug("turn HV on.")
            hv.on()
            self.wait()

    @myretry(10)
    def reset(self):
        self.logger.debug("reset all HV channels.")
        self.dev.cmd('z')

    @myretry(10)
    def set(self, chan, value):
        hv_chan = HV_CHANS[chan]
        self.logger.debug("set HV chan {} to {}".format(hv_chan, value))
        self.dev.set(hv_chan, value)
        self.memory[chan] = value

    def wait(self):
        delay = self.HV_DELAY
        self.logger.debug("wait {} seconds...".format(delay))
        sleep(delay)

    # Procedures
    def set_all(self, value, channels=ALL_CHANNELS):
        """ Set HV values in a smart way: without turning HV off 
        if value changes not too harsh.
        """
        memo = self.memory
        if value > 4000 or value < 1:
            raise ValueError("Wrong value %d." % value)
        
        # If at least one channel was not set previously (not in memory)
        # then turn HV off before seting the values.

        if any((chan not in memo for chan in channels)):
            self.off()
            self.reset()

        # If at least for one channel the value changes more than MAX_STEP,
        # then turn HV off before seting the values.
        # (to not to change HV value harshly).

        for chan in channels:
            if chan in memo and abs(memo[chan] - value) > self.MAX_STEP:
                self.off()
                self.reset()
                break
        
        # Restore memorized values
        for chan, memorized in memo.items():
            if chan not in channels:  # no new value for this channel
                self.set(chan, memorized)
        
        # Set the new values
        for chan in channels:
            self.set(chan, value)
        
        self.on()
        


class ADC(object):
    """A wrapper object for ADC readout.
    """
    name = "ADC Unit"
    ALL_CHANNELS = range(0,16)
    
    def __init__(self, addr, *params):
        self.dev = sis3316.Sis3316_udp(addr, *params)
        self.logger = logger  # global
        self.name = "ADC Unit {}.".format(addr)
    
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
    
    @myretry(10)
    def set_thresholds(self, value, channels=ALL_CHANNELS):
        for ch in channels:
            self.dev.chan[ch].trig.threshold = 0x8000000 + value
    
    @myretry(10)
    def get_thresholds(self, value, channels=ALL_CHANNELS):
        return [(self.dev.chan[ch].trig.threshold - 0x8000000) for ch in channels]
    
    @myretry(10)
    def measure_rates(self, channels=ALL_CHANNELS):
        adc = self.dev
        ts_summ = 0
        
        ts_prev = get_mtime()
        adc.mem_toggle()  # flush ADC memory
        
        sleep(300)  # TODO: estimate confidence of the measurement

        ts = get_mtime()
        ts_diff = ts - ts_prev
        byte_counts = adc.poll_act(channels)
        rates = []
        
        for bc in byte_counts:
            rate = 1000.0 * bc / EVENT_SZ / ts_diff
            rates.append(round(rate,3))
        
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
    logger = setlog('hvtune', logfile=OUTDIR+'/log.log', console_lvl='DEBUG')

    hv = HV(*HV_ADDR)
    adc = ADC(*ADC_ADDR)
    
    logger.info( hv.connect())
    logger.info( adc.connect())
    
    data = defaultdict(list)  # { (chan, threshold): [(hv, rate), ...] }
    plots = {}  # { chan: plot }
    
    for hv_ in hv_range:
        hv.set_all(hv_, channels=channels)
        
        for th_ in threshold_range:
            adc.set_thresholds(th_)
            logger.info('set {} threshold {}'.format(hv_, th_))
            logger.info(hv.connect())  # log HV status

            rates = adc.measure_rates(channels)
            
            if all( [r < 0.1 for r in rates.values()]):
                # move to next HV
                break
            
            for chan, rate in rates.items():
                print chan, th_, hv_, rate
                sys.stdout.flush()
                data[(chan, th_)].append((hv_, rate))
        
    hv.off()


if __name__ == "__main__":
    main()
