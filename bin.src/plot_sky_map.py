import glob
import sys
import pickle
import os
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches
import lsst.afw.geom as afwGeom
import lsst.afw.image as afwImage
import lsst.daf.persistence as dafPersist

plt.ion()

def makePatch(vertexList, wcs):
    """Return a path in sky coords from vertex list in pixel coords"""
    skyPatchList = [wcs.pixelToSky(pos).getPosition(afwGeom.degrees)
                    for pos in vertexList]
    verts = [(coord[0], coord[1]) for coord in skyPatchList]
    verts.append((0,0))
    codes = [Path.MOVETO,
             Path.LINETO,
             Path.LINETO,
             Path.LINETO,
             Path.CLOSEPOLY,
             ]
    return Path(verts, codes)

def plotSkyMap(skyMap, tract=0, title=None, ax=None):
    if title is None:
        title = 'tract {}'.format(tract)
    tractInfo = skyMap[tract]
    tractBox = afwGeom.Box2D(tractInfo.getBBox())
    tractPosList = tractBox.getCorners()
    wcs = tractInfo.getWcs()
    xNum, yNum = tractInfo.getNumPatches()

    if ax is None:
        fig = plt.figure(figsize=(12,8))
        ax = fig.add_subplot(111)

    tract_center = wcs.pixelToSky(tractBox.getCenter())\
                      .getPosition(afwGeom.degrees)
    ax.text(tract_center[0], tract_center[1], '%d' % tract, size=16,
            ha="center", va="center", color='blue')
    for x in range(xNum):
        for y in range(yNum):
            patchInfo = tractInfo.getPatchInfo([x, y])
            patchBox = afwGeom.Box2D(patchInfo.getOuterBBox())
            pixelPatchList = patchBox.getCorners()
            path = makePatch(pixelPatchList, wcs)
            patch = patches.PathPatch(path, alpha=0.1, lw=1)
            ax.add_patch(patch)
            center = wcs.pixelToSky(patchBox.getCenter())\
                        .getPosition(afwGeom.degrees)
            ax.text(center[0], center[1], '%d,%d'%(x,y), size=6,
                    ha="center", va="center")

    skyPosList = [wcs.pixelToSky(pos).getPosition(afwGeom.degrees)
                  for pos in tractPosList]
    ax.set_xlim(max(coord[0] for coord in skyPosList) + 1,
                min(coord[0] for coord in skyPosList) - 1)
    ax.set_ylim(min(coord[1] for coord in skyPosList) - 1,
                max(coord[1] for coord in skyPosList) + 1)
    ax.grid(ls=':',color='gray')
    ax.set_xlabel("RA (deg.)")
    ax.set_ylabel("Dec (deg.)")
    ax.set_title(title)
    return ax

def plot_protoDC2_region(ax):
    uddf_ra = [53.764, 52.486, 52.479, 53.771, 53.764]
    uddf_dec = [-27.533, -27.533, -28.667, -28.667, -27.533]

    wfd_ra = [52.25, 52.11, 58.02, 57.87, 52.25]
    wfd_dec = [-27.25, -32.25, -32.25, -27.25, -27.25]

    ax.errorbar(wfd_ra, wfd_dec, fmt='-', color='green',
                label='protoDC2 boundary')
    ax.errorbar(uddf_ra, uddf_dec, fmt='-', color='red',
                label='DDF boundary')


if __name__ == '__main__':
    repo = 'Run1.1_output'
    butler = dafPersist.Butler(repo)
    tracts = sorted([int(os.path.basename(x)) for x in glob.glob(os.path.join(repo, 'deepCoadd-results', 'merged', '*'))])
    ax = None
    for tract in tracts:
        skyMap = butler.get('deepCoadd_skyMap')
        ax = plotSkyMap(skyMap, tract=tract, title='', ax=ax)
    plot_protoDC2_region(ax)
    ax.set_xlim(60.5, 50)
    ax.set_ylim(-33.5, -26)
    plt.legend(loc=0)

    
