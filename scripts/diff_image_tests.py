import os
import glob
import subprocess
import numpy as np
import scipy.stats
import astropy.io.fits as fits
import matplotlib.pyplot as plt

plt.ion()

def plot_pixel_diff_dist(eimage1, eimage2, bins=50, range=(-3, 3), title=''):
    im1 = fits.open(eimage1)
    im2 = fits.open(eimage2)
    # These are eimages, so the pixel contents are Poisson counts and
    # dividing the difference by the sqrt of the sum, scales by the
    # effective Gaussian sigma so the resulting distribution should be
    # a Gaussian with sigma=1 in null case.
    diff = (im1[0].data - im2[0].data)/np.sqrt(im1[0].data + im2[0].data)
    y, x, _ = plt.hist(diff.ravel(), bins=bins, range=range, histtype='step',
                       label="(im1 - im2)/sqrt(im1 + im2)")
    plt.yscale('log')
    plt.axvline(0, linestyle=':')
    # Overlay a Gaussian function with unit sigma.
    binsize = x[1] - x[0]
    plt.plot(x, sum(y)*scipy.stats.norm.pdf(x)*binsize, linestyle='--',
             label='unit sigma Gaussian')
    plt.legend(fontsize='x-small')
    plt.title(title, fontsize='small')
    return x, y

grid_files = sorted(glob.glob('/global/cscratch1/sd/jchiang8/imsim_pipeline/GridPP_Runs/fits/*R22_S11*'))

theta_dir = '/global/projecta/projectdirs/lsst/groups/CI/ALCF_1.2i/testing/sv2/skx'
knl_dir = '/global/projecta/projectdirs/lsst/groups/CI/ALCF_1.2i/testing/sv/knl'

fig = plt.figure(figsize=(9, 12))

for i, grid_file in enumerate(grid_files):
    fig.add_subplot(3, 2, i+1)
    basename = os.path.basename(grid_file)
    command = 'find {} -name {}\* -print'.format(theta_dir, basename)
    theta_file = subprocess.check_output(command, shell=True).decode('utf-8').strip()
    command = 'find {} -name {}\* -print'.format(knl_dir, basename)
    knl_file = subprocess.check_output(command, shell=True).decode('utf-8').strip()
#    x, y = plot_pixel_diff_dist(grid_file, knl_file, title=basename)
    x, y = plot_pixel_diff_dist(grid_file, theta_file, title=basename)
#    x, y = plot_pixel_diff_dist(theta_file, knl_file, title=basename)
    print()
plt.tight_layout()
