import os
import sys
import time
import glob
import subprocess
import multiprocessing
import desc.imsim

class WriteAmpFile:
    def __init__(self, opsim_db):
        self.opsim_db = opsim_db

    def __call__(self, eimage_file):
        image_source = desc.imsim.ImageSource.create_from_eimage(eimage_file,
                                                                 opsim_db=self.opsim)
        image_source.write_fits_file(self.outfile(eimage_file))

    @staticmethod
    def outfile(eimage_file, outdir='.'):
        return os.path.join(outdir, os.path.basename(eimage_file).replace('lsst_e', 'lsst_a'))

eimage_files = sorted(glob.glob('lsst_e_*.fits'))

processes = 10
pool = multiprocessing.Pool(processes=processes)
results = []
write_amp_file = WriteAmpFile('/global/cscratch1/sd/descpho/Pipeline-tasks/DC2-R1-2p-WFD-r/000094/instCat/phosim_cat_219976.txt')
for item in eimage_files:
    outfile = write_amp_file.outfile(item)
    if os.path.isfile(outfile):
        continue
    print("processing", os.path.basename(item))
    sys.stdout.flush()
    results.append(pool.apply_async(write_amp_file, (item,)))

pool.close()
pool.join()
for res in results:
    res.get()
