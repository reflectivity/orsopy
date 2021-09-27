"""
Implementation of the top level class for the ORSO header.
"""

# author: Andrew R. McCluskey (arm61)

import yaml
from typing import List, Union, TextIO, Optional
from dataclasses import dataclass
from .base import (Header, Column, _possibly_open_file,
                   _read_header_data, _nested_update, _dict_diff)
from .data_source import DataSource
from .reduction import Reduction

import numpy as np


ORSO_VERSION = '0.1'
ORSO_DESIGNATE = (f"# ORSO reflectivity data file | {ORSO_VERSION} standard "
                  "| YAML encoding | https://www.reflectometry.org/")


class Orso(Header):
    """
    The Orso object collects the necessary metadata.
    """
    data_source: DataSource
    reduction: Reduction
    columns: List[Column]
    data_set: Optional[Union[int, str]] = None

    __repr__ = Header._staggered_repr

    def __init__(self, creator: Creator, data_source: DataSource, reduction: Reduction,
                 columns: List[Column], data_set: Optional[Union[int, str]] = None, **user_data):
        self.creator = creator
        self.data_source = data_source
        self.reduction = reduction
        self.columns = columns
        self.data_set = data_set
        self.__post_init__()
        # additional keywords used to add fields to the file header
        # some recreation does not work when using the attribute directly so it's wrapped in a property
        self._user_data = user_data

    @property
    def user_data(self):
        return self._user_data

    @user_data.setter
    def user_data(self, value):
        if not type(value) is dict:
            raise ValueError("user_data has to be a dictionary")
        self._user_data = value

    def column_header(self) -> str:
        """
        An information string that explains what each of the columns
        in a dataset corresponds to.
        """
        out = '# '
        for ci in self.columns:
            if ci.unit is None:
                out += f"{ci.name:<23}"
            else:
                out += f"{f'{ci.name} ({ci.unit})':<23}"
            if ci is self.columns[0]:
                # strip two characters from first column to align
                out = out[:-4]
        return out[:-1]

    def from_difference(self, other_dict: dict) -> 'Orso':
        """
        Constructs another `Orso` instance from self, and a dict
        containing updated header information.

        Parameters
        ----------
        other_dict: dict
            Contains updated header information

        Returns
        -------
        new_orso: Orso
            A new `Orso` object constructed from self, and the
            updated header information.
        """
        # recreate info from difference dictionary
        output = self.to_dict()
        output = _nested_update(output, other_dict)
        return Orso(**output)

    def to_difference(self, other: 'Orso') -> dict:
        """
        A dictionary containing the difference in header information between
        two Orso objects.

        Parameters
        ----------
        other: Orso

        Returns
        -------
        out_dict: dict
        """
        # return a dictionary of differences to other object
        my_dict = self.to_dict()
        other_dict = other.to_dict()
        out_dict = _dict_diff(my_dict, other_dict)
        return out_dict

    def to_dict(self):
        """
        Adds the user data to the returned dictionary.
        """
        out = super().to_dict()
        out.update(self._user_data)
        # put columns at the end of the dictionary
        cols = out.pop('columns')
        out['columns'] = cols
        return out


@dataclass
class OrsoDataset:
    """
    Parameters
    ----------
    info: Orso
        The header information for the reflectivity measurement.
    data: np.ndarray
        The numerical data associated with the reflectivity measurement.
        The data has shape `(npnts, ncols)`, where
        `ncols == len(self.info.columns)`.
    """
    info: Orso
    data: np.ndarray

    def __post_init__(self):
        if self.data.shape[1] != len(self.info.columns):
            raise ValueError("Data has to have the same number of columns as header")

    def header(self) -> str:
        """
        The header string for the ORSO file.
        """
        out = self.info.to_yaml()
        out += self.info.column_header()
        return out

    def diff_header(self, other: 'OrsoDataset') -> str:
        # return a header string that only contains changes to other
        # OrsoDataset ensure that data_set is the first entry
        out_dict = {"data_set": None}

        _diff = self.info.to_difference(other.info)
        out_dict.update(_diff)
        out_dict["data_set"] = other.info.data_set

        out = yaml.dump(out_dict, sort_keys=False)
        out += self.info.column_header()
        return out

    def save(self, fname):
        return save_orso([self], fname)

    def __eq__(self, other: 'OrsoDataset'):
        return self.info == other.info and (self.data == other.data).all()


def save_orso(
        datasets: List[OrsoDataset],
        fname: Union[TextIO, str],
        comment: Optional[str] = None) -> None:
    """
    Saves an ORSO file.

    Parameters
    ----------
    datasets: List
        List of OrsoDataset to save into the Orso file.
    fname: file-like or str
        The Orso file to save
    comment: str, Optional
        Comment to write at top of Orso file.

    Each of the datasets must have a unique `OrsoDataset.info.data_set`
    attribute. If that attribute is not set, it is given an integer value
    corresponding to it's position in the list. If more than one dataset has
    the same attribute value then a Va
    """
    for idx, dataset in enumerate(datasets):
        info = dataset.info
        data_set = info.data_set
        if (data_set is None or (isinstance(data_set, str) and len(data_set) == 0)):
            # it's not set, or is zero length string
            info.data_set = idx

    dsets = [dataset.info.data_set for dataset in datasets]
    if len(set(dsets)) != len(dsets):
        raise ValueError(
            "All `OrsoDataset.info.data_set` values must be unique")

    with _possibly_open_file(fname, 'w') as f:
        header = f"{ORSO_DESIGNATE}\n"
        if comment is not None:
            header += f"# {comment}\n"

        ds1 = datasets[0]
        header += ds1.header()
        np.savetxt(f, ds1.data, header=header, fmt='%-22.16e')

        for dsi in datasets[1:]:
            hi = ds1.diff_header(dsi)
            np.savetxt(f, dsi.data, header=hi, fmt='%-22.16e')


def load_orso(fname: Union[TextIO, str]) -> List[OrsoDataset]:
    """
    Parameters
    ----------
    fname: file-like or str
        The Orso file to load

    Returns
    -------
    ods: List
        List of OrsoDataset corresponding to each dataset contained within the
        ORT file.
    """
    dct_list, datas, version = _read_header_data(fname)
    ods = []

    for dct, data in zip(dct_list, datas):
        o = Orso(**dct)
        od = OrsoDataset(o, data)
        ods.append(od)
    return ods
