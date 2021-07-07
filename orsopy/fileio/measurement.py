"""
The measurement description for the ORSO header
"""

# author: Andrew R. McCluskey (arm61)

from typing import Optional, List, Union
from dataclasses import field, dataclass
from dataclasses_json import dataclass_json
from .base import File, Header, ValueRange, ValueScalar, ValueVector


@dataclass_json
@dataclass
class InstrumentSettings(Header):
    """Settings associated with the instrumentation."""
    incident_angle: Union[ValueScalar, ValueRange]
    wavelength: Union[ValueScalar, ValueRange]
    polarization: Optional[Union[str, ValueVector]] = field(
        default=None,
        metadata={
            'description':
            'Polarization described as p / m / pp / pm / mp / mm / vector'
        })
    configuration: Optional[str] = field(
        default=None,
        metadata={
            'description': 'half / full polarised | liqid_surface | etc'
        })
    _orso_optionals = ['configuration']


@dataclass_json
@dataclass
class Measurement(Header):
    """The measurement elements for the header."""
    instrument_settings: InstrumentSettings
    data_files: List[Union[File, str]]
    reference_data_files: Optional[List[Union[File,
                                              str]]] = field(default=None)
    scheme: Optional[str] = field(
        default=None,
        metadata={
            'description':
            'angle-dispersive/energy-dispersive/angle- and energy-dispersive'
        })
    _orso_optionals = ['reference_data_files', 'scheme']
