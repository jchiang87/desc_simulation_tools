import os
import glob
import argparse
import numpy as np
import sqlite3
import astropy.io.fits as fits
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

import lsst.sims.utils
from lsst.sims.utils import _getRotSkyPos as getRotSkyPos
import lsst.sims.coordUtils
from lsst.afw.cameraGeom import SCIENCE
from lsst.sims.GalSimInterface import LSSTCameraWrapper
from lsst.sims.catUtils.utils import ObservationMetaDataGenerator

plt.ion()

class ChipPlotter(object):
    def __init__(self, obs_md):
        self.obs_md = obs_md
        self.camera = LSSTCameraWrapper().camera
    def _get_corners(self, chip_name):
        corners = lsst.sims.coordUtils.getCornerRaDec(chip_name, self.camera,
                                                      self.obs_md)
        ra, dec = [], []
        for i in [0, 1, 3, 2, 0]:
            ra.append(corners[i][0])
            dec.append(corners[i][1])
        return ra, dec
    def plot_chips(self, phosim_output_dir, color='black'):
        eimages = glob.glob(os.path.join(phosim_output_dir, 'lsst_e*'))
        ra, dec = [], []
        for i, eimage_file in enumerate(eimages):
            fits_data = fits.open(eimage_file)
            chipid = fits_data[0].header['CHIPID']
            chipname = 'R:{},{} S:{},{}'.format(chipid[1], chipid[2],
                                                chipid[5], chipid[6])
            if i == 0:
                plt.errorbar(*self._get_corners(chipname), fmt='-', color=color,
                             label='simulated sensors')
            else:
                plt.errorbar(*self._get_corners(chipname), fmt='-', color=color)


def plot_Run1_1p_regions():
    uddf_ra = [53.764, 52.486, 52.479, 53.771, 53.764]
    uddf_dec = [-27.533, -27.533, -28.667, -28.667, -27.533]

    wfd_ra = [52.25, 52.11, 58.02, 57.87, 52.25]
    wfd_dec = [-27.25, -32.25, -32.25, -27.25, -27.25]

    #axis = [51.5, 54.5, -28.5, -26]
    axis = [51.5, 58.5, -32.75, -25.]

    plt.errorbar(wfd_ra, wfd_dec, fmt='--', color='green',
                 label='protoDC2 boundary')
    plt.errorbar(uddf_ra, uddf_dec, fmt='--', color='red',
                 label='uDDF boundary')
    plt.xlabel('RA (J2000 degrees)')
    plt.ylabel('Dec (J2000 degrees)')
    plt.axis(axis)

class OpsimdbInterface(object):
    def __init__(self, opsim_db='/global/projecta/projectdirs/lsst/groups/SSim/DC2/minion_1016_desc_dithered_v4.db'):
        self.conn = sqlite3.connect(opsim_db)
        self.obs_gen = ObservationMetaDataGenerator(database=opsim_db,
                                                    driver='sqlite')
        self._cache = dict()
    def get_obs_md(self, obsHistID):
        if obsHistID not in self._cache:
            self._cache[obsHistID] = self._get_obs_md(obsHistID)
        return self._cache[obsHistID]
    def _get_obs_md(self, obsHistID):
        curs = self.conn.execute('select descDitheredRA, descDitheredDec, descDitheredRotTelPos from Summary where obsHistID={}'.format(obsHistID))
        data = [x for x in curs][0]
        ra, dec = [x*180./np.pi for x in data[:2]]
        rottelpos = data[2]
        obs_md = self.obs_gen.getObservationMetaData(obsHistID=obsHistID,
                                                     boundType='circle',
                                                     boundLength=0.1)[0]
        obs_md.pointingRA = ra
        obs_md.pointingDec = dec
        obs_md.OpsimMetaData['rotTelPos'] = rottelpos
        obs_md.rotSkyPos = getRotSkyPos(obs_md._pointingRA, obs_md._pointingDec,
                                        obs_md, rottelpos)*180./np.pi
        return obs_md
    def plot_fov(self, obsHistID, radius=2.047):
        obs_md = self.get_obs_md(obsHistID)
        ra, dec = obs_md.pointingRA, obs_md.pointingDec
        phi = np.linspace(0, 2*np.pi, 100)
        radius /= np.cos(dec*np.pi/180.)
        plt.errorbar(radius*np.sin(phi) + ra, radius*np.cos(phi) + dec,
                     fmt='--', label='{} fov'.format(obsHistID))


def plot_ref_cat(ref_cat, label='ref cat objects'):
    with open(ref_cat, 'r') as cat_:
        header = cat_.readline()
        names = header.lstrip('#').split(',')
    data = np.recfromtxt(ref_cat, names=names, delimiter=',')
    ra = [np.float(x) for x in data['raJ2000']]
    dec = [np.float(x) for x in data['decJ2000']]
    plt.errorbar(ra, dec, fmt='.', label=label, alpha=0.5)

def get_obsHistID(phosim_output_dir):
    return int(os.path.basename(glob.glob(os.path.join(phosim_output_dir, 'lsst_e_*'))[0]).split('_')[2])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot protoDC2 sensor sims')
    parser.add_argument('visit_subdir', type=str,
                        help='Visit-specific sub-directory with pixel data')
    parser.add_argument('--phosim_root_dir', type=str,
                        default='/global/projecta/projectdirs/lsst/production/DC2',
                        help='root directory for DC2 phosim outputs')
    parser.add_argument('--ref_cat', type=str, default='../ref_cat_Run1.1p.txt',
                        help='reference catalog')

    args = parser.parse_args()

    phosim_output_dir = os.path.join(args.phosim_root_dir, args.visit_subdir)
    obsHistID = get_obsHistID(phosim_output_dir)

    opsimdb_interface = OpsimdbInterface()
    chip_plotter = ChipPlotter(opsimdb_interface.get_obs_md(obsHistID))

    plt.figure()
    plot_ref_cat(args.ref_cat)
    plot_Run1_1p_regions()
    opsimdb_interface.plot_fov(obsHistID)
    chip_plotter.plot_chips(phosim_output_dir)
    plt.legend(loc=1)
    plt.title('visit %s' % obsHistID)
    plt.savefig('visit_%s.png' % obsHistID)
