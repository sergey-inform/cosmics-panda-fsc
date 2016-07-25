#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Find optimal HV value for detector's PMTs in cosmics setup.
Read out SIS3316 ADC while changing HV value in specified range,
plot HV vs Rate and find a plato.
"""

import sys,os
import argparse
from datetime import datetime
from time import sleep 
import logging


# https://github.com/sergey-inform/SIS3316
import sis3316

# https://github.com/sergey-inform/panda-fsc-hvctl
from hvctl import HVUnit


# //////////  SETUP  ////////////////////
EVENT_SZ = 35  # bytes per event
OUTDIR = "./hvtune_out/"
hv_range = range(2000, 3100, 100)
channels = range(0,6    )

#~ hv_addr = ('localhost', 2217)
hv_addr = ('172.22.60.202', 2217)
#~ adc_addr = ('10.0.0.1', 3344)
adc_addr = ('172.22.60.202', 2222)

chunksize = 1024*1024  # how many bytes to request at once

hvchans = { # channel to HV channel
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
    
# ///////////////////////////////////////


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
    
    
def main():
    parser = argparse.ArgumentParser(description=__doc__,
            formatter_class=argparse.RawTextHelpFormatter)
    # --channels

    args = parser.parse_args()
    #~ print args
    
    makedirs(OUTDIR)
    logger = setLogging(logfile=OUTDIR+'/log.log')

    #
    # Connect to HV Unit
    try:
        hv = HVUnit(*hv_addr)
        hv_responce = hv.cmd('v')[:-1]  # trim \n
    except Exception as e:
        logger.error("HV Unit:" + str(e))
        exit(1)
    
    logger.info(hv_responce)
    
    #
    # Connect to ADC Unit
    try:
        adc = sis3316.Sis3316_udp(*adc_addr)
        adc.open()   # enable network access.
        adc.configure()  # set channel numbers and so on.
        adc_response = "ADC  id: %s, serial: %s, temp: %d°C" % (
                str(adc.id),
                hex(adc.serno),
                adc.temp,
                )
    except Exception as e:
        logger.error("ADC Unit:" + str(e))
        exit(1)
    
    logger.info(adc_response)
    
    hv_delay = 12  # sec
 
    #
    # Turn off HV
    #~ hv_voltage = int(hv.v()['V'])
    #~ if hv_voltage > 1:
        #~ logger.info("Turn off HV (wait %d sec)..." % hv_delay)
        #~ hv.off()
        #~ sleep(hv_delay)
    
    #
    # Set initial HV values and turn ON:
    #~ hv_initial = hv_range[0]
    #~ logger.info("Begin HV-Tune.")
    #~ logger.info("For selected channels set HV codes to %d..." % hv_initial)
    #~ hv.cmd('z')  # set all HV channels to 0
    #~ for chan in channels:
        #~ hvchan = hvchans[chan]
        #~ hv.set(hvchan, hv_initial)
        #~ logger.info("chan %d (hvchan %d) set to %d" % (chan, hvchan, hv_initial))
    #~ 
    #~ logger.warn("HV On (waig %d sec)..." % hv_delay)
    #~ hv.on()
    #~ sleep(hv_delay) 
    
    #
    # Begin
    
    sink = open('/dev/null', 'wb')
    
    for hv_value in hv_range:
        
        # Set new HV code
        for chan in channels:
            hv.set(hvchans[chan], hv_value)
      
        logger.warn("hv %d set" % hv_value)
        adc.mem_toggle()  # flush the device memory
        
        # Perform readout
        counts = dict( [(ch, 0) for ch in channels])
        
        opts = {'chunk_size': chunksize/4 }
       
        while True:
            sleep(1) # wait 1 sec
            adc.mem_toggle() 
            
            try:
                counts = readout()
            except Exception as e:
                
                continue
                    
                    
                counts[chan] += bytes_ / EVENT_SZ
                
            print 'counts', counts
            break
            
            # TODO: running sum, median, std...
        
        
        # Replot graphs
    
def adc_readout(channels)
    """ Generator.
        Yields counts.
    """
     for chan in channels:
                bytes_ = 0
                try:
                    for ret in adc.readout_pipe(chan, sink, 0, opts ):  # per chunk
                       bytes_ += ret['transfered'] * 4  # words -> bytes
                except Exception as e:
                    # ignore readout errors
                    logger.error(e)
    
def makedirs(path):
	""" Create directories for `path` (like 'mkdir -p'). """
	if not path:
		return
	folder = os.path.dirname(path)
	if folder and not os.path.exists(folder):
	    os.makedirs(folder)

if __name__ == "__main__":
    main()
