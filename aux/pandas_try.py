#!/usr/bin/env python

import sys
import pandas as pd
from matplotlib import pyplot as plt
from itertools import cycle

fp = sys.argv[1]

df = pd.read_csv(fp, sep=' ')
columns = ['run', 'chan', 'dist', 'trigA', 'trigB', 'value']
df.columns = columns

colours = ['r','g','b','y','c']
filled_markers = ('o', 'v', '^', '<', '>', '8', 's', 'p', '*', 'h', 'H', 'D', 'd')

chans = sorted(df['chan'].unique())
df['group'] = df['run'].apply(lambda s: s.split('_')[0])
groups = df['group'].unique()

for chan in chans:
 plt.cla()
 color = cycle(colours)
 marker = cycle(filled_markers)
 for group in groups:
  s = df[(df['chan'] == chan) & (df['group'] == group) & (df['value']>0.5)]
  plt.scatter(s['dist'], s['value'], label=group, c = color.next(), marker=marker.next())
 
 ax = plt.gca()
 ax.set_xlim(0)
 plt.axhline(1.0, color='black')
 plt.legend(loc='upper left')
 plt.title(chan)
 plt.show()
 #plt.savefig('{}.png'.format(chan))

