#!/usr/bin/env python
import sys
import pickle
import numpy as np
import matplotlib.pyplot as plt
from process_monitor import RssHistory

plt.ion()

try:
    process_info_file = sys.argv[1]
except IndexError:
    process_info_file = 'process_info.pkl'

plt.clf()
data = pickle.load(open(process_info_file, 'rb'))

t0 = None
for pid in data:
    if t0 is None:
        t0 = data[pid].time[0]
    plt.errorbar((np.array(data[pid].time) - t0)/60., data[pid].rss,
                 fmt='-', label='RSS ' + str(pid))
    try:
        plt.errorbar((np.array(data[pid].time) - t0)/60., data[pid].uss,
                     fmt=':', label='USS ' + str(pid))
    except AttributeError:
        ylabel = 'RSS memory (GB)'
    else:
        ylabel = 'RSS/USS memory (GB)'
plt.xlabel('relative time (min)')
plt.ylabel(ylabel)
#plt.legend(loc=0, fontsize='x-small')
