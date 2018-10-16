import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import scipy
import astropy.visualization as viz
from astropy.coordinates import SkyCoord
from astropy.visualization.mpl_normalize import ImageNormalize
import lsst.daf.persistence as dp
import lsst.afw.display as afw_display
import lsst.afw.image as afw_image
import lsst.afw.geom as afw_geom
from lsst.meas.algorithms import LoadIndexedReferenceObjectsTask

plt.ion()

default_colors = {'CR': 'red', 'DETECTED': 'blue'}

def image_norm(image_array, percentiles=(0, 99.9), stretch=viz.AsinhStretch):
    """
    Create the ImageNormalize object based on the desired stretch and
    pixel value range.
    See http://docs.astropy.org/en/stable/visualization/normalization.html
    """
    vmin, vmax = scipy.percentile(image_array.ravel(), percentiles)
    norm = ImageNormalize(vmin=vmin, vmax=vmax, stretch=stretch())
    return norm

def display_calexp(calexp, colors=default_colors, alpha=0.40, cmap=plt.cm.gray, percentiles=(0, 99.9), **kwds):
    image = calexp.getImage()
    box = afw_geom.Box2D(image.getBBox())
    extent = (box.getMinX(), box.getMaxX(), box.getMinY(), box.getMaxY())
    kwds.setdefault("extent", extent)
    kwds.setdefault("origin", "lower")
    kwds.setdefault("interpolation", "nearest")
    kwds.setdefault("cmap", cmap)
    disp = plt.imshow(image.array, **kwds)
    norm = image_norm(image.array, percentiles=percentiles)
    disp.set_norm(norm)
    kwds.pop("vmin", None)
    kwds.pop("vmax", None)
    kwds.pop("norm", None)
    kwds.pop("cmap", None)
    mask = calexp.getMask()
    for plane, color in colors.items():
        array = np.zeros(mask.array.shape + (4,), dtype=float)
        rgba = np.array(matplotlib.colors.hex2color(matplotlib.colors.cnames[color]) + (alpha, ),
                        dtype=float)
        np.multiply.outer((mask.array & mask.getPlaneBitMask(plane)).astype(bool), rgba, out=array)
        matplotlib.pyplot.imshow(array, **kwds)

def overlay_sources(src, calexp, ref_pix_coords=None,
                    mag_cut=22.):
    Flags = ["base_PixelFlags_flag_saturated", "base_PixelFlags_flag_cr",
             "base_PixelFlags_flag_interpolated",
             "slot_ModelFlux_flag", "base_SdssCentroid_flag",
             "base_SdssCentroid_flag_almostNoSecondDerivative",
             "base_SdssCentroid_flag_edge",
             "base_SdssCentroid_flag_noSecondDerivative",
             "base_SdssCentroid_flag_notAtMaximum",
             "base_SdssCentroid_flag_resetToPeak",
             "base_SdssShape_flag", "base_ClassificationExtendedness_flag"]
    calib = calexp.getCalib()
    xvals, yvals = [], []
    selection = src['base_ClassificationExtendedness_value'] == 0
    for flag in Flags:
        selection &= src[flag]==False
    my_src = src[selection].copy(deep=True)
    for s in my_src:
        mag = calib.getMagnitude(s['slot_ModelFlux_instFlux'])
        if mag > mag_cut:
            continue
        xvals.append(s.getX())
        yvals.append(s.getY())
    plt.errorbar(xvals, yvals, fmt='+', color='red', alpha=0.8,
                 fillstyle='none')
    if ref_pix_coords is not None:
        plt.errorbar(*ref_pix_coords, fmt='x', color='green', alpha=0.8,
                     fillstyle='none')
    return xvals, yvals, my_src

class RefCat:
    def __init__(self, butler):
        self.butler = butler
        refConfig = LoadIndexedReferenceObjectsTask.ConfigClass()
        self.refTask = LoadIndexedReferenceObjectsTask(self.butler,
                                                       config=refConfig)
    def get_pixel_coords(self, dataId, mag_cut=22.):
        calexp = self.butler.get('calexp', dataId)
        wcs = calexp.getWcs()
        dim = calexp.getDimensions()
        centerPixel = afw_geom.Point2D(dim.getX()/2., dim.getY()/2.)
        centerCoord = wcs.pixelToSky(centerPixel)
        radius = afw_geom.Angle(0.17, afw_geom.degrees)
        ref_cat \
            = self.refTask.loadSkyCircle(centerCoord, radius,
                                         calexp.getFilter().getName()).refCat
        xref, yref = [], []
        mags = -2.5*np.log10(ref_cat['u_flux']/3631.)
        for i, row in enumerate(ref_cat):
            if mags[i] > mag_cut:
                continue
            point = wcs.skyToPixel(row.getCoord())
            xref.append(point.getX())
            yref.append(point.getY())
        return xref, yref, ref_cat

def get_seps(src_cat, calexp, ref_cat, mag_cut=22):
    src_mags \
        = calexp.getCalib().getMagnitude(src_cat['slot_ModelFlux_instFlux'])
    mag_sel = np.where(src_mags < mag_cut)
    src = SkyCoord(ra=src_cat['coord_ra'][mag_sel],
                   dec=src_cat['coord_dec'][mag_sel], unit='rad')
    ref = SkyCoord(ra=ref_cat['coord_ra'], dec=ref_cat['coord_dec'], unit='rad')
    _, dist, _ = src.match_to_catalog_sky(ref)
    return dist.milliarcsecond

if __name__ == '__main__':
    import sys
    butler = dp.Butler('/global/cscratch1/sd/jchiang8/desc/Run1.2p_analysis/output_2018-10-04/rerun/jchiang/w_2018_39')
    ref_cat = RefCat(butler)
    visit, raft, sensor = sys.argv[1:4]
    dataId = dict(visit=int(visit), raftName=raft, detectorName=sensor)
    calexp = butler.get('calexp', dataId=dataId)
    src = butler.get('src', dataId=dataId)
    xref, yref, my_ref_cat = ref_cat.get_pixel_coords(dataId)

    show_mask = False
    show_mask = True
    colors = default_colors if show_mask else {}
    fig = plt.figure(figsize=(18, 7.5))
    fig.add_subplot(1, 2, 1)
    display_calexp(calexp, colors=colors, percentiles=(0, 99.95))
    xvals, yvals, src_cat \
        = overlay_sources(src, calexp, ref_pix_coords=(xref, yref))
    plt.xlabel('x (pixel)')
    plt.ylabel('y (pixel)')
    plt.xlim(0, 4072)
    plt.ylim(0, 4000)

    fig.add_subplot(1, 2, 2)
    seps = get_seps(src_cat, calexp, my_ref_cat, mag_cut=22.)
    plt.hist(seps, range=(0, 1000), bins=50, histtype='step')
    plt.xlabel('offsets (mas)')
    plt.suptitle('v%(visit)d, %(raftName)s, %(detectorName)s' % dataId)
