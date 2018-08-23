import numpy as np
import lsst.daf.persistence as dp

def write_region_file(sourceCatalog, outfile):
    with open(outfile, 'w') as output:
        output.write("""# Region file format: DS9 version 4.1
global color=green dashlist=8 3 width=1 font="helvetica 10 normal roman" select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1
fk5
""")
        for ra, dec in zip(np.degrees(sourceCatalog['coord_ra']),
                           np.degrees(sourceCatalog['coord_dec'])):
            output.write("point({},{}) # point=circle\n".format(ra, dec))

def cast(value):
    if value == 'None':
        return None
    try:
        if value.find('.') == -1 and value.find('e') == -1:
            return int(value)
        else:
            return float(value)
    except ValueError:
        # Check if it can be cast as a boolean.
        if value in 'True False'.split():
            return eval(value)
        # Return as the original string.
        return value

def make_dataId(id_list):
    dataId = dict()
    for item in id_list:
        key, value = item.split('=')
        dataId[key] = cast(value)
    return dataId

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('repo', type=str, help="data repo")
    parser.add_argument('--id', nargs='*', help='dataId')
    parser.add_argument('--outfile', type=str, default=None)
    args = parser.parse_args()

    butler = dp.Butler(args.repo)
    dataId = make_dataId(args.id)
    src = butler.get('src', dataId=dataId)

    outfile = "v%(visit)s_%(raftName)s_%(detectorName)s.reg" % dataId \
              if args.outfile is None else args.outfile

    write_region_file(src, outfile)
