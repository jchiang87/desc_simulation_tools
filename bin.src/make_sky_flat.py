#!/usr/bin/env python
"""
Script to make sky flats from eimage and calexp data.
"""
import sys
import lsst.afw.math as afw_math
import lsst.daf.persistence as dp

def make_sky_flat(butler, dataId, sky_flat_stat=afw_math.MEANCLIP,
                  med_range=None, nframes=None):
    """
    Make a sky flat from eimages, appylying the calexp masks to avoid
    including counts from detected sources, cosmic rays, and other
    defects.

    Parameters
    ----------
    butler: lsst.daf.persistence.Butler
        Butler to the data repository containing the calexps and eimages.
    dataId: dict specifying the band and sensor, e.g.,
        dict(raft='2,2', sensor='1,1', filter='r')
    sky_flat_stat: lsst.afw.math._statistics.Property [MEANCLIP]
        Statistics property to apply to the stacked images.
    med_range: tuple(float, float) [None]
        If not None, this is the acceptance range for the median pixel
        value of the eimages.
    nframes: int [None]
        If not None, only the first nframes of calexps will be included
        in the image stack.

    Returns
    -------
    lsst.afw.image.MaskedImage: A masked image containing the sky flat.
    """
    # Get datarefs from all of the visits for the band and sensor
    # identified by the dataId.
    datarefs = [x for x in butler.subset('calexp', **dataId)]

    if nframes is None:
        # Process all of the data.
        nframes = len(datarefs)

    # Compile a list of eimages to include in the sky flat.
    images = []
    for i, dataref in enumerate(datarefs[:nframes]):
        print(i, nframes)
        sys.stdout.flush()
        eimage = butler.get('eimage', dataref.dataId)
        # Compute the eimage median for downselection.
        image_median = afw_math.makeStatistics(eimage.getImage(),
                                               afw_math.MEDIAN).getValue()
        if med_range is not None and med_range[0] < image_median < med_range[1]:
            # Add the calexp mask to eimage exposures so that sources
            # and other features can be masked.
            try:
                eimage.setMask(dataref.get().getMask())
                images.append(eimage.getMaskedImage())
            except dp.NoResults:
                # Handle NoResults error from the butler.
                pass

    # Set all of the mask bits via a StatisticsControl
    # object, excluding the edge rolloff mask.
    stat_ctrl = afw_math.StatisticsControl()
    mpd = images[0].getMask().getMaskPlaneDict()
    bits = 2**len(mpd) - 1 - 2**mpd['EDGE']
    stat_ctrl.setAndMask(bits)

    # Make the sky flat.
    sky_flat = afw_math.statisticsStack(images, sky_flat_stat, stat_ctrl)

    # Check stacked image statistics.
    stats = afw_math.makeStatistics(sky_flat,
                                    afw_math.VARIANCECLIP | afw_math.MEANCLIP)
    print("image clipped mean and variance:", stats.getValue(afw_math.MEANCLIP),
          stats.getValue(afw_math.VARIANCECLIP))

    return sky_flat

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import lsst.afw.image as afw_image
    import lsst.afw.display as afw_display
    import lsst.log
    # Silence the CameraMapper warnings about metadata.
    lsst.log.setLevel(lsst.log.getDefaultLoggerName(), lsst.log.ERROR)
    plt.ion()

    repo = '/global/projecta/projectdirs/lsst/production/DC1/DM/DC1-imsim-dithered'
    dataId = dict(raft='2,2', sensor='1,1', filter='r')
    #dataId = dict(raft='0,3', sensor='0,2', filter='r')
    butler = dp.Butler(repo)

    sky_flat = make_sky_flat(butler, dataId, med_range=(300, 500))
    sky_flat.writeFits('sky_flat_R22_S11.fits')
