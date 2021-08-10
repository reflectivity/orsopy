"""
Tests for fileio module
"""

# author: Andrew R. McCluskey (arm61)

import unittest
import pathlib
from datetime import datetime
from orsopy.fileio.orso import Orso, make_empty
from orsopy.fileio.data_source import DataSource, Experiment, Sample
from orsopy.fileio.measurement import Measurement, InstrumentSettings
from orsopy.fileio.reduction import Reduction, Software
from orsopy.fileio.creator import Creator
from orsopy.fileio.base import Person, ValueRange, ValueScalar, File, Column


class TestOrso(unittest.TestCase):
    """
    Testing the Orso class.
    """
    def test_creation(self):
        """
        Creation of Orso object.
        """
        now = datetime.now()
        value = Orso(
            Creator('A Person', 'Some Uni', 'my computer', now),
            DataSource(
                Person('A Person', 'Some Uni'),
                Experiment('Experiment 1', 'ESTIA',
                           datetime(2021, 7, 7, 16, 31, 10), 'neutron'),
                Sample('The sample')),
            Measurement(
                InstrumentSettings(ValueScalar(4.0, 'deg'),
                                   ValueRange(2., 12., 'angstrom')),
                [File('README.rst', None)]),
            Reduction(Software('orsopy', '0.0.1', 'macOS-10.15'),
                      datetime(2021, 7, 14, 10, 10, 10),
                      Person('Andrew McCluskey', 'European Spallation Source'),
                      ['footprint', 'background']),
            [Column('q', '1/angstrom'), Column('R')], 0)
        assert value.data_source.owner.name == 'A Person'
        assert value.measurement.data_files[0].file == 'README.rst'
        assert value.reduction.software.name == 'orsopy'
        assert value.column_description[0].quantity == 'q'
        assert value.data_set == 0

    def test_to_yaml(self):
        """
        Transformation to yaml of Orso class.
        """
        now = datetime.now()
        value = Orso(
            Creator('A Person', 'Some Uni', 'my computer', now),
            DataSource(
                Person('A Person', 'Some Uni'),
                Experiment('Experiment 1', 'ESTIA',
                           datetime(2021, 7, 7, 16, 31, 10), 'neutron'),
                Sample('The sample')),
            Measurement(
                InstrumentSettings(ValueScalar(4.0, 'deg'),
                                   ValueRange(2., 12., 'angstrom')),
                [File('README.rst', None)]),
            Reduction(Software('orsopy', '0.0.1', 'macOS-10.15'),
                      datetime(2021, 7, 14, 10, 10, 10),
                      Person('Andrew McCluskey', 'European Spallation Source'),
                      ['footprint', 'background']),
            [Column('q', '1/angstrom'), Column('R')], 0)
        print(value.to_yaml())
        fna = pathlib.Path('README.rst')
        assert value.to_yaml() == (
            'creator:\n  name: A Person\n  affiliation: Some Uni\n  '
            'computer: my computer\n  time: ' + now.isoformat() + '\n'
            'data_source:\n  owner:\n    name: '
            'A Person\n    affiliation: Some Uni\n  experiment:\n    '
            'title: Experiment 1\n    instrument: ESTIA\n    timestamp: '
            '2021-07-07T16:31:10\n    probe: neutron\n  sample:\n    '
            'identifier: The sample\nmeasurement:\n  '
            'instrument_settings:\n    incident_angle:\n      '
            'magnitude: 4.0\n      unit: deg\n    wavelength:\n      '
            'min: 2.0\n      max: 12.0\n      unit: angstrom\n    '
            'polarization: null\n  data_files:\n  - file: README.rst\n    '
            'timestamp: '
            f'{datetime.fromtimestamp(fna.stat().st_mtime).isoformat()}\n'
            'reduction:\n  software:\n    name: orsopy\n    '
            'version: 0.0.1\n    platform: macOS-10.15\n  timestamp: '
            '2021-07-14T10:10:10\n  creator:\n    name: Andrew McCluskey\n'
            '    affiliation: European Spallation Source\n  corrections:\n'
            '  - footprint\n  - background\ncolumn_description:\n- '
            'quantity: q\n  unit: 1/angstrom\n- quantity: R\n'
        )

    def test_creation_data_set1(self):
        """
        Creation of Orso object with a non-zero data_set.
        """
        now = datetime.now()
        value = Orso(
            Creator('A Person', 'Some Uni', 'my computer', now),
            DataSource(
                Person('A Person', 'Some Uni'),
                Experiment('Experiment 1', 'ESTIA',
                           datetime(2021, 7, 7, 16, 31, 10), 'neutron'),
                Sample('The sample')),
            Measurement(
                InstrumentSettings(ValueScalar(4.0, 'deg'),
                                   ValueRange(2., 12., 'angstrom')),
                [File('README.rst', None)]),
            Reduction(Software('orsopy', '0.0.1', 'macOS-10.15'),
                      datetime(2021, 7, 14, 10, 10, 10),
                      Person('Andrew McCluskey', 'European Spallation Source'),
                      ['footprint', 'background']),
            [Column('q', '1/angstrom'), Column('R')], 1)
        assert value.data_source.owner.name == 'A Person'
        assert value.measurement.data_files[0].file == 'README.rst'
        assert value.reduction.software.name == 'orsopy'
        assert value.column_description[0].quantity == 'q'
        assert value.data_set == 1

    def test_to_yaml_data_set1(self):
        """
        Transformation to yaml of Orso class with a non-zero data_set.
        """
        value = Orso(
            Creator(
                'A Person', 'Some Uni', 'my computer',
                datetime(2021, 7, 14, 10, 10, 10)
            ),
            DataSource(
                Person('A Person', 'Some Uni'),
                Experiment('Experiment 1', 'ESTIA',
                           datetime(2021, 7, 7, 16, 31, 10), 'neutron'),
                Sample('The sample')),
            Measurement(
                InstrumentSettings(ValueScalar(4.0, 'deg'),
                                   ValueRange(2., 12., 'angstrom')),
                [File('README.rst', None)]),
            Reduction(Software('orsopy', '0.0.1', 'macOS-10.15'),
                      datetime(2021, 7, 14, 10, 10, 10),
                      Person('Andrew McCluskey', 'European Spallation Source'),
                      ['footprint', 'background']),
            [Column('q', '1/angstrom'), Column('R')], 1)
        print(value.to_yaml())
        fna = pathlib.Path('README.rst')
        assert value.to_yaml() == (
            'creator:\n  name: A Person\n  affiliation: Some Uni\n  '
            'computer: my computer\n  time: 2021-07-14T10:10:10\n'
            'data_source:\n  owner:\n    name: '
            'A Person\n    affiliation: Some Uni\n  experiment:\n    '
            'title: Experiment 1\n    instrument: ESTIA\n    timestamp: '
            '2021-07-07T16:31:10\n    probe: neutron\n  sample:\n    '
            'identifier: The sample\nmeasurement:\n  '
            'instrument_settings:\n    incident_angle:\n      '
            'magnitude: 4.0\n      unit: deg\n    wavelength:\n      '
            'min: 2.0\n      max: 12.0\n      unit: angstrom\n    '
            'polarization: null\n  data_files:\n  - file: README.rst\n    '
            'timestamp: '
            f'{datetime.fromtimestamp(fna.stat().st_mtime).isoformat()}\n'
            'reduction:\n  software:\n    name: orsopy\n    '
            'version: 0.0.1\n    platform: macOS-10.15\n  timestamp: '
            '2021-07-14T10:10:10\n  creator:\n    name: Andrew McCluskey\n'
            '    affiliation: European Spallation Source\n  corrections:\n'
            '  - footprint\n  - background\ncolumn_description:\n- '
            'quantity: q\n  unit: 1/angstrom\n- quantity: R\ndata_set: 1\n'
        )


class TestFunctions(unittest.TestCase):
    """
    Tests for functionality in the Orso module.
    """
    def test_make_empty(self):
        """
        Creation of the empty Orso object.
        """
        empty = make_empty()
        assert issubclass(empty.__class__, Orso)
        assert empty.data_source.owner is None
        assert empty.data_source.experiment.title is None
        assert empty.data_source.experiment.instrument is None
        assert empty.data_source.experiment.timestamp is None
        assert empty.data_source.experiment.probe is None
        assert empty.data_source.sample.identifier is None
        assert empty.measurement.instrument_settings.incident_angle is None
        assert empty.measurement.instrument_settings.wavelength is None
        assert empty.measurement.data_files is None
        assert empty.reduction.software.name is None
        assert empty.reduction.software.version is None
        assert empty.reduction.software.platform is None
        assert empty.reduction.timestamp is None
        assert empty.reduction.creator is None
        assert empty.reduction.corrections is None
        assert empty.column_description is None
        assert empty.data_set is None

    def test_empty_to_yaml(self):
        """
        Checking yaml string form empty Orso object.
        """
        empty = make_empty()
        assert empty.to_yaml() == (
            'creator:\n  name: null\n  affiliation: null\n  '
            'computer: null\n  time: null\n'
            'data_source:\n  owner: null\n  '
            'experiment:\n    title: null\n    instrument: null\n    '
            'timestamp: null\n    probe: null\n  sample:\n    '
            'identifier: null\nmeasurement:\n  '
            'instrument_settings:\n    incident_angle: null\n    '
            'wavelength: null\n    polarization: null\n  '
            'data_files: null\nreduction:\n  software:\n    '
            'name: null\n    version: null\n    platform: null\n  '
            'timestamp: null\n  creator: null\n  corrections: null\n'
            'column_description: null\ndata_set: null\n'
        )
