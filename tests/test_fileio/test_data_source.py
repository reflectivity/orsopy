"""
Tests for fileio.data_source module
"""

# author: Andrew R. McCluskey (arm61)

import unittest
from datetime import datetime
from orsopy.fileio import data_source, base


class TestExperiment(unittest.TestCase):
    """
    Testing the Experiment class.
    """
    def test_creation(self):
        """
        Creation with minimal set.
        """
        value = data_source.Experiment('My First Experiment',
                                       'A Lab Instrument',
                                       datetime(1992, 7, 14, 10, 10,
                                                10), 'X-ray')
        assert value.title == "My First Experiment"
        assert value.instrument == 'A Lab Instrument'
        assert value.date == datetime(1992, 7, 14, 10, 10, 10)
        assert value.probe == 'X-ray'
        assert value.facility is None
        assert value.proposalID is None
        assert value.doi is None

    def test_to_yaml(self):
        """
        Transformation to yaml with minimal set.
        """
        value = data_source.Experiment('My First Experiment',
                                       'A Lab Instrument',
                                       datetime(1992, 7, 14, 10, 10,
                                                10), 'X-ray')
        assert value.to_yaml() == 'title: My First Experiment\n'\
            + 'instrument: A Lab Instrument\ndate: 1992-07-14T'\
            + '10:10:10\nprobe: X-ray\n'

    def test_creation_optionals(self):
        """
        Creation with optionals.
        """
        value = data_source.Experiment('My First Neutron Experiment',
                                       'TAS8',
                                       datetime(1992, 7, 14, 10, 10, 10),
                                       'neutron',
                                       facility='Risoe',
                                       proposalID='abc123',
                                       doi='10.0000/abc1234')
        assert value.title == "My First Neutron Experiment"
        assert value.instrument == 'TAS8'
        assert value.date == datetime(1992, 7, 14, 10, 10, 10)
        assert value.probe == 'neutron'
        assert value.facility == 'Risoe'
        assert value.proposalID == 'abc123'
        assert value.doi == '10.0000/abc1234'

    def test_to_yaml_optionals(self):
        """
        Transformation to yaml with optionals.
        """
        value = data_source.Experiment('My First Neutron Experiment',
                                       'TAS8',
                                       datetime(1992, 7, 14, 10, 10, 10),
                                       'neutron',
                                       facility='Risoe',
                                       proposalID='abc123',
                                       doi='10.0000/abc1234')
        assert value.to_yaml() == 'title: My First Neutron Experiment\n'\
            + 'instrument: TAS8\ndate: 1992-07-14T'\
            + '10:10:10\nprobe: neutron\nfacility: Risoe\nproposalID: '\
            + 'abc123\ndoi: 10.0000/abc1234\n'


class TestSample(unittest.TestCase):
    """
    Testing for the Sample class.
    """
    def test_creation(self):
        """
        Creation with a minimal set.
        """
        value = data_source.Sample('A Perfect Sample')
        assert value.identifier == 'A Perfect Sample'
        assert value.type is None
        assert value.composition is None
        assert value.description is None
        assert value.environment is None

    def test_to_yaml(self):
        """
        Transformation to yaml with a minimal set.
        """
        value = data_source.Sample('A Perfect Sample')
        assert value.to_yaml() == 'identifier: A Perfect Sample\n'

    def test_creation_optionals(self):
        """
        Creation with a optionals.
        """
        value = data_source.Sample(
            'A Perfect Sample',
            type='solid/gas',
            composition='Si | SiO2(20 A) | Fe(200 A) | air(beam side)',
            description='The sample is without flaws',
            environment='Temperature cell')
        assert value.identifier == 'A Perfect Sample'
        assert value.type == 'solid/gas'
        assert value.composition == 'Si | SiO2(20 A) | '\
            + 'Fe(200 A) | air(beam side)'
        assert value.description == 'The sample is without flaws'
        assert value.environment == 'Temperature cell'

    def test_to_yaml_optionals(self):
        """
        Transformation to yaml with optionals.
        """
        value = data_source.Sample(
            'A Perfect Sample',
            type='solid/gas',
            composition='Si | SiO2(20 A) | Fe(200 A) | air(beam side)',
            description='The sample is without flaws',
            environment='Temperature cell')
        assert value.to_yaml() == 'identifier: A Perfect Sample\ntype: '\
            + 'solid/gas\ncomposition: Si | SiO2(20 A) | Fe(200 A) | air'\
            + '(beam side)\ndescription: The sample is without flaws\n'\
            + 'environment: Temperature cell\n'


class TestDataSource(unittest.TestCase):
    """
    Tests for the DataSource class.
    """
    def test_creation(self):
        """
        Creation with only default.
        """
        value = data_source.DataSource(
            base.Person('A Person', 'Some Uni'),
            data_source.Experiment('My First Experiment', 'A Lab Instrument',
                                   datetime(1992, 7, 14, 10, 10, 10), 'X-ray'),
            data_source.Sample('A Perfect Sample'))
        assert value.owner.name == 'A Person'
        assert value.owner.affiliation == 'Some Uni'
        assert value.experiment.title == 'My First Experiment'
        assert value.experiment.instrument == 'A Lab Instrument'
        assert value.experiment.date == datetime(1992, 7, 14, 10, 10, 10)
        assert value.experiment.probe == 'X-ray'
        assert value.sample.identifier == 'A Perfect Sample'
