"""
Implementation of the data_source for the ORSO header.
"""

# author: Andrew R. McCluskey (arm61)

import enum
from typing import Optional, Dict, List, Union, Literal
from dataclasses import field, dataclass
import datetime

from .base import File, Header, ValueRange, Value, ValueVector, Person


@dataclass(repr=False)
class Experiment(Header):
    """A definition of the experiment performed."""
    title: str
    instrument: str
    date: datetime.datetime
    probe: Union[Literal["neutrons", "x-rays"]]
    facility: Optional[str] = None
    proposalID: Optional[str] = None
    doi: Optional[str] = None


@dataclass(repr=False)
class Sample(Header):
    """A description of the sample measured."""
    name: str
    type: Optional[str] = None
    composition: Optional[str] = None
    description: Optional[Union[str, List[str]]] = None
    environment: Optional[Union[str, List[str]]] = None
    sample_parameters: Optional[Dict] = field(
        default=None,
        metadata={
            'description':
                'Using keys for parameters and Value* objects for values.'
        })


# Enum does not work with yaml, if we really want this it has to be handle
# as special case.
#
# class Polarization(str, enum.Enum):
#     """
#     The first symbol indicates the magnetisation direction of the incident
#     beam. An optional second symbol indicates the direction of the scattered
#     beam, if a spin analyser is present.
#     """
#
#     unpolarized = "unpolarized"
#     p = "+"
#     m = "-"
#     mm = "--"
#     mp = "-+"
#     pm = "+-"
#     pp = "++"


@dataclass(repr=False)
class InstrumentSettings(Header):
    """Settings associated with the instrumentation."""
    incident_angle: Union[Value, ValueRange]
    wavelength: Union[Value, ValueRange]
    polarization: Optional[Union[Literal['unpolarized', 'p', 'm', 'mm', 'mp', 'pm', 'pp'],
                                 ValueVector]] = field(
        default='unpolarized',
        metadata={
            'description':
                'Polarization described as unpolarized/ p / m / pp / pm / mp / mm / vector'
        })
    configuration: Optional[str] = field(
        default=None,
        metadata={
            'description': 'half / full polarized | liquid_surface | etc'
        })

    __repr__ = Header._staggered_repr


@dataclass(repr=False)
class Measurement(Header):
    """The measurement elements for the header."""
    instrument_settings: InstrumentSettings
    data_files: List[Union[File, str]]
    references: Optional[List[Union[File, str]]] = None
    scheme: Optional[Union[
        Literal[
            "angle- and energy-dispersive",
            "angle-dispersive",
            "energy-dispersive",
        ]
    ]] = None

    __repr__ = Header._staggered_repr


@dataclass(repr=False)
class DataSource(Header):
    """The data_source object definition."""
    owner: Person
    experiment: Experiment
    sample: Sample
    measurement: Measurement
    _orso_optionals = []

    __repr__ = Header._staggered_repr
