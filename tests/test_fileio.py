"""
Tests for fileio module
"""

# author: Andrew R. McCluskey (arm61)

import unittest
import pathlib
from datetime import datetime
from orsopy import fileio


class TestOrso(unittest.TestCase):
    """
    Testing the Orso class.
    """
    def test_creation(self):
        """
        Creation of Orso object.
        """
        value = fileio.Orso(
            fileio.DataSource(
                fileio.Person('A Person', 'Some Uni'),
                fileio.Experiment('Experiment 1', 'ESTIA',
                                  datetime(2021, 7, 7, 16, 31, 10), 'neutron'),
                fileio.Sample('The sample')),
            fileio.Measurement(
                fileio.InstrumentSettings(
                    fileio.ValueScalar(4.0, 'deg'),
                    fileio.ValueRange(2., 12., 'angstrom')),
                [fileio.File('README.rst', None)]),
            fileio.Reduction(
                fileio.Software('orsopy', '0.0.1', 'macOS-10.15'),
                datetime(2021, 7, 14, 10, 10, 10),
                fileio.Person('Andrew McCluskey',
                              'European Spallation Source'),
                ['footprint', 'background']),
            [fileio.Column('q', '1/angstrom'),
             fileio.Column('R')])
        assert value.data_source.owner.name == 'A Person'
        assert value.measurement.data_files[0].file == 'README.rst'
        assert value.reduction.software.name == 'orsopy'
        assert value.column_description[0].quantity == 'q'

    def test_to_yaml(self):
        """
        Transformation to yaml of Orso class.
        """
        value = fileio.Orso(
            fileio.DataSource(
                fileio.Person('A Person', 'Some Uni'),
                fileio.Experiment('Experiment 1', 'ESTIA',
                                  datetime(2021, 7, 7, 16, 31, 10), 'neutron'),
                fileio.Sample('The sample')),
            fileio.Measurement(
                fileio.InstrumentSettings(
                    fileio.ValueScalar(4.0, 'deg'),
                    fileio.ValueRange(2., 12., 'angstrom')),
                [fileio.File('README.rst', None)]),
            fileio.Reduction(
                fileio.Software('orsopy', '0.0.1', 'macOS-10.15'),
                datetime(2021, 7, 14, 10, 10, 10),
                fileio.Person('Andrew McCluskey',
                              'European Spallation Source'),
                ['footprint', 'background']),
            [fileio.Column('q', '1/angstrom'),
             fileio.Column('R')])
        print(value.to_yaml())
        fna = pathlib.Path('README.rst')
        assert value.to_yaml() == 'data_source:\n  owner:\n    name: '\
            + 'A Person\n    affiliation: Some Uni\n  experiment:\n    '\
            + 'title: Experiment 1\n    instrument: ESTIA\n    timestamp: '\
            + '2021-07-07T16:31:10\n    probe: neutron\n  sample:\n    '\
            + 'identifier: The sample\nmeasurement:\n  '\
            + 'instrument_settings:\n    incident_angle:\n      '\
            + 'magnitude: 4.0\n      unit: deg\n    wavelength:\n      '\
            + 'min: 2.0\n      max: 12.0\n      unit: angstrom\n    '\
            + 'polarization: null\n  data_files:\n  - file: README.rst\n    '\
            + 'timestamp: '\
            + f'{datetime.fromtimestamp(fna.stat().st_mtime).isoformat()}\n'\
            + 'reduction:\n  software:\n    name: orsopy\n    '\
            + 'version: 0.0.1\n    platform: macOS-10.15\n  timestamp: '\
            + '2021-07-14T10:10:10\n  creator:\n    name: Andrew McCluskey\n'\
            + '    affiliation: European Spallation Source\n  corrections:\n'\
            + '  - footprint\n  - background\ncolumn_description:\n- '\
            + 'quantity: q\n  unit: 1/angstrom\n- quantity: R\n'
