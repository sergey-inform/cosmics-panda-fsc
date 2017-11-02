#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Sergey Ryzhikov <sergey.ryzhikov@ihep.ru>

# A simple script to plot temperature and humidity data.
# Data format:
#2017-10-27 15:58:26     DHT21 sensors
#2017-10-27 15:58:26     Status, Humidity (%),   Temperature (*C)
#2017-10-27 15:58:26     OK      29.00   19.20
#...
#

import sys
from datetime import datetime
from matplotlib import pyplot as plt

filename = "humtemp.log"
if len(sys.argv) > 1:
	filename = sys.argv[1]  # the first argument is a name of file

data = {'date':[],
	'hum':[],
	'temp': []
	}

with open(filename, 'r') as f:
	for line in f:
		vals = line.split()
		date = datetime.strptime(
			vals[0]+vals[1],
			'%Y-%m-%d%H:%M:%S')  # '2017-11-0216:01:03' -> datetime
		try:
			status = vals[2]
			hum = float(vals[3])
			temp = float(vals[4])

		except Exception as e:
			continue  # skip line
		
		#print vals

		if status != 'OK':
			continue

		data['date'].append(date)
		data['hum'].append(hum)
		data['temp'].append(temp)

# Humidity plot
fig, ax1 = plt.subplots()
l1, = ax1.plot_date(data['date'], data['hum'], '-b')
ax1.grid()

# Temperature plot
ax2 = ax1.twinx()
l2, = ax2.plot_date(data['date'], data['temp'], '-r')

fig.legend( (l1,l2), ('humidity', 'temperature'), "upper left")
fig.autofmt_xdate()

plt.show()
