"""
Implementation of the base classes for the ORSO header.
"""

import datetime
import json
import os.path
import pathlib
import re
import sys
import warnings

from collections.abc import Mapping
from contextlib import contextmanager
from copy import deepcopy
from enum import Enum
from inspect import isclass
from typing import Any, Dict, Generator, List, Optional, TextIO, Tuple, Union

import numpy as np
import yaml
import yaml.constructor

# typing stuff introduced in python 3.8
try:
    from typing import Literal, get_args, get_origin
except ImportError:
    from .typing_backport import Literal, get_args, get_origin

from ..dataclasses import (_FIELD, _FIELD_INITVAR, _FIELDS, _HAS_DEFAULT_FACTORY, _POST_INIT_NAME, MISSING, _create_fn,
                           _field_init, _init_param, _set_new_attribute, dataclass, field, fields)


def _noop(self, *args, **kw):
    pass


JSON_MIMETYPE = "application/json"

yaml.emitter.Emitter.process_tag = _noop

# make sure that datetime strings get loaded as str not datetime instances
yaml.constructor.SafeConstructor.yaml_constructors[
    "tag:yaml.org,2002:timestamp"
] = yaml.constructor.SafeConstructor.yaml_constructors["tag:yaml.org,2002:str"]


def _custom_init_fn(fieldsarg, frozen, has_post_init, self_name, globals):
    """
    _init_fn from dataclasses adapted to accept additional keywords.
    See dataclasses source for comments on code.
    """
    seen_default = False
    for f in fieldsarg:
        if f.init:
            if not (f.default is MISSING and f.default_factory is MISSING):
                seen_default = True
            elif seen_default:
                raise TypeError(f"non-default argument {f.name!r} " "follows default argument")

    locals = {f"_type_{f.name}": f.type for f in fieldsarg}
    locals.update({"MISSING": MISSING, "_HAS_DEFAULT_FACTORY": _HAS_DEFAULT_FACTORY})

    body_lines = []
    for f in fieldsarg:
        line = _field_init(f, frozen, locals, self_name)
        if line:
            body_lines.append(line)

    if has_post_init:
        params_str = ",".join(f.name for f in fieldsarg if f._field_type is _FIELD_INITVAR)
        body_lines.append(f"{self_name}.{_POST_INIT_NAME}({params_str})")

    # processing of additional user keyword arguments
    body_lines += ["for k,v in user_kwds.items():", "    setattr(self, k, v)"]

    return _create_fn(
        "__init__",
        [self_name] + [_init_param(f) for f in fieldsarg if f.init] + ["**user_kwds"],
        body_lines,
        locals=locals,
        globals=globals,
        return_type=None,
    )


# register all ORSO classes here:
ORSO_DATACLASSES = dict()


def orsodataclass(cls: type):
    ORSO_DATACLASSES[cls.__name__] = cls
    attrs = cls.__dict__
    bases = cls.__bases__
    if "__annotations__" in attrs and len([k for k in attrs["__annotations__"].keys() if not k.startswith("_")]) > 0:
        # only applies to dataclass children of Header
        # add optional comment attribute, needs to come last
        attrs["__annotations__"]["comment"] = Optional[str]
        setattr(cls, "comment", field(default=None))

        # create the _orso_optional attribute
        orso_optionals = []
        for fname, ftype in attrs["__annotations__"].items():
            if type(None) in get_args(ftype):
                orso_optionals.append(fname)
        for base in bases:
            if hasattr(base, "_orso_optionals"):
                orso_optionals += getattr(base, "_orso_optionals")
        setattr(cls, "_orso_optionals", orso_optionals)
        out = dataclass(cls, repr=False, init=False)
        fieldsarg = getattr(out, _FIELDS)

        # Generate custom __init__ method that allows arbitrary extra keyword arguments
        has_post_init = hasattr(out, _POST_INIT_NAME)
        # Include InitVars and regular fields (so, not ClassVars).
        flds = [f for f in fieldsarg.values() if f._field_type in (_FIELD, _FIELD_INITVAR)]
        init_fun = _custom_init_fn(flds, False, has_post_init, "self", globals())
        _set_new_attribute(out, "__init__", init_fun)

        return out
    else:
        return cls


class ORSOResolveError(ValueError):
    pass


class Header:
    """
    The super class for all of the items in the orso module.
    """

    _orso_optionals: List[str] = []

    def __post_init__(self):
        """Make sure Header types are correct."""
        for fld in fields(self):
            attr = getattr(self, fld.name, None)
            type_attr = type(attr)
            if attr is None or type_attr is fld.type:
                continue
            else:
                try:
                    updt = self._resolve_type(fld.type, attr)
                except Exception as e:
                    message = (
                        f"An exception occurred when trying to resolve value '{attr}' in {self.__class__.__name__}:"
                    )
                    message += f" {e.__class__.__name__}: {e}"
                    raise ORSOResolveError(message) from e
                if updt is not None:
                    # convert to dataclass instance
                    setattr(self, fld.name, updt)
                else:
                    warnings.warn(
                        f"No suitable conversion found for {fld.name}, "
                        f"{fld.type} with value {attr}, "
                        "setting attribute with raw value from ORSO file",
                        RuntimeWarning,
                    )
                    setattr(self, fld.name, attr)
                    # raise ValueError(f"No suitable conversion found for {fld.type} with value {attr}")

        if hasattr(self, "unit"):
            self._check_unit(self.unit)

    @property
    def user_data(self):
        out_dict = {}
        fnames = [f.name for f in fields(self)]
        for key, value in self.__dict__.items():
            if key.startswith("_") or key in fnames:
                continue
            out_dict[key] = value
        return out_dict

    @staticmethod
    def _resolve_type(hint: type, item: Any) -> Any:
        """
        This function (recursively for :py:class:`Union` and
        :py:class`Optional` objects) populates different attributes,
        including constructing :py:class:`Header` object. Once the given
        object is created it is returned. If it is not possible to
        determine the correct object type :code:`None` is returned.

        :param hint: The type of the given field.
        :param item: An unresolved item to populate attribute.

        :return: Correctly resolved object with required type for orso
            compatibility.
        """
        if hint is Any:
            return item
        elif isclass(hint) and not getattr(hint, "__origin__", None) in [Dict, List, Tuple, Union, Literal]:
            # simple type that we can work with, no Union or List/Dict
            if isinstance(item, hint):
                return item
            if issubclass(hint, datetime.datetime) and isinstance(item, str):
                # convert str to datetime
                try:
                    return datetime.datetime.fromisoformat(item)
                except AttributeError:  # python 3.6
                    try:
                        item = item.split("+", 1)[0]
                        if "." in item:
                            return datetime.datetime.strptime(item, "%Y-%m-%dT%H:%M:%S.%f")
                        else:
                            return datetime.datetime.strptime(item, "%Y-%m-%dT%H:%M:%S")
                    except ValueError:
                        # string wasn't ISO8601 format
                        return None
                except ValueError:
                    # string wasn't ISO8601 format
                    return None
            if issubclass(hint, Header) and isinstance(item, dict):
                # convert to dataclass instance
                attribs = hint.__annotations__.keys()
                realised_items = {k: item[k] for k in item.keys() if k in attribs}
                # orphan_items are extra dictionary entries that don't correspond to
                # arguments of a Header instance. They can't be used to construct
                # a header instance, so remove them from the dict of arguments.
                # This enables back compatibility of Orso files as attributes
                # present in later versions will still be loadable by earlier code.
                orphan_items = {k: item[k] for k in item.keys() if k not in attribs}

                try:
                    value = hint(**realised_items)
                    # keep the orphan items with the newly constructed Header
                    for k, it in orphan_items.items():
                        setattr(value, k, it)
                    return value
                except (ValueError, TypeError):
                    return None
            else:
                # convert to type
                try:
                    return hint(item)
                except (ValueError, TypeError):
                    return None
        else:
            # the hint is a combined type (Union/List/Dict etc.)
            hbase = get_origin(hint)
            if hbase in (list, tuple):
                t0 = get_args(hint)[0]
                if isinstance(item, (list, tuple)):
                    if hbase is list:
                        return list([Header._resolve_type(t0, i) for i in item])
                    else:
                        return tuple([Header._resolve_type(ti, i) for ti, i in zip(get_args(hint), item)])
                else:
                    return hbase([Header._resolve_type(t0, item)])
            elif hbase is dict:
                try:
                    value_type = get_args(hint)[1]
                except IndexError:
                    warnings.warn(
                        "The evaluation of type hints requires key/value definition for Dict, "
                        "if you want to use unspecified dictionaries use dict instead of Dict."
                    )
                    raise
                try:
                    for key, value in item.items():
                        # resolve the type of any value in the dictionary
                        item[key] = Header._resolve_type(value_type, value)
                    return item
                except AttributeError:
                    return None
            elif hbase in [Union, Optional]:
                subtypes = get_args(hint)
                if type(item) in subtypes:
                    # check if the item is in the list of allowed
                    # subtypes
                    return item
                for subt in subtypes:
                    # if it's not, then try to resolve its type.
                    res = Header._resolve_type(subt, item)
                    if res is not None:
                        return res
            elif hbase is Literal:
                if item in get_args(hint):
                    return item
                else:
                    warnings.warn(
                        f"Has to be one of {get_args(hint)} got {item}",
                        RuntimeWarning,
                    )
                    return str(item)
        return None

    @classmethod
    def empty(cls) -> "Header":
        """
        Create an empty instance of this item containing
        all non-option attributes as :code:`None`.

        :return: Empty class.
        """
        attr_items = {}
        for fld in fields(cls):
            if type(None) in get_args(fld.type):
                # skip optional arguments
                continue
            elif isclass(fld.type) and issubclass(fld.type, Header):
                attr_items[fld.name] = fld.type.empty()
            elif (
                get_origin(fld.type) is Union
                and isclass(get_args(fld.type)[0])
                and issubclass(get_args(fld.type)[0], Header)
            ):
                attr_items[fld.name] = get_args(fld.type)[0].empty()
            elif (
                get_origin(fld.type) is list
                and isclass(get_args(fld.type)[0])
                and issubclass(get_args(fld.type)[0], Header)
            ):
                attr_items[fld.name] = [get_args(fld.type)[0].empty()]
            elif get_origin(fld.type) is list:
                attr_items[fld.name] = []
            else:
                attr_items[fld.name] = None
        return cls(**attr_items)

    @staticmethod
    def asdict(header: "Header") -> dict:
        """
        Static method for :py:func:`to_dict`.

        :param header: Object to convert to dictionary.

        :return: Dictionary result.
        """
        return header.to_dict()

    def to_dict(self) -> dict:
        """
        Produces a clean dictionary of the Header object, removing
        any optional attributes with the value :code:`None`.

        :return: Cleaned dictionary.
        """
        out_dict = {}
        for i, value in self.__dict__.items():
            if i.startswith("_") or (value is None and i in self._orso_optionals):
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
            else:
                # here _todict converts objects that aren't derived from Header
                # and therefore don't have to_dict methods.
                out_dict[i] = _todict(value)
        return out_dict

    def to_yaml(self) -> str:
        """
        Return the yaml string for the Header item

        :return: Yaml string
        """
        return yaml.dump(self, Dumper=OrsoDumper, sort_keys=False)

    def _to_object_dict(self):
        output = {}
        for i, value in self.__dict__.items():
            if i.startswith("_") or (value is None and i in self._orso_optionals):
                continue
            output[i] = value
        return output

    def yaml_representer(self, dumper: yaml.Dumper):
        output = self._to_object_dict()
        return dumper.represent_mapping(dumper.DEFAULT_MAPPING_TAG, output, flow_style=False)

    def yaml_representer_compact(self, dumper: yaml.Dumper):
        output = self._to_object_dict()
        return dumper.represent_mapping(dumper.DEFAULT_MAPPING_TAG, output, flow_style=True)

    def to_nexus(self, root=None, name=None):
        """
        Produces an HDF5 representation of the Header object, removing
        any optional attributes with the value :code:`None`.

        :return: HDF5 object
        """
        classname = self.__class__.__name__
        import h5py

        assert isinstance(root, h5py.Group)
        group = root.create_group(classname if name is None else name)
        group.attrs["ORSO_class"] = classname

        for child_name, value in self.__dict__.items():
            if child_name.startswith("_") or (value is None and child_name in self._orso_optionals):
                continue

            if value.__class__ in ORSO_DATACLASSES.values():
                value.to_nexus(root=group, name=child_name)
            elif isinstance(value, (list, tuple)):
                child_group = group.create_group(child_name)
                child_group.attrs["sequence"] = 1
                for index, item in enumerate(value):
                    # use the 'name' attribute of children if it exists, else index:
                    sub_name = getattr(item, "name", str(index))
                    if item.__class__ in ORSO_DATACLASSES.values():
                        item_out = item.to_nexus(root=child_group, name=sub_name)
                    else:
                        t_value = nexus_value_converter(item)
                        if any(isinstance(t_value, t) for t in (str, float, int, bool, np.ndarray)):
                            item_out = child_group.create_dataset(sub_name, data=t_value)
                        elif t_value is None:
                            # special handling for null datasets: no data
                            item_out = child_group.create_dataset(sub_name, dtype="f")
                        elif isinstance(t_value, dict):
                            item_out = child_group.create_dataset(sub_name, data=json.dumps(t_value))
                            item_out.attrs["mimetype"] = JSON_MIMETYPE
                        else:
                            import warnings
                            # raise ValueError(f"unserializable attribute found: {child_name}[{index}] = {t_value}")
                            warnings.warn(f"unserializable attribute found: {child_name}[{index}] = {t_value}")
                            continue
                    item_out.attrs["sequence_index"] = index
            else:
                # here _todict converts objects that aren't derived from Header
                # and therefore don't have to_dict methods.
                t_value = nexus_value_converter(value)
                if any(isinstance(t_value, t) for t in (str, float, int, bool, np.ndarray)):
                    group.create_dataset(child_name, data=t_value)
                elif t_value is None:
                    group.create_dataset(child_name, dtype="f")
                elif isinstance(t_value, dict):
                    dset = group.create_dataset(child_name, data=json.dumps(t_value))
                    dset.attrs["mimetype"] = JSON_MIMETYPE
                else:
                    import warnings
                    warnings.warn(f"unserializable attribute found: {child_name} = {t_value}")
                    # raise ValueError(f"unserializable attribute found: {child_name} = {t_value}")
        return group

    @staticmethod
    def _check_unit(unit: str):
        """
        Check if the unit is valid, in future this could include
        recommendations.

        :param unit: Value to check if it is a value unit.

        :raises: ValueError is the unit is not ASCII text.
        """
        if unit is not None:
            # raise UnicodeError if not ascii
            unit.encode("ascii")

    def __repr__(self):
        """
        Representation that does not show empty arguments.
        """
        out = f"{self.__class__.__name__}("
        for fi in fields(self):
            if fi.name in self._orso_optionals and getattr(self, fi.name) is None:
                # ignore empty optional arguments
                continue
            out += f"{fi.name}={getattr(self, fi.name)!r}, "
        out = out[:-2] + ")"
        return out

    def _staggered_repr(self):
        """
        Generate a string representation distributed over multiple lines
        to improve readability.

        To use in a subclass, the __repr__ method has to be replaced with this one.
        """
        slen = len(self.__class__.__name__)
        out = f"{self.__class__.__name__}(\n"
        for fi in fields(self):
            if fi.name in self._orso_optionals and getattr(self, fi.name) is None:
                # ignore empty optional arguments
                continue
            nlen = len(fi.name)
            ftxt = repr(getattr(self, fi.name))
            ftxt = ftxt.replace("\n", "\n" + " " * (slen + nlen + 2))
            out += " " * (slen + 1) + f"{fi.name}={ftxt},\n"
        out += " " * (slen + 1) + ")"
        return out


class OrsoDumper(yaml.SafeDumper):
    def represent_data(self, data):
        if hasattr(data, "yaml_representer"):
            return data.yaml_representer(self)
        elif isinstance(data, datetime.datetime):
            value = data.isoformat("T")
            return super().represent_scalar("tag:yaml.org,2002:timestamp", value)
        elif np.isscalar(data) and hasattr(data, "item"):
            # If data is a numpy scalar, convert to a python object
            return super().represent_data(data.item())
        else:
            return super().represent_data(data)


unit_registry = None


@orsodataclass
class ErrorValue(Header):
    """
    Information about errors on a value.
    """

    error_value: float
    error_type: Optional[Literal["uncertainty", "resolution"]] = None
    value_is: Optional[Literal["sigma", "FWHM"]] = None
    distribution: Optional[Literal["gaussian", "triangular", "uniform", "lorentzian"]] = None

    yaml_representer = Header.yaml_representer_compact

    @property
    def sigma(self):
        """
        Return value converted to standard deviation.

        The conversion factors can be found in common statistics and experimental physics text books or derived
        manually solving the variance definition integral.
        (e.g. Dekking, Michel (2005).
        A modern introduction to probability and statistics : understanding why and how.
        Springer, London, UK:)
        Values and some references available on Wikipedia, too.
        """
        if self.value_is == "FWHM":
            from math import log, sqrt

            value = self.error_value

            if self.distribution in ["gaussian", None]:
                # Solving for the gaussian function = 0.5 yields:
                return value / (2.0 * sqrt(2.0 * log(2.0)))
            elif self.distribution == "triangular":
                # See solution of integral e.g. https://math.stackexchange.com/questions/4271314/
                # what-is-the-proof-for-variance-of-triangular-distribution/4273147#4273147
                # setting c=0 and a=b=FWHM for the symmetric triangle around 0.
                return value / sqrt(6.0)
            elif self.distribution == "uniform":
                # Variance is just the integral of x² from -0.5*FWHM to 0.5*FWHM => 1/12.
                return value / sqrt(12.0)
            elif self.distribution == "lorentzian":
                raise ValueError("Lorentzian distribution does not have a sigma value")
            else:
                raise NotImplementedError(f"Unknown distribution {self.distribution}")
        else:
            # Value is already sigma
            return self.error_value


@orsodataclass
class Value(Header):
    """
    A value or list of values with an optional unit.
    """

    magnitude: float
    unit: Optional[str] = field(default=None, metadata={"description": "SI unit string"})
    error: Optional[ErrorValue] = None

    yaml_representer = Header.yaml_representer_compact

    def __repr__(self):
        """
        Make representation more readability by removing names of default arguments.
        """
        output = super().__repr__()
        output = output.replace("magnitude=", "")
        output = output.replace("unit=", "")
        return output

    def as_unit(self, output_unit):
        """
        Returns the value as converted to the given unit.
        """
        if output_unit == self.unit:
            return self.magnitude

        global unit_registry
        if unit_registry is None:
            import pint

            unit_registry = pint.UnitRegistry()

        val = self.magnitude * unit_registry(self.unit)
        return val.to(output_unit).magnitude


@orsodataclass
class ComplexValue(Header):
    """
    A value or list of values with an optional unit.
    """

    real: float
    imag: Optional[float] = None
    unit: Optional[str] = field(default=None, metadata={"description": "SI unit string"})
    error: Optional[ErrorValue] = None

    yaml_representer = Header.yaml_representer_compact

    def __repr__(self):
        """
        Make representation more readability by removing names of default arguments.
        """
        output = super().__repr__()
        output = output.replace("real=", "")
        output = output.replace("imag=", "")
        output = output.replace("unit=", "")
        return output

    def as_unit(self, output_unit):
        """
        Returns the complex value as converted to the given unit.
        """
        if self.imag is None:
            value = self.real + 0j
        else:
            value = self.real + 1j * self.imag
        if output_unit == self.unit:
            return value

        global unit_registry
        if unit_registry is None:
            import pint

            unit_registry = pint.UnitRegistry()

        val = value * unit_registry(self.unit)
        return val.to(output_unit).magnitude


@orsodataclass
class ValueRange(Header):
    """
    A range or list of ranges with mins, maxs, and an optional unit.
    """

    min: float
    max: float
    unit: Optional[str] = field(default=None, metadata={"description": "SI unit string"})

    yaml_representer = Header.yaml_representer_compact

    def as_unit(self, output_unit):
        """
        Returns a (min, max) tuple of values as converted to the given unit.
        """
        if output_unit == self.unit:
            return (self.min, self.max)

        global unit_registry
        if unit_registry is None:
            import pint

            unit_registry = pint.UnitRegistry()

        vmin = self.min * unit_registry(self.unit)
        vmax = self.max * unit_registry(self.unit)
        return (vmin.to(output_unit).magnitude, vmax.to(output_unit).magnitude)


@orsodataclass
class ValueVector(Header):
    """
    A vector or list of vectors with an optional unit.
    For vectors relating to the sample, such as polarisation,
    the follow definitions are used.

    :param x: is defined as parallel to the radiation beam, positive going
        with the beam direction.
    :param y: is defined from the other two based on the right hand rule.
    :param z: is defined as normal to the sample surface, positive direction
        in scattering direction.
    :param unit: SI unit string.
    """

    x: float
    y: float
    z: float
    unit: Optional[str] = field(default=None, metadata={"description": "SI unit string"})
    error: Optional[ErrorValue] = None

    yaml_representer = Header.yaml_representer_compact

    def as_unit(self, output_unit):
        """
        Returns a (x, y, z) tuple of values as converted to the given unit.
        """
        if output_unit == self.unit:
            return (self.x, self.y, self.z)

        global unit_registry
        if unit_registry is None:
            import pint

            unit_registry = pint.UnitRegistry()

        vx = self.x * unit_registry(self.unit)
        vy = self.y * unit_registry(self.unit)
        vz = self.z * unit_registry(self.unit)
        return (vx.to(output_unit).magnitude, vy.to(output_unit).magnitude, vz.to(output_unit).magnitude)


@orsodataclass
class Person(Header):
    """
    Information about a person, including name, affilation(s), and contact
    information.
    """

    name: str
    affiliation: str
    contact: Optional[str] = field(default=None, metadata={"description": "Contact (email) address"})


@orsodataclass
class Column(Header):
    """
    Information about a data column.
    """

    name: str
    unit: Optional[str] = field(default=None, metadata={"description": "SI unit string"})
    physical_quantity: Optional[str] = field(
        default=None, metadata={"physical_quantity": "A description of the column"}
    )

    yaml_representer = Header.yaml_representer_compact


@orsodataclass
class ErrorColumn(Header):
    """
    Information about a data column.
    """

    error_of: str
    error_type: Optional[Literal["uncertainty", "resolution"]] = None
    value_is: Optional[Literal["sigma", "FWHM"]] = None
    distribution: Optional[Literal["gaussian", "triangular", "uniform", "lorentzian"]] = None

    yaml_representer = Header.yaml_representer_compact

    @property
    def name(self):
        """
        A convenience property to allow programs to get a valid name attribute for any column.
        """
        return f"s{self.error_of}"

    @property
    def to_sigma(self):
        """
        The multiplicative factor needed to convert a FWHM to sigma.

        The conversion factors can be found in common statistics and experimental physics text books or derived
        manually solving the variance definition integral.
        (e.g. Dekking, Michel (2005).
        A modern introduction to probability and statistics : understanding why and how.
        Springer, London, UK:)
        Values and some references available on Wikipedia, too.
        """
        if self.value_is == "FWHM":
            from math import log, sqrt

            if self.distribution in ["gaussian", None]:
                # Solving for the gaussian function = 0.5 yields:
                return 1.0 / (2.0 * sqrt(2.0 * log(2.0)))
            elif self.distribution == "triangular":
                # See solution of integral e.g. https://math.stackexchange.com/questions/4271314/
                # what-is-the-proof-for-variance-of-triangular-distribution/4273147#4273147
                # setting c=0 and a=b=FWHM for the symmetric triangle around 0.
                return 1.0 / sqrt(6.0)
            elif self.distribution == "uniform":
                # Variance is just the integral of x² from -0.5*FWHM to 0.5*FWHM => 1/12.
                return 1.0 / sqrt(12.0)
            elif self.distribution == "lorentzian":
                raise ValueError("Lorentzian distribution does not have a sigma value")
            else:
                raise NotImplementedError(f"Unknown distribution {self.distribution}")
        else:
            # Value is already sigma
            return 1.0


@orsodataclass
class File(Header):
    """
    A file with file path and a last modified timestamp.
    """

    file: str
    timestamp: Optional[datetime.datetime] = field(
        default=None,
        metadata={
            "description": "Last modified timestamp. If it's not specified,"
            " then an attempt will be made to check on the file"
            " itself"
        },
    )

    def __post_init__(self):
        """
        Assigns a timestamp for file creation if not defined.
        """
        Header.__post_init__(self)
        if self.timestamp is None:
            fname = pathlib.Path(self.file)
            if fname.exists():
                self.timestamp = datetime.datetime.fromtimestamp(fname.stat().st_mtime)


class NotOrsoCompatibleFileError(ValueError):
    pass


def _read_header_data(file: Union[TextIO, str], validate: bool = False) -> Tuple[List[dict], list, str]:
    """
    Reads the header and data contained within an ORSO file, parsing it into
    json dictionaries and numerical arrays.

    Parameters
    ----------
    :param file: File to read.
    :param validate: Validates the file against the ORSO json schema.
        Requires that the jsonschema package be installed.

    :return: The tuple contains:
        - First item is a list of json dicts containing the parsed yaml
        header. This has to be processed further.
        - Second item is a Python list containing numpy arrays holding the
        reflectometry data in the file. It's contained in a list because
        each of the datasets may have a different number of columns.
        - Final item is the ORSO version string.
    """

    with _possibly_open_file(file, "r") as fi:
        header = []

        # collection of the numerical arrays
        data = []
        _ds_lines = []
        first_dataset = True

        for i, line in enumerate(fi.readlines()):
            if not line.startswith("#"):
                # ignore empty lines
                if line.strip() != "":
                    _ds_lines.append(line)
                continue

            if line.startswith("# data_set") and first_dataset:
                header.append(line[1:])
                first_dataset = False
            elif line.startswith("# data_set") and not first_dataset:
                # a new dataset is starting. Complete the previous dataset's
                # numerical array  and start collecting the numbers for this
                # dataset
                _d = np.array([np.fromstring(v, dtype=float, sep=" ") for v in _ds_lines])
                data.append(_d.T)
                _ds_lines = []

                # append '---' to signify the start of a new yaml document
                # Subsequent datasets get parsed into a separate dictionary,
                # which can be used to synthesise new datasets from the first.
                header.append("---\n")
                header.append(line[1:])
            else:
                header.append(line[1:])

        # append the last numerical array
        _d = np.array([np.fromstring(v, dtype=float, sep=" ") for v in _ds_lines])
        data.append(_d.T)

        yml = "".join(header)

        # first line of an ORSO file should have the magic string
        pattern = re.compile(
            r"^(# ORSO reflectivity data file \| ([0-9]+\.?[0-9]*|\.[0-9]+)"
            r" standard \| YAML encoding \| https://www\.reflectometry\.org/)$"
        )

        if len(header) < 1 or not pattern.match(header[0].lstrip(" ")):
            raise NotOrsoCompatibleFileError("First line does not appear to match that of an ORSO file")
        version = re.findall(r"([0-9]+\.?[0-9]*|\.[0-9]+)+?", header[0])[0]

        dcts = yaml.safe_load_all(yml)

        # synthesise json dicts for each dataset from the first dataset, and
        # updates to the yaml.
        first_dct = next(dcts)

        dct_list = [_nested_update(deepcopy(first_dct), dct) for dct in dcts]
        dct_list.insert(0, first_dct)

    if validate:
        # requires jsonschema be installed
        _validate_header_data(dct_list)

    return dct_list, data, version


def _validate_header_data(dct_list: List[dict]):
    """
    Checks whether a json dictionary corresponds to a valid ORSO header.

    Obtain these dct_list by loading from _read_header_data first.

    :param dct_list: Dicts corresponding to parsed yaml headers from the ORT file.

    :raises ValueError: When the first four columns are not named correctly
        (i.e. :code:`'Qz'`, :code:`'R'`, :code:`'sR'`, :code:`'sQz'`).
    :raises ValueError: When the units for the :code:`'Qz'` column is not
        :code:`'1/angstrom'`.
    :raises ValueError: When the units for columns :code:`'Qz'` and
        :code:`'sQz'` are not the same.
    """
    import jsonschema

    req_cols = ["Qz", "R", "sR", "sQz"]
    acceptable_Qz_units = ["1/angstrom", "1/nm"]

    pth = os.path.dirname(__file__)
    schema_pth = os.path.join(pth, "schema", "refl_header.schema.json")
    with open(schema_pth, "r") as f:
        schema = json.load(f)

    for dct in dct_list:
        jsonschema.validate(dct, schema)

        # Validate the column names. Ideally this is done with the jsonschema,
        # but it's difficult to create a schema from the 'default' orsopy
        # dataclasses that does that. It is possible but it requires extra
        # column objects like Qz_column, R_column, etc.
        cols = dct["columns"]

        ncols = min(4, len(cols))
        col_names = [col["name"] if "name" in col else "s" + col["error_of"] for col in cols]
        units = [col.get("unit") for col in cols]

        if col_names[:ncols] != req_cols[:ncols]:
            raise ValueError("The first four columns should be named" " 'Qz', 'R', ['sR', ['sQz']]")

        if units[0] not in acceptable_Qz_units:
            raise ValueError("The Qz column must have units of '1/angstrom'" " or '1/nm'")


@contextmanager
def _possibly_open_file(f: Union[TextIO, str], mode: str = "wb") -> Generator[TextIO, None, None]:
    """
    Context manager for files.

    :param f: If `f` is a file, then yield the file. If `f` is a str then
        open the file and yield the newly opened file. On leaving this
        context manager the file is closed, if it was opened by this
        context manager (i.e. `f` was a string).
    :param modes: An optional string that specifies the mode in which
        the file is opened.
    :yields: On leaving the context manager the file is closed, if it
        was opened by this context manager.
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


def _todict(obj: Any, classkey: Any = None) -> dict:
    """
    Recursively converts an object to a dict representation
    https://stackoverflow.com/questions/1036409
    Licenced under CC BY-SA 4.0

    :param obj: Object to convert to dict representation.
    :param classkey: Key to be assigned to class objects.

    :return: Dictionary representation of object.
    """
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = _todict(v, classkey)
        return data
    elif isinstance(obj, Enum):
        return obj.value
    elif hasattr(obj, "_ast"):
        return _todict(obj._ast())
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [_todict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict(
            [
                (key, _todict(value, classkey))
                for key, value in obj.__dict__.items()
                if not callable(value) and not key.startswith("_")
            ]
        )

        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj


def json_datetime_trap(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    return obj


def enum_trap(obj):
    if isinstance(obj, Enum):
        return obj.value
    return obj


def nexus_value_converter(obj):
    for converter in (json_datetime_trap, enum_trap):
        obj = converter(obj)
    return obj


def _nested_update(d: dict, u: dict) -> dict:
    """
    Nested dictionary update.

    :param d: Dictionary to be updated.
    :param u: Dictionary where updates should come from.

    :return: Updated dictionary.
    """
    for k, v in u.items():
        if isinstance(d, Mapping):
            if isinstance(v, Mapping):
                r = _nested_update(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        else:
            d = {k: u[k]}
    return d


def _dict_diff(old: dict, new: dict) -> dict:
    """
    Recursive find differences between two dictionaries.

    :param old: Original dictionary.
    :param new: New dictionary to find differences in.

    :return: Dictionary containing values present in :py:attr:`new`
        that are not in :py:attr:`old`.
    """
    out = {}
    for key, value in new.items():
        if key in old:
            if type(value) is dict:
                diff = _dict_diff(old[key], value)
                if diff == {}:
                    continue
                else:
                    out[key] = diff
            elif old[key] == value:
                continue
            else:
                out[key] = value
        else:
            out[key] = value
    for key in [ki for ki in old.keys() if ki not in new]:
        out[key] = None
    return out
