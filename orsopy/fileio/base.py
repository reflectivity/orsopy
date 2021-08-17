"""
Implementation of the base classes for the ORSO header.
"""

# author: Andrew R. McCluskey (arm61)

import os.path
from copy import deepcopy
from collections.abc import Mapping
from typing import Optional, Union, List
from dataclasses import field, dataclass
import datetime
import pathlib
import warnings
import json
import yaml
from contextlib import contextmanager
import re

import numpy as np
from .. import orsopy


def _noop(self, *args, **kw):
    pass


yaml.emitter.Emitter.process_tag = _noop


def __datetime_representer(dumper, data):
    """
    Ensures that datetime objects are represented correctly."""
    value = data.isoformat("T")
    return dumper.represent_scalar("tag:yaml.org,2002:timestamp", value)


yaml.add_representer(datetime.datetime, __datetime_representer)


class Header:
    """
    The super class for all of the items in the orso module.
    """

    _orso_optionals = []

    def __post_init__(self):
        if hasattr(self, "unit"):
            self._check_unit(self.unit)

    def to_dict(self):
        """
        Produces a clean dictionary of the Header object, removing
        any optional attributes with the value `None`.

        :return: Cleaned dictionary
        :rtype: dict
        """
        out_dict = {}
        for i, value in self.__dict__.items():
            if i.startswith("_") or (
                value is None and i in self._orso_optionals
            ):
                continue

            if hasattr(value, "to_dict"):
                out_dict[i] = value.to_dict()
            elif isinstance(value, (list, tuple)):
                cleaned_list = []
                for j in value:
                    if hasattr(j, "to_dict"):
                        cleaned_list.append(j.to_dict())
                    else:
                        cleaned_list.append(j)
                out_dict[i] = type(value)(cleaned_list)
            elif i == "data_set" and value == 0:
                continue
            else:
                # here _todict converts objects that aren't derived from Header
                # and therefore don't have to_dict methods.
                out_dict[i] = _todict(value)
        return out_dict

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
class Value(Header):
    """A value or list of values with an optional unit."""

    magnitude: Union[float, List[float]]
    unit: Optional[str] = field(
        default=None, metadata={"description": "SI unit string"}
    )
    _orso_optionals = ["unit"]


@dataclass
class ValueRange(Header):
    """A range or list of ranges with mins, maxs, and an optional unit."""

    min: Union[float, List[float]]
    max: Union[float, List[float]]
    unit: Optional[str] = field(
        default=None, metadata={"description": "SI unit string"}
    )
    _orso_optionals = ["unit"]


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
    unit: Optional[str] = field(
        default=None, metadata={"description": "SI unit string"}
    )
    _orso_optionals = ["unit"]


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
    contact: Optional[str] = field(
        default=None, metadata={"description": "Contact (email) address"}
    )
    _orso_optionals = ["contact"]


@dataclass
class Creator(Person):
    time: datetime.datetime = None
    computer: str = ""
    _orso_optionals = ["contact"]


@dataclass
class Column(Header):
    """Information about a data column"""

    name: str
    unit: Optional[str] = field(
        default=None, metadata={"description": "SI unit string"}
    )
    dimension: Optional[str] = field(
        default=None, metadata={"dimension": "A description of the column"}
    )
    _orso_optionals = ["unit", "dimension"]


@dataclass
class File(Header):
    """A file with a last modified timestamp."""

    file: str
    created: Optional[datetime.datetime] = field(
        default=None,
        metadata={
            "description": "Last modified timestamp if not given and available"
        },
    )
    _orso_optionals = []

    def __post_init__(self):
        fname = pathlib.Path(self.file)
        if not fname.exists():
            warnings.warn(f"The file {self.file} cannot be found.")
        else:
            if self.created is None:
                self.created = datetime.datetime.fromtimestamp(
                    fname.stat().st_mtime
                )


def _read_header_data(file):
    """
    Reads the header and data contained within an ORSO file, parsing it into
    json dictionaries and numerical arrays.

    Parameters
    ----------
    file: str or file-like

    Returns
    -------
    dct_list, data_sets: list, list
        `dct_list` is a list of json dicts containing the parsed yaml header.
        This has to be processed further.
        `data_sets` is a Python list containing numpy arrays holding the
        reflectometry data in the file. It's contained in a list because each
        of the datasets may have a different number of columns.
    """

    with _possibly_open_file(file, "r") as fi:
        header = []

        # variables to keep track of where the datasets are
        ds_lines = []
        in_ds = False
        start_line = -1
        end_line = -1
        first_dataset = True

        for i, line in enumerate(fi.readlines()):
            if not line.startswith("#"):
                if not in_ds:
                    # you're in the first line of a dataset
                    in_ds = True
                    start_line = i
                continue
            if in_ds:
                # you've reached the first line after a comment line
                end_line = i - 1
                ds_lines.append((start_line, end_line))
                start_line = end_line = -1
                in_ds = False

            if line.startswith("# data_set") and first_dataset:
                header.append(line[1:])
                first_dataset = False
            elif line.startswith("# data_set") and not first_dataset:
                # append '---' to signify the start of a new yaml document
                # Subsequent datasets get parsed into a separate dictionary,
                # which can be used to synthesise new datasets from the first.
                header.append(" ---\n")
                header.append(line[1:])
            else:
                header.append(line[1:])

        yml = "".join(header)

        # first line of an ORSO file should have the magic string
        pattern = re.compile(
            r"^(# ORSO reflectivity data file \| ([0-9]+\.?[0-9]*|\.[0-9]+)"
            r" standard \| YAML encoding \| https://www\.reflectometry\.org/)$"
        )

        if not pattern.match(header[0].lstrip(" ")):
            raise ValueError(
                "First line does not appear to match that of an ORSO file"
            )

        dcts = yaml.safe_load_all(yml)

        # synthesise json dicts for each dataset from the first dataset, and
        # updates to the yaml.
        first_dct = next(dcts)
        dct_list = [_nested_update(deepcopy(first_dct), dct) for dct in dcts]
        dct_list.insert(0, first_dct)

        # now load the numerical data
        # finished reading the file, have to append the last dataset
        ds_lines.append((start_line, i))

        data = []
        for ds_line in ds_lines:
            fi.seek(0, 0)
            start, end = ds_line
            arr = np.loadtxt(fi, skiprows=start, max_rows=end - start + 1)
            data.append(arr)

        return dct_list, data


def _validate_header_data(dct_list: List[dict]):
    """
    Checks whether a json dictionary corresponds to a valid ORSO header.

    Obtain these dct_list by loading from _read_header_data first.

    Parameters
    ----------
    dct_list : List[dict]
        Header of file
    """
    import jsonschema

    pth = os.path.dirname(orsopy.__file__)
    schema_pth = os.path.join(pth, "schema", "refl_header.schema.json")
    with open(schema_pth, "r") as f:
        schema = json.load(f)

    # d contains datetime.datetime objects, which would fail the
    # jsonschema validation, so force those to be strings.
    modified_dct_list = [
        json.loads(json.dumps(dct, default=str)) for dct in dct_list
    ]
    for dct in modified_dct_list:
        jsonschema.validate(dct, schema)


@contextmanager
def _possibly_open_file(f, mode="wb"):
    """
    Context manager for files.
    Parameters
    ----------
    f : file-like or str
        If `f` is a file, then yield the file. If `f` is a str then open the
        file and yield the newly opened file.
        On leaving this context manager the file is closed, if it was opened
        by this context manager (i.e. `f` was a string).
    mode : str, optional
        mode is an optional string that specifies the mode in which the file
        is opened.
    Yields
    ------
    g : file-like
        On leaving the context manager the file is closed, if it was opened by
        this context manager.
    """
    close_file = False
    if (hasattr(f, "read") and hasattr(f, "write")) or f is None:
        g = f
    else:
        g = open(f, mode)
        close_file = True
    yield g
    if close_file:
        g.close()


def _todict(obj, classkey=None):
    """
    https://stackoverflow.com/questions/1036409
    Licenced under CC BY-SA 4.0
    """
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = _todict(v, classkey)
        return data
    elif hasattr(obj, "_ast"):
        return _todict(obj._ast())
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [_todict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict(
            [(key, _todict(value, classkey)) for key, value
             in obj.__dict__.items()
             if not callable(value) and not key.startswith('_')]
        )

        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj


def _nested_update(d, u):
    # nested dictionary update.
    for k, v in u.items():
        if isinstance(d, Mapping):
            if isinstance(v, Mapping):
                r = update(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        else:
            d = {k: u[k]}
    return d
