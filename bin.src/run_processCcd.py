#!/usr/bin/env python
import os
import subprocess
import multiprocessing
import sqlite3
import pandas as pd

class RunProcessCcd:
    """Callback function class for running processCcd.py in a subprocess
    via the multiprocessing module.
    """
    def __init__(self, repo, rerun):
        self.template = 'processCcd.py {} --rerun {} --id visit=%(visit)d raftName=%(raftName)s detectorName=%(detectorName)s --calib %(calib_path)s --no-versions --clobber-config'.format(repo, rerun)

    def __call__(self, visit, filt, raftName, detectorName, calib_path):
        command = self.template % locals()
        log_file = os.path.join(logging_dir,
                                'processCcd_{}-{}_{}_{}.log'
                                .format(visit, filt, raftName, detectorName))
        full_command = "(time %(command)s) >& %(log_file)s" % locals()
        print(full_command)
        subprocess.check_call(full_command, shell=True)

def run_processCcd_pool(visits, repo, rerun, processes, logging_dir, calib):
    os.makedirs(logging_dir, exist_ok=True)
    registry = os.path.join(repo, 'registry.sqlite3')
    with sqlite3.connect(registry) as conn:
        exp_info = pd.read_sql('select visit, filter, raftName, detectorName, '
                               'detector from raw', conn)
    run_processCcd = RunProcessCcd(repo, rerun)
    with multiprocessing.Pool(processes=processes) as pool:
        results = []
        for visit in visits:
            df = exp_info.query('visit=={}'.format(visit))
            print(visit, len(df))
            for irow in range(len(df)):
                row = df.iloc[irow]
                filt = row['filter']
                raftName = row['raftName']
                detectorName = row['detectorName']
                det_name = '{}_{}'.format(raftName, detectorName)
                calib_path = calib
                visit_dir = '{:08d}-{}'.format(visit, filt)
                suffix = 'det{:03d}.fits'.format(row['detector'])
                calexp_fn = 'calexp_' + '-'.join((visit_dir, raftName,
                                                  detectorName, suffix))
                calexp_path = os.path.join(repo, 'rerun', rerun, 'calexp',
                                           visit_dir, raftName, calexp_fn)
                print(calexp_path)
                if not os.path.isfile(calexp_path):
                    results.append(pool.apply_async(run_processCcd,
                                                    (visit, filt, raftName,
                                                     detectorName, calib_path)))
        pool.close()
        pool.join()
        for res in results:
            res.get()


if __name__ == '__main__':
    import sys
    import configparser
    cp = configparser.ConfigParser()
    cp.optionxform = str

    cp.read(sys.argv[1])
    config = dict(cp.items('DEFAULT'))
    repo = config['repo']
    rerun = config['rerun']
    calib = config['calib']
    logging_dir = config['logging_dir']
    visits = [int(_.strip()) for _ in config['visits'].split(',')]
    processes = int(config['processes'])
    print(config)
    run_processCcd_pool(visits, repo, rerun, processes, logging_dir, calib)
