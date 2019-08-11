#!/usr/bin/env python
from __future__ import print_function
import os
import glob
import shutil
import numpy as np
import pandas as pd
import lsst.daf.persistence as dp

def create_sql_schema(catalog, outfile, table_name):
    """
    Derive the SQL CREATE TABLE script from the catalog fields.

    Parameters
    ----------
    catalog: lsst.afw.table.source.source.SourceCatalog
        SourceCatalog object returned by the Data Butler.
    outfile: str
        Filename of the create table script.
    table_name: str
        Name of the db table to create.
    """
    sql_type = {'Angle': 'DOUBLE',
                'D': 'DOUBLE',
                'F': 'FLOAT',
                'Flag': 'TINYINT(1)',
                'I': 'INT',
                'L': 'BIGINT'}
    with open(outfile, 'w') as output:
        output.write("create table if not exists {} (\n".format(table_name))
        for item in catalog.schema:
            output.write("%s %s %s,\n" % (" "*6,
                                          item.field.getName(),
                                          sql_type[item.field.getTypeString()]))
        output.write("       tract INT,\n")
        output.write("       patch CHAR(2),\n")
        output.write("       primary key (id, tract, patch)\n")
        output.write("       )\n")

def write_csv_file(catalog, tract, patch, outfile=None):
    """
    Write the contents of a SourceCatalog object as a csv file for
    loading into a mysql db table.

    Parameters
    ----------
    catalog: lsst.afw.table.source.source.SourceCatalog
        SourceCatalog object returned by the Data Butler.
    tract: int
        ID of tract.
    patch: str
        ID of patch.  This will be slugified, e.g., "0,1" -> "01".
    outfile: str [None]
        Filename of the csv file.  If None, then no csv file will be written.

    Returns
    -------
    pandas.DataFrame: A data frame of the catalog contents.
    """
    columns = []
    df = pd.DataFrame()
    for col in catalog.getSchema():
        name = col.field.getName()
        coldata = catalog.get(name)
        if coldata.dtype == np.bool:
            df[name] = coldata.astype(int)
        else:
            df[name] = coldata
        columns.append(name)
    columns.extend(['tract', 'patch'])
    df['tract'] = np.ones(len(df), dtype=np.int)*tract
    df['patch'] = np.array([patch.replace(',', '')]*len(df))
    if outfile is not None:
        df.to_csv(outfile, index=False, columns=columns)
    return df

def get_patch_ids(butler):
    """
    Get the patch ids from the SkyMap object.

    Parameters
    ----------
    butler: lsst.daf.persistence.Butler
        Data butler for the desired data repo.

    Returns
    -------
    dict: A dictionary of patch IDs, keyed by tract ID.
    """
    skymap = butler.get('deepCoadd_skyMap')
    patch_ids = dict()
    for tract in skymap:
        patch_ids[tract.getId()] = ['%i,%i' % x.getIndex() for x in tract]
    return patch_ids

def get_tract_ids(repo):
    """
    Get the non-empty tract IDs in the deepCoadd-results/merged folder
    in a data repo.

    Parameters
    ----------
    repo: str
        Data repo path.

    Returns
    -------
    list: a list of tract IDs.
    """
    return [int(os.path.basename(x)) for x in
            glob.glob(os.path.join(repo, 'deepCoadd-results', 'merged', '*'))]

if __name__ == '__main__':
    import desc.pserv
    dry_run = True
    dry_run = False

    db_info = dict(host='nerscdb04.nersc.gov',
                   database='DESC_DC1_Level_2')
    conn = desc.pserv.DbConnection(**db_info)

    data_product = 'deepCoadd_ref'
    dataId = dict()
    band = 'merged'
    schema_script = 'coadd_%s_catalog_schema.sql' % band
    table_name = 'CoaddObject_Run1_1p'

    csv_archive = 'csv_archive_Run1.1p'
    if not os.path.isdir(csv_archive):
        os.mkdir(csv_archive)

    repo = 'Run1.1_output'

    tract_ids = get_tract_ids(repo)
    butler = dp.Butler(repo)
    patch_ids = get_patch_ids(butler)

    nmax = 200
    n = 0
    for tract_id in tract_ids:
        dataId['tract'] = tract_id
        for patch_id in patch_ids[tract_id]:
            if n >= nmax:
                break
            dataId['patch'] = patch_id
            csv_file \
                = 'coadd_catalog_{}_{}_{}.csv'.format(band, tract_id, patch_id)
            if os.path.isfile(os.path.join(csv_archive, csv_file)):
                continue

            try:
                catalog = butler.get(data_product, dataId=dataId)
            except RuntimeError as eobj:
                continue

            if not os.path.isfile(schema_script):
                create_sql_schema(catalog, schema_script, table_name)
                conn.run_script(schema_script, dry_run=dry_run)

            df = write_csv_file(catalog, tract_id, patch_id, outfile=csv_file)

            print("loading %s" % csv_file)
            if not dry_run:
                conn.load_csv(table_name, csv_file)
                shutil.move(csv_file, csv_archive)

            n += 1
