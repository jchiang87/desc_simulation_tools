#!/usr/bin/env python
import os
import copy
from collections import namedtuple
import numpy as np
import matplotlib.pyplot as plt
import lsst.afw.cameraGeom.utils as cameraGeomUtils
import lsst.afw.display as afw_display
import lsst.afw.math as afw_math
import lsst.daf.persistence as dp
plt.ion()

def plot_profile(exposure, row, bg=None, label='', box=None):
    imarr = np.array(exposure.getImage().getArray(), dtype=np.float)
    ny, nx = imarr.shape
    if bg is not None:
        imarr -= bg.getImage().getArray()
    if box is not None:
        kernel = np.ones(box)/box
        profile = np.convolve(imarr[row, :], kernel, mode='same')
    else:
        profile = imarr[row, :]
    plt.errorbar(range(nx), profile, fmt='-', label=label)
    return profile

def set_ybounds(profile, nsig=3):
    axis = list(plt.axis())
    stats = afw_math.makeStatistics(profile, afw_math.STDEVCLIP | afw_math.MEDIAN)
    median = stats.getValue(afw_math.MEDIAN)
    sigma = stats.getValue(afw_math.STDEVCLIP)
    axis[2:] = median - nsig*sigma, median + nsig*sigma
    plt.axis(axis)

Images = namedtuple('Images', 'calexp bg eimage dataId'.split())
def display_images(butler, dataId, frame0=1):
    calexp = butler.get('calexp', dataId)
    bg = butler.get('calexpBackground', dataId)
    eimage = butler.get('eimage', dataId)

    disp_eimage = afw_display.Display(frame0)
    disp_eimage.mtv(eimage)

    disp_bg = afw_display.Display(frame0 + 1)
    disp_bg.mtv(bg.getImage())

    disp_calexp = afw_display.Display(frame0 + 2)
    disp_calexp.mtv(calexp)
    return Images(calexp, bg, eimage, dataId)

repo = '/global/cscratch1/sd/jchiang8/DC2/phosim_Run1.1p/output'

butler = dp.Butler(repo)

# sensor near edge of fov
images_edge = display_images(butler, dict(visit=181866, raft='0,3',
                                          sensor='0,2'), 1)

# sensor far from edge of fov
images_center = display_images(butler, dict(visit=181866, raft='1,2',
                                            sensor='1,1'), 4)

box = 100
row = 2000
for ims in (images_edge, images_center):
    plt.figure()
    profile = plot_profile(ims.eimage, row, box=box,
                           label='eimage, {}-pixel box-car'.format(box))
    plot_profile(ims.bg, row, box=None, label='background')
    set_ybounds(profile)
    plt.title('v%(visit)i, R:%(raft)s, S:%(sensor)s' % ims.dataId)
    plt.legend(loc=1)
    plt.savefig('profile_v%i_R%s_S%s_%i.png' % (ims.dataId['visit'],
                                                ims.dataId['raft'][::2],
                                                ims.dataId['sensor'][::2],
                                                row))
