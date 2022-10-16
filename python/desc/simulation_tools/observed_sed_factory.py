import os
from collections import defaultdict
import yaml
import numpy as np
import pandas as pd
from astropy.cosmology import FlatLambdaCDM
import galsim


class ObservedSedFactory:
    _clight = 3e8  # m/s
    _to_W_per_Hz = 4.4659e13  # conversion of cosmoDC2 tophat Lnu values to W/Hz
    def __init__(self, config):
        # Get wavelength and frequency bin boundaries.
        bins = config['SED_models']['tophat']['bins']
        wl0 = [_[0] for _ in bins]
        wl0.append(bins[-1][0] + bins[-1][1])
        wl0 = 0.1*np.array(wl0)
        self.wl = np.array(wl0)
        self.nu = self._clight/(self.wl*1e-9)  # frequency in Hz

        # Create a FlatLambdaCDM cosmology from a dictionary of input
        # parameters.  This code is based on/borrowed from
        # https://github.com/LSSTDESC/gcr-catalogs/blob/master/GCRCatalogs/cosmodc2.py#L128
        cosmo_astropy_allowed = FlatLambdaCDM.__init__.__code__.co_varnames[1:]
        cosmo_astropy = {k: v for k, v in config['Cosmology'].items()
                         if k in cosmo_astropy_allowed}
        self.cosmology = FlatLambdaCDM(**cosmo_astropy)

    def dl(self, z):
        """
        Return the luminosity distance in units of meters.
        """
        # Conversion factor from Mpc to meters (obtained from pyccl).
        MPC_TO_METER = 3.085677581491367e+22
        return self.cosmology.luminosity_distance(z).value*MPC_TO_METER

    def create(self, Lnu, redshift_hubble, redshift, delta_wl=0.001):
        # Compute Llambda in units of W/nm
        Llambda = (Lnu*self._to_W_per_Hz*(self.nu[:-1] - self.nu[1:])
                   /(self.wl[1:] - self.wl[:-1]))

        # Fill the arrays for the galsim.LookupTable. A non-zero
        # delta_wl is used to avoid repeated abscissa values.  Prepend
        # a zero-valued bin down to zero wl to handle redshifts z > 2.
        my_wl = [0, self.wl[0] - delta_wl]
        my_Llambda = [0, 0]
        for i in range(len(Llambda)):
            my_wl.extend((self.wl[i], self.wl[i+1] - delta_wl))
            my_Llambda.extend((Llambda[i], Llambda[i]))

        # Convert to (unredshifted) flux given redshift_hubble.
        flambda = np.array(my_Llambda)/(4.0*np.pi*self.dl(redshift_hubble)**2)

        # Convert to cgs units
        flambda *= (1e7/1e4)  # (erg/joule)*(m**2/cm**2)

        # Create the lookup table.
        lut = galsim.LookupTable(my_wl, flambda, interpolant='nearest')

        # Create the SED object and apply redshift.
        sed = galsim.SED(lut, wave_type='nm', flux_type='flambda')\
                    .atRedshift(redshift)
        return sed


class AB_mag:
    """
    Convert flux to AB magnitude for a set of bandpasses.
    """
    def __init__(self, bps):
        ab_sed = galsim.SED(lambda nu : 3631e-23, wave_type='nm',
                            flux_type='fnu')
        self.ab_fluxes = {band: ab_sed.calculateFlux(bp) for
                          band, bp in bps.items()}
    def __call__(self, flux, band):
        return -2.5*np.log10(flux/self.ab_fluxes[band])


if __name__ == '__main__':
    skycatalog_root = '/global/cscratch1/sd/jrbogart/desc/skycatalogs/new_SEDS'
    skycatalog_file = os.path.join(skycatalog_root, 'skyCatalog.yaml')

    with open(skycatalog_file) as fobj:
        config = yaml.safe_load(fobj)

    sed_factory = ObservedSedFactory(config)

    # Read in LSST bandpasses
    bps = {}
    for band in 'ugrizy':
        bp_file = os.path.join(os.environ['RUBIN_SIM_DATA_DIR'], 'throughputs',
                               'baseline', f'total_{band}.dat')
        bps[band] = galsim.Bandpass(bp_file, wave_type='nm').thin()

    # Read in parquet file with galaxy data
    galaxy_file = os.path.join(skycatalog_root, 'galaxy_9556.parquet')
    df0 = pd.read_parquet(galaxy_file)

    ab_mag = AB_mag(bps)

    data = defaultdict(list)
    components = ('sed_val_bulge', 'sed_val_disk', 'sed_val_knots')
    for i, row in df0.iterrows():
        print(i, len(df0))
        seds = [sed_factory.create(row[component], row.redshift_hubble,
                                   row.redshift) for component in components]
        data['galaxy_id'].append(row.galaxy_id)
        for band, bp in bps.items():
            flux = sum(sed.calculateFlux(bp) for sed in seds)
            data[f'lsst_flux_{band}'].append(flux)
            data[f'mag_{band}'].append(ab_mag(flux, band))
    df = pd.DataFrame(data)
    df.to_parquet('galaxy_flux_mag_9556.parquet')
