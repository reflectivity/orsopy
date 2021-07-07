"""
Tests for fileio.measurement module
"""

# author: Andrew R. McCluskey (arm61)

import unittest
import pathlib
from datetime import datetime
from orsopy import fileio


class TestInstrumentSettings(unittest.TestCase):
    """
    Tests for the InstrumentSettings class.
    """
    def test_creation(self):
        """
        Creation with minimal settings.
        """
        value = fileio.InstrumentSettings(
            fileio.ValueScalar(4., 'deg'),
            fileio.ValueRange(2., 12., 'angstrom'),
        )
        assert value.incident_angle.magnitude == 4.
        assert value.incident_angle.unit == 'deg'
        assert value.wavelength.min == 2.
        assert value.wavelength.max == 12.
        assert value.wavelength.unit == 'angstrom'
        assert value.polarization is None
        assert value.configuration is None

    def test_to_yaml(self):
        """
        Transformation to yaml with minimal set.
        """
        value = fileio.InstrumentSettings(
            fileio.ValueScalar(4., 'deg'),
            fileio.ValueRange(2., 12., 'angstrom'),
        )
        assert value.to_yaml() == 'incident_angle:\n  magnitude: '\
            + '4.0\n  unit: deg\nwavelength:\n  min: 2.0\n  '\
            + 'max: 12.0\n  unit: angstrom\npolarization: null\n'

    def test_creation_config_and_polarization(self):
        """
        Creation with optional items.
        """
        value = fileio.InstrumentSettings(fileio.ValueScalar(4., 'deg'),
                                          fileio.ValueRange(
                                              2., 12., 'angstrom'),
                                          polarization='p',
                                          configuration='liquid surface')
        assert value.incident_angle.magnitude == 4.
        assert value.incident_angle.unit == 'deg'
        assert value.wavelength.min == 2.
        assert value.wavelength.max == 12.
        assert value.wavelength.unit == 'angstrom'
        assert value.polarization == 'p'
        assert value.configuration == 'liquid surface'

    def test_to_yaml_config_and_polarization(self):
        """
        Transformation to yaml with optional items.
        """
        value = fileio.InstrumentSettings(fileio.ValueScalar(4., 'deg'),
                                          fileio.ValueRange(
                                              2., 12., 'angstrom'),
                                          polarization='p',
                                          configuration='liquid surface')
        assert value.to_yaml() == 'incident_angle:\n  magnitude: '\
            + '4.0\n  unit: deg\nwavelength:\n  min: 2.0\n  '\
            + 'max: 12.0\n  unit: angstrom\npolarization: p\n'\
            + 'configuration: liquid surface\n'


class TestMeasurement(unittest.TestCase):
    """
    Tests for the Measurement class.
    """
    def test_creation(self):
        """
        Creation with minimal set.
        """
        value = fileio.Measurement(
            fileio.InstrumentSettings(
                fileio.ValueScalar(4., 'deg'),
                fileio.ValueRange(2., 12., 'angstrom'),
            ), [
                fileio.File(
                    str(pathlib.Path().resolve().joinpath("README.rst")), None)
            ])
        assert value.instrument_settings.incident_angle.magnitude == 4.0
        assert value.instrument_settings.incident_angle.unit == 'deg'
        assert value.instrument_settings.wavelength.min == 2.0
        assert value.instrument_settings.wavelength.max == 12.0
        assert value.instrument_settings.wavelength.unit == 'angstrom'
        assert value.data_files[0].file == str(
            pathlib.Path().resolve().joinpath("README.rst"))
        assert value.data_files[0].timestamp == datetime.fromtimestamp(
            pathlib.Path('README.rst').stat().st_mtime)

    def test_to_yaml(self):
        """
        Transform to yaml with minimal set.
        """
        value = fileio.Measurement(
            fileio.InstrumentSettings(
                fileio.ValueScalar(4., 'deg'),
                fileio.ValueRange(2., 12., 'angstrom'),
            ), [
                fileio.File(
                    str(pathlib.Path().resolve().joinpath("README.rst")), None)
            ])
        fname = pathlib.Path('README.rst')
        assert value.to_yaml() == 'instrument_settings:\n  incident_angle:'\
            + '\n    magnitude: 4.0\n    unit: deg\n  wavelength:\n    min: '\
            + '2.0\n    max: 12.0\n    unit: angstrom\n  polarization: '\
            + 'null\ndata_files:\n- file: '\
            + f'{str(fname.absolute())}\n  timestamp: '\
            + f'{datetime.fromtimestamp(fname.stat().st_mtime).isoformat()}\n'

    def test_creation_optionals(self):
        """
        Creation with optionals.
        """
        value = fileio.Measurement(
            fileio.InstrumentSettings(
                fileio.ValueScalar(4., 'deg'),
                fileio.ValueRange(2., 12., 'angstrom'),
            ), [
                fileio.File(
                    str(pathlib.Path().resolve().joinpath("README.rst")), None)
            ], [
                fileio.File(
                    str(pathlib.Path().resolve().joinpath("AUTHORS.rst")),
                    None)
            ])
        assert value.instrument_settings.incident_angle.magnitude == 4.0
        assert value.instrument_settings.incident_angle.unit == 'deg'
        assert value.instrument_settings.wavelength.min == 2.0
        assert value.instrument_settings.wavelength.max == 12.0
        assert value.instrument_settings.wavelength.unit == 'angstrom'
        assert value.data_files[0].file == str(
            pathlib.Path().resolve().joinpath("README.rst"))
        assert value.data_files[0].timestamp == datetime.fromtimestamp(
            pathlib.Path('README.rst').stat().st_mtime)
        assert value.reference_data_files[0].file == str(
            pathlib.Path().resolve().joinpath("AUTHORS.rst"))
        assert value.reference_data_files[
            0].timestamp == datetime.fromtimestamp(
                pathlib.Path('AUTHORS.rst').stat().st_mtime)

    def test_to_yaml_optionals(self):
        """
        Transform to yaml with optionals.
        """
        value = fileio.Measurement(
            fileio.InstrumentSettings(
                fileio.ValueScalar(4., 'deg'),
                fileio.ValueRange(2., 12., 'angstrom'),
            ), [
                fileio.File(
                    str(pathlib.Path().resolve().joinpath("README.rst")), None)
            ], [
                fileio.File(
                    str(pathlib.Path().resolve().joinpath("AUTHORS.rst")),
                    None)
            ], 'energy-dispersive')
        fname = pathlib.Path('README.rst')
        gname = pathlib.Path('AUTHORS.rst')
        assert value.to_yaml() == 'instrument_settings:\n  incident_angle:'\
            + '\n    magnitude: 4.0\n    unit: deg\n  wavelength:\n    min: '\
            + '2.0\n    max: 12.0\n    unit: angstrom\n  polarization: '\
            + 'null\ndata_files:\n- file: '\
            + f'{str(fname.absolute())}\n  timestamp: '\
            + f'{datetime.fromtimestamp(fname.stat().st_mtime).isoformat()}\n'\
            + 'reference_data_files:\n- file: '\
            + f'{str(gname.absolute())}\n  timestamp: '\
            + f'{datetime.fromtimestamp(gname.stat().st_mtime).isoformat()}\n'\
            + 'scheme: energy-dispersive\n'
