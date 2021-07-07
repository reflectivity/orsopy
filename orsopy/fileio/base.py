"""
Implementation of the base classes for the ORSO header.
"""

# author: Andrew R. McCluskey (arm61)

from typing import Optional, Union, List
from dataclasses import field, dataclass
import datetime
import pathlib
import warnings
import yaml


def _noop(self, *args, **kw):
    pass


yaml.emitter.Emitter.process_tag = _noop


def __datetime_representer(dumper, data):
    """
    Ensures that datetime objects are represented correctly."""
    value = data.isoformat('T')
    return dumper.represent_scalar('tag:yaml.org,2002:timestamp', value)


yaml.add_representer(datetime.datetime, __datetime_representer)


class Header:
    """
    The super class for all of the items in the orso module.
    """
    def __post_init__(self):
        if hasattr(self, 'unit'):
            self._check_unit(self.unit)

    def to_dict(self):
        """
        Produces a clean dictionary of the Header object, removing
        any optional attributes with the value `None`.

        :return: Cleaned dictionary
        :rtype: dict
        """
        d = {}
        for i in self.__dir__():
            v = getattr(self, i)
            if (not i.startswith('_') and not callable(v)) and (
                    v is not None or i not in self._orso_optionals):
                if hasattr(v, '_orso_optionals'):
                    d[i] = v.to_dict()
                elif isinstance(v, list):
                    dd = []
                    for j in v:
                        if hasattr(j, '_orso_optionals'):
                            dd.append(j.to_dict())
                        else:
                            dd.append(j)
                    d[i] = dd
                else:
                    d[i] = v
        return d

    def to_yaml(self):
        """
        Return the yaml string for the Header item

        :return: Yaml string
        :rtype: str
        """
        return yaml.dump(self.to_dict(), sort_keys=False)

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


@dataclass
class ValueScalar(Header):
    """A value or list of values with an optional unit."""
    magnitude: Union[float, List[float]]
    unit: Optional[str] = field(default=None,
                                metadata={'description': 'SI unit string'})
    _orso_optionals = ['unit']


@dataclass
class ValueRange(Header):
    """A range or list of ranges with mins, maxs, and an optional unit."""
    min: Union[float, List[float]]
    max: Union[float, List[float]]
    unit: Optional[str] = field(default=None,
                                metadata={'description': 'SI unit string'})
    _orso_optionals = ['unit']


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
    _orso_optionals = ['unit']


@dataclass
class Comment(Header):
    """A comment."""
    comment: str
    _orso_optionals = []


@dataclass
class Person(Header):
    """Information about a person, including name, affilation(s), and email."""
    name: str
    affiliation: Union[str, List[str]]
    email: Optional[str] = field(
        default=None, metadata={'description': 'Contact email address'})
    _orso_optionals = ['email']


@dataclass
class Column(Header):
    """Information about a data column"""
    quantity: str
    unit: Optional[str] = field(default=None,
                                metadata={'description': 'SI unit string'})
    description: Optional[str] = field(
        default=None, metadata={'description': 'A description of the column'})
    _orso_optionals = ['unit', 'description']


@dataclass
class File(Header):
    """A file with a last modified timestamp."""
    file: str
    timestamp: Optional[datetime.datetime] = field(
        default=None,
        metadata={
            'description': 'Last modified timestamp if not given and available'
        })
    _orso_optionals = []

    def __post_init__(self):
        fname = pathlib.Path(self.file)
        if not fname.exists():
            warnings.warn(f"The file {self.file} cannot be found.")
        else:
            if self.timestamp is None:
                self.timestamp = datetime.datetime.fromtimestamp(
                    fname.stat().st_mtime)
