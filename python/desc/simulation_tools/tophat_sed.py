import numpy as np
import pandas as pd
from GCR import GCRQuery
import GCRCatalogs
import pyccl as ccl

__all__ = ['GalaxyTopHatSEDFactory']


class TopHatSED:
    """
    Function to represent the tophat SEDs used in cosmoDC2.  In each
    of the tophat bands, Fnu has a single value over the entire
    wavelength range of the band.
    """
    def __init__(self, wls, Fnus):
        self.wls = wls
        self.Fnus = Fnus

    def fnu(self, wl):
        """Return Fnu (W/Hz/m**2) as a function of wl (nm)."""
        if wl < self.wls[0] or wl > self.wls[-1]:
            raise ValueError(f'Requested wavelength {wl} is outside the '
                             f'valid range, ({self.wls[0]}, {self.wls[-1]}), '
                             'for this SED.')
        index = np.where(wl >= self.wls)[0][-1]
        return self.Fnus[index]

    def flambda(self, wl):
        """Return Flambda (W/nm/m**2) as function of wl (nm)."""
        # Compute flambda = clight*Fnu/lambda**2 in SI units.
        flambda = ccl.physical_constants.CLIGHT*self.fnu(wl)/(wl*1e-9)**2
        # Explicitly convert from W/m/m**2 to W/nm/m**2.
        return flambda/1e9


class GalaxyTopHatSEDFactory:
    def __init__(self, galaxy_catalog='cosmoDC2_v1.1.4_image'):
        self.catalog = GCRCatalogs.load_catalog(galaxy_catalog)
        cat_cosmo = self.catalog.cosmology
        self.cosmo = ccl.Cosmology(Omega_c=cat_cosmo.Om0,
                                   Omega_b=cat_cosmo.Ob0,
                                   h=cat_cosmo.h,
                                   sigma8=cat_cosmo.sigma8,
                                   n_s=cat_cosmo.n_s)
        self._read_tophat_columns()
        self._hp_cache = dict()

    def dl(self, redshift_hubble):
        """
        Luminosity distance (meters) as a function of Hubble flow redshift.
        """
        ascale = 1/(1 + redshift_hubble)
        return (ccl.luminosity_distance(self.cosmo, ascale)
                *ccl.physical_constants.MPC_TO_METER)

    def _read_tophat_columns(self):
        """
        Read in the SED tophat column names to get the wavelength
        info for each tophat band.
        """
        wls = []
        widths = []
        columns = []
        for item in self.catalog.list_all_quantities():
            if item.startswith('sed'):
                tokens = item.split('_')
                if len(tokens) != 3:
                    continue
                wls.append(float(tokens[1]))
                widths.append(float(tokens[2]))
                columns.append(item)
        index = np.argsort(wls)
        self.wls = np.array(wls)[index]
        self.columns = np.array(columns)[index]
        # Append the upper bound of the last wl bin.
        last_width = np.array(widths)[index][-1]
        self.wls = np.append(self.wls, [self.wls[-1] + last_width])
        self.gcr_columns = (['redshift_true', 'galaxy_id']
                            + ['_'.join((_, 'bulge_no_host_extinction'))
                               for _ in self.columns]
                            + ['_'.join((_, 'disk_no_host_extinction'))
                               for _ in self.columns] )

    def create(self, galaxy_id, healpix,
               component_type='bulge_no_host_extinction',
               one_maggy=4.3442e13):
        """
        Create a TopHatSED function object that returns Flambda
        (W/nm/m**2) for the specified galaxy as a function of
        wavelength (nm).
        """
        if healpix not in self._hp_cache:
            native_filters = [f'healpix_pixel=={healpix}']
            data = self.catalog.get_quantities(self.gcr_columns,
                                               native_filters=native_filters)
            self._hp_cache[healpix] = pd.DataFrame(data=data)

        row = self._hp_cache[healpix].query(f'galaxy_id=={galaxy_id}').iloc[0]

        # Convert GCR Lnu values from maggies to W/Hz.
        Lnus = one_maggy*np.array([row['_'.join((_, component_type))]
                                    for _ in self.columns])
        Fnus = Lnus/4/np.pi/self.dl(row['redshift_true'])**2
        wls = self.wls/10  # convert to nm
        return TopHatSED(wls, Fnus)
