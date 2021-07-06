"""
Implementation of the base classes for the ORSO header.
"""

# author: Andrew R. McCluskey (arm61)

from typing import Optional, Union, List
from dataclasses import field, dataclass
from dataclasses_json import dataclass_json
import yaml


def _noop(self, *args, **kw):
    pass


yaml.emitter.Emitter.process_tag = _noop


class Header:
    """
    The super class for all of the items in the orso module.
    """
    def __post_init__(self):
        if hasattr(self, 'unit'):
            self._check_unit(self.unit)

    def _clean(self):
        """
        Produces a clean dictionary of the Header object, removing
        any optional attributes with the value `None`.

        :return: Cleaned dictionary
        :rtype: dict
        """
        return dict((k, v) for (k, v) in self.__dict__.items()
                    if (v is not None or k not in self.orso_optionals))

    def to_yaml(self):
        """
        Return the yaml string for the Header item

        :return: Yaml string
        :rtype: str
        """
        return yaml.dump(self._clean(), sort_keys=False)

    @staticmethod
    def _check_unit(unit):
        """
        Check if the unit is valid, in future this could include
        recommendations.

        :param unit: Value to check if it is a value unit
        :type unit: str
        :raises: ValueError is the unit is not ASCII text
        """
        if unit is not None:
            if not unit.isascii():
                raise ValueError("The unit must be in ASCII text.")


@dataclass_json
@dataclass
class ValueScalar(Header):
    """A value or list of values with an optional unit."""
    magnitude: Union[float, List[float]]
    unit: Optional[str] = field(default=None,
                                metadata={'description': 'SI unit string'})
    orso_optionals = ['unit']


@dataclass_json
@dataclass
class ValueRange(Header):
    """A range or list of ranges with mins, maxs, and an optional unit."""
    min: Union[float, List[float]]
    max: Union[float, List[float]]
    unit: Optional[str] = field(default=None,
                                metadata={'description': 'SI unit string'})
    orso_optionals = ['unit']


@dataclass_json
@dataclass
class ValueVector(Header):
    """A vector or list of vectors with an optional unit.

    For vectors relating to the sample, such as polarisation,
    the follow is defined:

    * x is defined as parallel to the radiation beam, positive going\
        with the beam direction

    * y is defined from the other two based on the right hand rule

    * z is defined as normal to the sample surface, positive direction\
        in scattering direction
    """
    x: Union[float, List[float]]
    y: Union[float, List[float]]
    z: Union[float, List[float]]
    unit: Optional[str] = field(default=None,
                                metadata={'description': 'SI unit string'})
    orso_optionals = ['unit']


@dataclass_json
@dataclass
class Comment(Header):
    """A comment."""
    comment: str
    orso_optionals = []


@dataclass_json
@dataclass
class Person(Header):
    """Information about a person, including name, affilation(s), and email."""
    name: str
    affiliation: Union[str, List[str]]
    email: Optional[str] = field(
        default=None, metadata={'description': 'Contact email address'})
    orso_optionals = ['email']


@dataclass_json
@dataclass
class Column(Header):
    """Information about a data column"""
    quantity: str
    unit: Optional[str] = field(default=None,
                                metadata={'description': 'SI unit string'})
    description: Optional[str] = field(
        default=None,
        metadata={'description': 'A description of the column'})
    orso_optionals = ['unit', 'description']
