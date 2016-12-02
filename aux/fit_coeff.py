#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Read analysis results.
    Calculate coefficients for each channel:
        for each channel and each run divide MPL for trigger A by MPL for trigger B (if any).

    Input data fields:
        channel_name run_name trigger_name MPL Chi2 NDF

    Author: Sergey Ryzhikov (sergey-inform@ya.ru), 2016
    License: GPLv2
"""
import sys
import os

import argparse
from util import natural_keys

RUN_COL = 0
CHAN_COL = 2
TRIG_COL = 3
MPL_COL = 5
ERR_COL = 6
STD_COL = 14
CHI2_COL = 8

def main():
    parser = argparse.ArgumentParser(description=__doc__,
            formatter_class=argparse.RawTextHelpFormatter)
    
    parser.add_argument( 'infile',
            type=argparse.FileType('r'),
            default=[sys.stdin],
            help='the file with results of fitting'
            )

    parser.add_argument('A',
            type=str, 
            help='trigger A'
            )
            
    parser.add_argument('B',
            type=str, 
            help='trigger B'
            )
            
    parser.add_argument('-d', '--distance',
            type=str,
            help="print distance"
            )

    args = parser.parse_args()
    
    
    ## Readout data
    data = {}
    line_count = 0
    trigs = args.A, args.B
    allruns = set()
    
    for line in args.infile:
        line_count += 1
        
        if line[0] == "#":
            #skip comments
            continue
        
        line = '\t'.join(line.split())  # replace spaces with tabs
        try:
            sline = line.split('\t')
            chan = sline[CHAN_COL]
            run = sline[RUN_COL]
	    
	    trig = sline[TRIG_COL]
            mpl = sline[MPL_COL]
            err = sline[ERR_COL]
            err = err.translate(None,'±')

            std = sline[STD_COL]
            chi2_ndf = sline[CHI2_COL]

        except IndexError as e:
            sys.stderr.write("{} \n".format(sline))
            sys.stderr.write("Wrong line #{}: {}\n".format(line_count, str(e)))
            exit(1)
        
        allruns.add(run)
       
        if trig not in trigs:
            continue
            
        if chan not in data:
            data[chan] = {}
        
        if run not in data[chan]:
            data[chan][run] = {}
            
        data[chan][run][trig] = (mpl,err)


    def nsort(dic):
        for key in sorted(dic, key=natural_keys):
            yield (key, dic[key])
    
    
    ## Calculate values
    values = {}
    for chan, cdata in nsort(data):
        for run, rdata in nsort(cdata):
            if len(rdata) < 2: 
                continue
            valA, errA = map(float, rdata[trigs[0]])
            valB, errB  = map(float, rdata[trigs[1]])
            
            if valB != 0:
                val = 1.0 * valA / valB
                err = val - (valA + errA)/(valB - errB)
            else:
                val = None
                err = None
    
            if chan not in values:
                values[chan] = []
                
            values[chan].append((run, (val, err) , trigs[0], trigs[1]))
    
    for chan, cvals in nsort(values):
        for run, (val,err), trig0, trig1 in cvals:
            if args.distance:
                print "{} {} {} {} {} {:.4} ±{:.2}".format( run, chan, args.distance, trig0, trig1, val, abs(err))
            else:
                print "{} {} {} {} {:.4} ±{:.2}".format( run, chan, trig0, trig1,  val, abs(err))

if __name__ == "__main__":
    main()
