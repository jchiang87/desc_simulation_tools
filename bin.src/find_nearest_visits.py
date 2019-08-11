#!/usr/bin/env python
"""
For simulated visits, order visits by angular offset from a
desired location, e.g., the center of the protoDC2 Run1.1 field, and
make symlinks of the stream subdirectories in the production area to
the transfer area.
"""

import os
import glob
import sqlite3
import numpy as np
from lsst.sims.utils import _angularSeparation

def opsim_db_visit_coords(opsim_db='/global/projecta/projectdirs/lsst/groups/SSim/DC2/minion_1016_desc_dithered_v4.db', box_size=5,
                          ra0=55.064, dec0=-28.783):
    # Extent of search region + fov radius (2.1 deg).
    half_box_size = np.radians(box_size/2. + 2.1)
    ra0, dec0 = np.radians((55.064, -28.783))
    ra_min, ra_max = ra0 - half_box_size, ra0 + half_box_size
    delta_dec = half_box_size/np.cos(dec0)
    dec_min, dec_max = dec0 - delta_dec, dec0 + delta_dec
    conn = sqlite3.connect(opsim_db)
    query = """select obsHistID, descDitheredRa, descDitheredDec from summary
where descDitheredRa > {} and descDitheredRa < {} and
descDitheredDec > {} and descDitheredDec < {}""".format(ra_min, ra_max, dec_min, dec_max)
    curs = conn.execute(query)
    coords = {entry[0]: entry[1:3] for entry in curs}
    return coords

def find_visits(stream_path):
    obsHistIDs, num_sensors, streams = [], [], []
    visit_dirs = sorted(glob.glob(os.path.join(stream_path, 'output', '*')))
    for visit_dir in visit_dirs:
        eimages = glob.glob(os.path.join(visit_dir, 'lsst_e*'))
        if eimages:
            obsHistID = int(os.path.basename(eimages[0]).split('_')[2])
            obsHistIDs.append(obsHistID)
            num_sensors.append(len(eimages))
            streams.append(os.path.basename(visit_dir))
    return np.array(obsHistIDs), np.array(num_sensors), np.array(streams)


if __name__ == '__main__':
    ra0, dec0 = np.radians((55.064, -28.783))

    phosim_root_path = '/global/projecta/projectdirs/lsst/production/DC2'
    stream_paths = glob.glob(os.path.join(phosim_root_path,
                                          'DC2-R1-2p-WFD*'))

#    transfer_area = '/global/projecta/projectdirs/lsst/global/DC2'
    transfer_area = '.'
    coords = opsim_db_visit_coords(box_size=6)
    for stream_path in stream_paths:
        print(stream_path)

        # Create the directory in the transfer are where the symlinks
        # are made.
        outdir = os.path.join(transfer_area, os.path.basename(stream_path))
        os.makedirs(outdir, exist_ok=True)

        obsHistIDs, num_sensors, streams = find_visits(stream_path)
        offsets = []
        for obsHistID in obsHistIDs:
            offsets.append(_angularSeparation(ra0, dec0, *coords[obsHistID]))
        offsets = np.array(offsets)
        index = np.argsort(offsets)
        icount = 0
        for obsHistID, stream, offset, nsensors \
            in zip(obsHistIDs[index], streams[index],
                   np.degrees(offsets[index]), num_sensors[index]):
            if icount > 10:
                break
            # Require at least half of the sensors in the focal plane
            # and require the offset to be less than 2 degrees.
            if nsensors > 90 and offset < 2.:
                print('%6i  %s  %.2f  %3i' % (obsHistID, stream, offset,
                                              nsensors))
                icount += 1
                os.symlink(os.path.join(stream_path, 'output', stream),
                           os.path.join(outdir, stream))
        print()
