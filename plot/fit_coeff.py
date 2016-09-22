#!/usr/bin/env python
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


CHAN_COL = 0
RUN_COL = 1
TRIG_COL = 2
MPL_COL = 3
STD_COL = 0
CHI2_COL = 1

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
            
    parser.add_argument('-t', '--table',
            action='store_true',
            help="print as a table"
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
            
        data[chan][run][trig] = mpl


    def nsort(dic):
        for key in sorted(dic, key=natural_keys):
            yield (key, dic[key])
    
    
    ## Calculate values
    values = {}
    for chan, cdata in nsort(data):
        for run, rdata in nsort(cdata):
            if len(rdata) < 2: 
                continue
            valA = float(rdata[trigs[0]])
            valB = float(rdata[trigs[1]])
            if valB != 0:
                val = 1.0 * valA / valB
            else:
                val = None
    
            if chan not in values:
                values[chan] = []
                
            values[chan].append((run, val))
    
    if not args.table:
        for chan, cvals in nsort(values):
            for run, val in cvals:
                if args.distance:
                    print "{} {} {} {:.4}".format( run, chan, args.distance, val)
                else:
                    print "{} {} {:.4}".format( run, chan, val)

    else:
        runs = set([ rvals[0] for cvals in values.values() for rvals in cvals])
        runs = [_ for _ in sorted(runs, key=natural_keys)]
        allruns = [_ for _ in sorted(allruns, key=natural_keys)]
       
        #~ print "runs:\t{}".format("\t".join(runs))
        print "ch\\run:\t{}".format("\t".join(allruns)) + "\tTrigA\tTrigB"
        
        for chan, cvals in nsort(values):
            sys.stdout.write("{}".format(chan))
            dvals = dict(cvals)
            
            #~ for run in runs:
            for run in allruns:
                if run in dvals:
                    sys.stdout.write( "\t{:.4}".format(dvals[run]))
                else:
                    sys.stdout.write( "\t-")
            
            sys.stdout.write("\t{}\t{}".format(*trigs))
            sys.stdout.write("\n")
                
                
    
 
if __name__ == "__main__":
    main()
