#!/usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
plt.ion()

def get_object_coords(infile):
    ra, dec = [], []
    ra_s, dec_s = [], []
    zlast = ''
    with open(infile) as input_:
        for line in input_:
            if not line.startswith('object'):
                continue
            tokens = line.split()
            ra.append(float(tokens[2]))
            dec.append(float(tokens[3]))
            if tokens[5].startswith('agn') and tokens[6] == zlast:
                ra_s.append(ra[-1])
                dec_s.append(dec[-1])
            zlast = tokens[6]
    return np.array(ra), np.array(dec), np.array(ra_s), np.array(dec_s)

sprinkled = get_object_coords('sprinkled_new_caches/imsim_cat_230.txt')
unsprinkled = get_object_coords('unsprinkled/imsim_cat_230.txt')

uddf_ra = [53.764, 52.486, 52.479, 53.771, 53.764]
uddf_dec = [-27.533, -27.533, -28.667, -28.667, -27.533]

wfd_ra = [52.25, 52.11, 58.02, 57.87, 52.25]
wfd_dec = [-27.25, -32.25, -32.25, -27.25, -27.25]

#axis = [51.5, 54.5, -28.5, -26]
axis = [51.5, 58.5, -32.75, -27.]

plt.figure()
plt.hist2d(*sprinkled[:2], bins=40, norm=LogNorm())
plt.errorbar(*sprinkled[2:], fmt='.', color='black')
plt.errorbar(wfd_ra, wfd_dec, fmt='--', color='green', label='protoDC2 boundary')
plt.errorbar(uddf_ra, uddf_dec, fmt='--', color='red', label='uDDF boundary')
plt.colorbar()
plt.xlabel('RA (J2000 degrees)')
plt.ylabel('Dec (J2000 degrees)')
plt.title('v230, sprinkled')
plt.legend(loc=1)
plt.axis(axis)
plt.savefig('sprinkled_v230_1deg-fov_full_wfd.png')


#plt.figure()
#plt.hist2d(*unsprinkled[:2], bins=40, norm=LogNorm())
#plt.errorbar(*unsprinkled[2:], fmt='.', color='black')
#plt.errorbar(wfd_ra, wfd_dec, fmt='--', color='green', label='protoDC2 boundary')
#plt.errorbar(uddf_ra, uddf_dec, fmt='--', color='red', label='uDDF boundary')
#plt.colorbar()
#plt.xlabel('RA (J2000 degrees)')
#plt.ylabel('Dec (J2000 degrees)')
#plt.title('v230, unsprinkled')
#plt.legend(loc=1)
#plt.axis(axis)
#plt.savefig('unsprinkled_v230_1deg-fov.png')
