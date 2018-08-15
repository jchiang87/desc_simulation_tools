import os
import glob
import sqlite3
import multiprocessing
import numpy as np
import astropy.io.fits as fits

def process_dataset(dataset, outfile):
    print("processing", dataset)
    root_dir = '/global/projecta/projectdirs/lsst/production/DC2'
    eimage_dir = os.path.join(root_dir, dataset, 'output')
    stream_dirs = sorted(glob.glob(os.path.join(eimage_dir, '0*')))
    with open(outfile, 'w') as output:
        for stream_dir in stream_dirs:
            eimage_files \
                = sorted(glob.glob(os.path.join(stream_dir, 'lsst_e*R22_S11*')))
            nfiles = len(eimage_files)
            for eimage_file in eimage_files:
                eimage = fits.open(eimage_file)
                hdr = eimage[0].header
                raft, sensor = hdr['CHIPID'].split('_')
                counts = float(np.median(eimage[0].data.ravel()))
                version = os.path.basename(hdr['BRANCH'])
                line = '  '.join(6*['{}']) + '\n'
                output.write(line.format(hdr['FILTER'], hdr['OBSID'], raft,
                                         sensor, counts, version))
                output.flush()

datasets = (['DC2-R1-2p-WFD-{}'.format(band) for band in 'ugrizy'] +
            ['DC2-R1-2p-uDDF-{}'.format(band) for band in 'ugrizy'])

processes = 4
pool = multiprocessing.Pool(processes=processes)
results = []
for dataset in datasets:
    outfile = dataset + '.txt'
    results.append(pool.apply_async(process_dataset, (dataset, outfile)))
pool.close()
pool.join()
for res in results:
    res.get()
