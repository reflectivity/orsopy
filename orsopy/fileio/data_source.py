"""
Implementation of the data_source for the ORSO header.
"""
from dataclasses import field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

import yaml

from .base import File, Header, Person, Value, ValueRange, ValueVector, orsodataclass

# typing stuff introduced in python 3.8
try:
    from typing import Literal
except ImportError:
    from .typing_backport import Literal


@orsodataclass
class Experiment(Header):
    """
    A definition of the experiment performed.

    :param title: Proposal or project title.
    :param instrument: Reflectometer identifier.
    :param start_date: Start date for the experiment.
    :param probe: Radiation probe, either :code:`'neutron'` or
        :code:`'x-ray'`.
    :param facility: Facility where the experiment was performed.
    :param proposalID: Identifier for experiment at a facility.
    :param doi: Digital object identifier for the experiment, possibly
        provided by the facility.
    """

    title: str
    instrument: str
    start_date: datetime
    probe: Literal["neutron", "x-ray"]
    facility: Optional[str] = None
    proposalID: Optional[str] = None
    doi: Optional[str] = None


@orsodataclass
class Sample(Header):
    """
    A description of the sample measured.

    :param name: An identified for the individual sample or the subject and
        state being measured.
    :param category: Simple sample description, front (beam side) / back,
        each side should be one of :code:`'solid/liquid'`,
        :code:`'liquid/solid'`, :code:`'gas/liquid'`,
        :code:`'liquid/liquid'`, :code:`'solid/gas'`, :code:`'gas/solid'`.
    :param composition: Notes on the nominal composition of the sample e.g.
        :code:`Si | SiO2 (20 angstrom) | Fe (200 angstrom) |
        air (beam side)`.
    :param description: Further details of the sample, e.g. size.
    :param environment: Name of the sample environment device(s).
    :param sample_parameters: Dictionary of sample parameters.
    """

    name: str
    category: Optional[str] = None
    composition: Optional[str] = None
    description: Optional[str] = None
    environment: Optional[List[str]] = None
    sample_parameters: Optional[Dict] = field(
        default=None, metadata={"description": "Using keys for parameters and Value* objects for values."}
    )


class Polarization(str, Enum):
    """
    The first symbol indicates the magnetisation direction of the incident
    beam. An optional second symbol indicates the direction of the scattered
    beam, if a spin analyser is present.
    """

    unpolarized = "unpolarized"
    # half polairzed states
    po = "po"
    mo = "mo"
    op = "op"
    om = "om"
    # full polarization analysis
    mm = "mm"
    mp = "mp"
    pm = "pm"
    pp = "pp"

    def yaml_representer(self, dumper: yaml.Dumper):
        output = self.value
        return dumper.represent_str(output)


@orsodataclass
class InstrumentSettings(Header):
    """
    Settings associated with the instrumentation.

    :param incident_angle: Angle (range) of incidence.
    :param wavelength: Neutron/x-ray wavelenght (range).
    :param polarization: Radiation polarization as one of
        :code:`'unpolarized'`, :code:`'p'`, :code:`'m'`, :code:`'pp'`,
        :code:`'pm'`, :code:`'mp'`, :code:`'mm'`, or a
        :py:class:`orsopy.fileio.base.ValueVector`.
    :param configuration: Description of the instreument configuration (full
        polarized/liquid surface/etc).
    """

    incident_angle: Union[Value, ValueRange]
    wavelength: Union[Value, ValueRange]
    polarization: Optional[Union[Polarization, ValueVector]] = field(
        default=None,
        metadata={
            "description": "Polarization described as unpolarized/ po/ mo / op / om / pp / pm / mp / mm / vector"
        },
    )
    configuration: Optional[str] = field(
        default=None, metadata={"description": "half / full polarized | liquid_surface | etc"}
    )

    __repr__ = Header._staggered_repr


@orsodataclass
class Measurement(Header):
    """
    The measurement elements for the header.

    :param instrument_settings: Instrumentation details.
    :param data_files: Raw data files produced in the measurement.
    :param references: Raw reference files used in the reduction.
    :param scheme: Measurement scheme (one of :code:`'angle-dispersive'`,
        :code:`'energy-dispersive'`/:code:`'angle- and energy-dispersive'`).
    """

    instrument_settings: InstrumentSettings
    data_files: List[Union[File, str]]
    additional_files: Optional[List[Union[File, str]]] = None
    scheme: Optional[Union[Literal["angle- and energy-dispersive", "angle-dispersive", "energy-dispersive"]]] = None

    __repr__ = Header._staggered_repr


@orsodataclass
class DataSource(Header):
    """
    The data_source object definition.

    :param owner: This refers to the actual owner of the data set, i.e. the
        main proposer or the person doing the measurement on a lab
        reflectometer.
    :param experiment: Details of the experimental.
    :param sample: Sample information.
    :param measurement: Measurement specifics.
    """

    owner: Person
    experiment: Experiment
    sample: Sample
    measurement: Measurement
    _orso_optionals = []

    __repr__ = Header._staggered_repr
