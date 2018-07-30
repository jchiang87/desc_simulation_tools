import numpy as np

__all__ = ["write_region_file"]

def write_region_file(sourceCatalog, outfile):
    with open(outfile, 'w') as output:
        output.write("""# Region file format: DS9 version 4.1
global color=green dashlist=8 3 width=1 font="helvetica 10 normal roman" select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1
fk5
""")
        for ra, dec in zip(np.degrees(sourceCatalog['coord_ra']),
                           np.degrees(sourceCatalog['coord_dec'])):
            output.write("point({},{}) # point=circle\n".format(ra, dec))
