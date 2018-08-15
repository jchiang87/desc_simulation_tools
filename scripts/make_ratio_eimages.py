import os
import glob
import astropy.io.fits as fits
import lsst.afw.image as afw_image

dome_flats = sorted(glob.glob('/global/cscratch1/sd/jchiang8/desc/calibration_products/dome_flats/CALIB_rescaled/flat/g/2022-01-01/flat_g-*.fits'))

#sky_flats = sorted(glob.glob('/global/projecta/projectdirs/lsst/global/in2p3/Run1.2p-test/w_2018_28/rerun/newformat-071718/CALIB/flat/g/2022-11-21/flat_g-*.fits'))

sky_flats = sorted(glob.glob('/global/homes/j/jchiang8/scratch/desc/calibration_products/dome_flats/dome_sky_flat_ratio/output/rerun/jchiang/calib/flat/g/2022-10-13/flat_g-*.fits'))

eimage_files = sorted(glob.glob('/global/projecta/projectdirs/lsst/production/DC2/DC2-R1-2p-WFD-g/output/000027/lsst_e*'))

for dome_file, sky_file, eimage_file in zip(dome_flats, sky_flats,
                                            eimage_files):
    dome_basename = os.path.basename(dome_file).split('_')[1]
    sky_basename = os.path.basename(sky_file).split('_')[1]
    assert(dome_basename == sky_basename)
    sensor = '-'.join(os.path.basename(eimage_file).split('_')[4:6])
    assert(sensor in dome_basename)

    eimage = fits.open(eimage_file)
    sky = afw_image.ImageF(sky_file)
    dome = afw_image.ImageF(dome_file)
    ratio = dome.getArray()/sky.getArray()
    eimage[0].data = ratio.transpose()
    outfile = os.path.basename(eimage_file)[:-len('.gz')]
    print(outfile)
    eimage.writeto(os.path.join('eimage_files_3visit',
                                os.path.basename(outfile)),
                   overwrite=True)
