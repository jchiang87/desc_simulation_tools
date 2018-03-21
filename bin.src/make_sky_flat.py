#!/usr/bin/env python
"""
Script to make sky flats from eimage and calexp data.
"""
import sys
import argparse
import lsst.afw.math as afw_math
import lsst.daf.persistence as dp

def get_stats_control(exposure, exclude=('EDGE',)):
    """
    Create a StatisticsControl object and set all of the mask bits
    in the exposure, except the excluded ones.
    """
    stats_ctrl = afw_math.StatisticsControl()
    mpd = exposure.getMask().getMaskPlaneDict()
    # Turn on all of the mask bits except the excluded ones.
    bits = 2**len(mpd) - 1 - sum([2**mpd[mask_id] for mask_id in exclude])
    stats_ctrl.setAndMask(bits)
    return stats_ctrl

def make_sky_flat(butler, dataId, sky_flat_stat=afw_math.MEANCLIP,
                  nframes=None):
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
    medians = []
    stats_ctrl = None
    for i, dataref in enumerate(datarefs[:nframes]):
        sys.stdout.write("%s  %s  " % (i, nframes))
        eimage = butler.get('eimage', dataref.dataId)
        try:
            # Add the calexp mask to the eimage exposure so that
            # sources and other non-background features can be masked.
            eimage.setMask(dataref.get().getMask())
            mi = eimage.getMaskedImage()
            # Subtract the image median so that unmasked areas do not
            # introduce structure in the final stacked image.
            if stats_ctrl is None:
                stats_ctrl = get_stats_control(eimage)
            image_median = afw_math.makeStatistics(mi, afw_math.MEDIAN,
                                                   stats_ctrl).getValue()
            mi -= image_median
            images.append(mi)
            medians.append(image_median)
            sys.stdout.write("%s" % image_median)
        except dp.NoResults as eobj:
            # NoResults error from the butler.  Skip this exposure, but
            # print a message reporting the error.
            print(dataref.dataId, eobj)
        sys.stdout.write("\n")
        sys.stdout.flush()

    # Make the sky flat.
    sky_flat = afw_math.statisticsStack(images, sky_flat_stat, stats_ctrl)
    # Add back in the sky_flat_stat estimate of the median values.
    sky_flat += afw_math.makeStatistics(medians, sky_flat_stat).getValue()

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

    parser = argparse.ArgumentParser(description="Application to produce a sky flat from eimage and calexp data.")
    parser.add_argument('repo', type=str, help='Stack data repo')
    parser.add_argument('--raft', type=str, help='raft id, e.g., "2,2"')
    parser.add_argument('--sensor', type=str, help='sensor id, e.g., "1,1"')
    parser.add_argument('--filter', type=str, help='filter, e.g., r')
    parser.add_argument('--outfile', type=str, default=None,
                        help='output FITS filename [sky_flat_fb_Rxx_Sxx.fits]')
    parser.add_argument('--nframes', type=int, default=None,
                        help='maximum number of frames to process')
    args = parser.parse_args()

    butler = dp.Butler(args.repo)
    dataId = dict(raft=args.raft, sensor=args.sensor, filter=args.filter)

    sky_flat = make_sky_flat(butler, dataId, nframes=args.nframes)

    outfile = args.outfile
    if outfile is None:
        outfile = 'sky_flat_f%s_R%s_S%s.fits' % (args.filter, args.raft[::2],
                                                 args.sensor[::2])
    sky_flat.writeFits(outfile)
