#!/usr/bin/env python
from collections import namedtuple
import numpy as np
import matplotlib.pyplot as plt

plt.ion()

class ProcessInfo:
    def __init__(self, file_name, label=None):
        self.colnames = 'cumtime RSS_mem id ADU cputime galsimtype'.split()
        self.data = np.recfromtxt(file_name, names=self.colnames)
        self.object_num = np.arange(len(self.data))
        self.label = label

    def __getitem__(self, key):
        if key in self.colnames:
            return self.data[key]
        elif key == 'object_num':
            return self.object_num

    def plot(self, xy_axes, fmt='.', color=None):
        xcol, xlabel = xy_axes[0]
        ycol, ylabel = xy_axes[1]
        my_plot = plt.errorbar(self[xcol], self[ycol], fmt=fmt, color=color,
                               label=self.label)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        return my_plot

if __name__ == '__main__':
    PlotAxis = namedtuple('PlotAxis', 'column label'.split())
    process_info_data = [
        ProcessInfo('imsim_process_info_fast_silicon_transpose.txt',
                    label='fast silicon'),
#        ProcessInfo('imsim_process_info_sensor.txt',
#                    label='no treerings')
    ]

    xy_plots = (
        (PlotAxis('object_num', 'object #'),
         PlotAxis('cumtime', 'cumulative cpu time (s)')),
        (PlotAxis('object_num', 'object #'),
         PlotAxis('RSS_mem', 'RSS memory (GB)')),
        (PlotAxis('object_num', 'object #'),
         PlotAxis('ADU', 'flux (ADU)'))
    )

    plt.rcParams['figure.figsize'] = (8, 4)
    plt.rcParams['legend.fontsize'] = 'x-small'

    fig = plt.figure()
    ny, nx = 1, 3
    for i, xy_axes in enumerate(xy_plots):
        fig.add_subplot(ny, nx, i + 1)
        for process_info in process_info_data:
            process_info.plot(xy_axes)
        plt.legend(loc=0)
    plt.tight_layout()
