#!/usr/bin/env python
""" Count events per hour for each channel in a sorted list of records.
    input columns: <timestamp> <chan> ...
    output columns: "<hour> <eph> ... <ephN>"
"""

import sys, os
import argparse
from collections import Counter

HZ = 250 * 1000 * 1000 # timestamp = HZ * seconds

def main():
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='(c) Sergey Ryzhikov <sergey.ryzhikov@ihep.ru>, 2016.\nLicense: GPLv2')
    
    
    parser.add_argument( 'infile',
            type=argparse.FileType('r'),
            default=sys.stdin,
            help='data file (stdin by default)')
    
    args = parser.parse_args()
    
    next_ts = None
    ts_increment = HZ * 60
    count = Counter()
    hr = 0
    lineno = 0
    channels = set()
    
    for line in args.infile:
        
        lineno +=1

        if line[0] == '#':
            continue  # skip comments

        line = '\t'.join(line.split())
        ts, chan, rest = line[:-1].split('\t', 2)  #stip '\n' without making a copy of the string
        ts = float(ts)
        chan = int(chan)
        
        count[chan] += 1

        if next_ts is None:
            next_ts = ts + ts_increment

        elif ts > next_ts:
            # it's time to print something
            hr += 1
            next_ts = ts + ts_increment
            
            newchannels = set(count.keys())
            
            if newchannels != channels:
                if newchannels.issubset(channels):
                    pass
                
                else:
                    #some channels had been added
                    channels.update(newchannels)

                    strchans = "\t".join(map(str, sorted(channels)))
                    print( "#hr\ch\t{}\tlineno".format(strchans))
            
            #print the data
            values = [count[c] for c in sorted(channels)]
            print('%d\t%s\t%d' % (hr, '\t'.join( map(str, values) ), lineno ) ) 
            
            count = Counter()

    
if __name__ == "__main__":
    main()
