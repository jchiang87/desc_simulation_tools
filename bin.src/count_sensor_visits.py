#!/usr/bin/env python
import os
import glob

phosim_root_path = '/global/projecta/projectdirs/lsst/production/DC2'
stream_paths = glob.glob(os.path.join(phosim_root_path, 'DC2-R1-2p*'))

num_sensors = 0
for folder in stream_paths:
    print(os.path.basename(folder))
    visit_dirs = sorted(glob.glob(os.path.join(folder, 'output', '*')))
    for visit_dir in visit_dirs:
        eimages = glob.glob(os.path.join(visit_dir, 'lsst_e*'))
        if eimages:
            obsHistID = os.path.basename(eimages[0]).split('_')[2]
            print(os.path.basename(visit_dir), obsHistID, len(eimages))
            num_sensors += len(eimages)
    print()

print("total # sensor-visits simulated:", num_sensors)
