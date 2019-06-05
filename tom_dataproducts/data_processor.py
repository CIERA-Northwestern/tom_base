import re
import magic

from astropy.time import Time, TimezoneInfo
from astropy import units
from astropy.io import fits, ascii
from astropy.wcs import WCS
from specutils import Spectrum1D
import numpy as np

from tom_observations.facility import get_service_class
from .exceptions import InvalidFileFormatException


class DataProcessor():

    def process_spectroscopy(self, data_product, facility):
        filetype = magic.from_file(data_product.data.path, mime=True)
        if filetype == 'image/fits':
            return self._process_spectrum_from_fits(data_product, facility)
        # TODO: process into Spectrum1D file
        elif filetype == 'text/plain':
            return self._process_spectrum_from_plaintext(data_product, facility)
        else:
            raise InvalidFileFormatException('Unsupported file type')

    def _process_spectrum_from_fits(self, data_product, facility):
        # https://specutils.readthedocs.io/en/doc-testing/specutils/read_fits.html
        flux, header = fits.getdata(data_product.data.path, header=True)

        # hdu = hlist[0]
        dim = len(flux.shape)
        if dim == 3:
            flux = flux[0, 0, :]
        elif flux.shape[0] == 2:
            flux = flux[0, :]
        header['CUNIT1'] = 'Angstrom'
        wcs = WCS(header=header)
        flux = flux * get_service_class(facility)().get_flux_constant()

        spectrum = Spectrum1D(flux=flux, wcs=wcs)

        return spectrum

    def _process_spectrum_from_plaintext(self, data_product, facility):
        # TODO: Move spectral axis units to facility?
        data = ascii.read(data_product.data.path)
        spectral_axis = np.array(data['wavelength']) * units.Angstrom
        flux = np.array(data['flux']) * get_service_class(facility)().get_flux_constant()
        spectrum = Spectrum1D(flux=flux, spectral_axis=spectral_axis)

        return spectrum

    def process_photometry(self, data_product):
        filetype = magic.from_file(data_product.data.path, mime=True)
        if filetype == 'text/plain':
            return self.process_photometry_from_plaintext(data_product)
        else:
            raise InvalidFileFormatException('Unsupported file type')

    def process_photometry_from_plaintext(self, data_product):
        photometry = {}
        with data_product.data.file.open() as f:
            for line in f:
                photometry_datum = [datum.strip() for datum in re.split(',', line.decode('UTF-8'))]
                time = Time(float(photometry_datum[0]), format='mjd')
                utc = TimezoneInfo(utc_offset=0*units.hour)
                time.format = 'datetime'
                value = {
                    'magnitude': photometry_datum[2],
                    'filter': photometry_datum[1],
                    'error': photometry_datum[3]
                }
                photometry[time.to_datetime(timezone=utc)] = value

        return photometry
