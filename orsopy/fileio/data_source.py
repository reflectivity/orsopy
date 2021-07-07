"""
Implementation of the data_source for the ORSO header.
"""

# author: Andrew R. McCluskey (arm61)

from typing import Optional, Dict
from dataclasses import field, dataclass
import datetime
from orsopy.fileio.base import Header, Person


@dataclass
class Experiment(Header):
    """A definition of the experiment performed."""
    title: str
    instrument: str
    timestamp: datetime.datetime
    probe: str
    facility: Optional[str] = field(default=None)
    proposalID: Optional[str] = field(default=None)
    doi: Optional[str] = field(default=None)
    _orso_optionals = ['facility', 'proposalID', 'doi']


@dataclass
class Sample(Header):
    """A description of the sample measured."""
    identifier: str
    type: Optional[str] = field(default=None)
    composition: Optional[str] = field(default=None)
    description: Optional[str] = field(default=None)
    environment: Optional[str] = field(default=None)
    sample_parameters: Optional[Dict] = field(
        default=None,
        metadata={
            'description':
            'Using keys for parameters and Value* objects for values.'
        })
    _orso_optionals = [
        'type', 'composition', 'description', 'environment',
        'sample_parameters']


@dataclass
class DataSource(Header):
    """The data_source object definition."""
    owner: Person
    experiment: Experiment
    sample: Sample
    _orso_optionals = []
