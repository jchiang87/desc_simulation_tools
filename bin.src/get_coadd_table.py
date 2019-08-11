#!/usr/bin/env python
from __future__ import print_function
import os
import pandas as pd
import lsst.daf.persistence as dp
#import desc.pserv

def create_sql_schema(catalog, outfile, table_name='CoaddObject'):
    sql_type = {'Angle': 'DOUBLE',
                'D': 'DOUBLE',
                'F': 'FLOAT',
                'Flag': 'BIT',
                'I': 'INT',
                'L': 'BIGINT'}
    with open(outfile, 'w') as output:
        output.write("create table if not exists CoaddObject (\n")
        for item in catalog.schema.asList():
            output.write("%s %s %s,\n" % (" "*6,
                                          item.field.getName(),
                                          sql_type[item.field.getTypeString()]))
        output.write("       project CHAR(30),\n")
        output.write("       primary key (id, project)\n")
        output.write("       )\n")

def write_csv_file(catalog, outfile=None):
    columns = []
    df = pd.DataFrame()
    for col in catalog.getSchema():
        name = col.field.getName()
        df[name] = catalog.get(name)
        columns.append(name)
    if outfile is not None:
        df.to_csv(outfile, index=False, columns=columns)
    return df

def get_patches(butler):
    skymap = butler.get('deepCoadd_skyMap')
    tract = [x for x in skymap][0]
    patches = dict()
    for tract in skymap:
        patches[tract.getId()] = ['%i,%i' % x.getIndex() for x in tract]
    return patches

if __name__ == '__main__':
    db_info = dict(host='scidb1.nersc.gov',
                   database='DESC_DC1_Level_2')
    conn = desc.pserv.DbConnection(**db_info)

    dry_run = True
    dry_run = False

    create_script = 'coadd_schema.sql'

    repo = '/global/cscratch1/sd/descdm/DC1/DC1-imsim-dithered'
    butler = dp.Butler(repo)
    patches = get_patches(butler)

    tract = 0
    band = 'r'

    n = 0
    nmax = 1
    for patch in patches[tract]:
        dataId = dict(patch=patch, tract=tract, filter=band)
        try:
            catalog = butler.get('deepCoadd_meas', dataId=dataId)
        except RuntimeError as eobj:
            continue
        if not os.path.isfile(create_script):
            create_sql_schema(catalog, create_script)
            conn.run_script(create_script, dry_run=dry_run)

        if n >= nmax:
            break
        csv_file = 'coadd_catalog_%s.csv' % patch
        df = write_csv_file(catalog, csv_file)

        print("loading %s" % csv_file)
        n += 1
        if not dry_run:
            conn.load_csv('CoaddObject', csv_file)
