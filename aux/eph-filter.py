#!/usr/bin/env python
""" 
    Calculate typical event rates for channels.
    Find intervals of time with extraordinary high event rates, 
    purge them from data flow and print some statistics to stderr.
    
    input columns: <timestamp> <chan> ...
"""

import sys, os
import argparse
from collections import Counter, defaultdict

HZ = 250 * 1000 * 1000 # timestamp = HZ * seconds


def parse_args():
 
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='(c) Sergey Ryzhikov <sergey.ryzhikov@ihep.ru>, 2016.\nLicense: GPLv2')
    
    parser.add_argument( 'infile',
            type=argparse.FileType('r'),
            default=sys.stdin,
            help='data file (stdin by default)')

    parser.add_argument( '--stats',
            #type=bool,
            action='store_true',
            help='print statistics' )
    
    args = parser.parse_args()
    return args


def get_chan_rates(infile, interval=60):
    """ Count event rate statistics per time intervals.
        Return: channels, [(line_no, Counter),...]
    """
    count = Counter()
    ts_incr = interval * HZ
    next_ts = None
    ret = []
    channels = set()
    
    for lineno, line in enumerate(infile):
        
        if line[0] == '#':
            continue  # skip comments

        line = '\t'.join(line.split())  # join spaces
        ts, chan, rest = line[:-1].split('\t', 2)  #stip '\n' without making a copy of the string
        ts = float(ts)
        chan = int(chan)
        
        if chan not in channels:
            channels.add(chan) 
        count[chan] += 1

        if next_ts is None:
            next_ts = ts + ts_incr

        if ts > next_ts:
            next_ts = ts + ts_incr
            ret.append( (lineno, count) )
            count = Counter()

    return channels, ret


def print_rates(rates):
    for lineno, counter in rates:
        print lineno, counter


def count_mean_rates(rates):
    """
    Return mean statistics for each channel.
    """
    data = defaultdict(list)

    for lineno, counter in rates:
        for chan, val in counter.items():
            data[chan].append(val)
    
    means = {}
    for chan, vals in data.items():
        means[chan] = sum(vals)* 1.0/len(vals)

    return means


def check_rates(rates, means):
    """ Check if rates is good.
        Return: [(lineno, True|False), ...]
    """
    rate_limits = dict( ((k, v * 4) for k,v in means.items() ))
    res = []

    for lineno, counts in rates:
        for c, v in counts.items():
            if v > rate_limits[c]:
                res.append( (lineno, False))
                continue
        res.append( (lineno, True))

    return res
    

def print_stats(stats):
    print stats



def main():
    args = parse_args()
    #print args

    channels, rates = get_chan_rates(args.infile)
    means = count_mean_rates(rates)
    checkrates = check_rates(rates, means)

    if args.stats:
        print means
        pass
    
    args.infile.seek(0,0)  # move to beginning of the file
    lastline, isok = checkrates.pop(0)

    for lineno, line in enumerate(args.infile):
        
        while lineno >= lastline:
            try:
                lastline, isok = checkrates.pop(0)
            except IndexError:
                # end of time interval
                exit(0)
        
        if isok:
            sys.stdout.write(line)

    
if __name__ == "__main__":
    main()
