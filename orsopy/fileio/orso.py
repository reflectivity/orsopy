"""
Implementation of the top level class for the ORSO header.
"""

# author: Andrew R. McCluskey (arm61)

import re
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


@dataclass(repr=False)
class Orso(Header):
    """
    The Orso object collects the necessary metadata.
    """
    data_source: DataSource
    reduction: Reduction
    columns: List[Column]
    data_set: Optional[Union[int, str]] = None

    __repr__ = Header._staggered_repr

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

        :param other_dict: Contains updated header information
        :type other_dict: dict

        :return: A new `Orso` object constructed from self, and the
            updated header information.
        :rtype: orsopy.fileio.Orso
        """
        # recreate info from difference dictionary
        output = self.to_dict()
        output = _nested_update(output, other_dict)
        return Orso(**output)

    def to_difference(self, other: 'Orso') -> dict:
        """
        A dictionary containing the difference in header information between
        two Orso objects.

        :param other: Other header to diff with
        :type other: orsopy.fileio.Orso

        :return: Dictioonary of the header information difference
        :rtype: dict
        """
        # return a dictionary of differences to other object
        my_dict = self.to_dict()
        other_dict = other.to_dict()
        out_dict = _dict_diff(my_dict, other_dict)
        return out_dict


@dataclass
class OrsoDataset:
    """
    :param info: The header information for the reflectivity measurement
    :type info: orsopy.fileio.Orso
    :param data: The numerical data associated with the reflectivity measurement.
        The data has shape `(npnts, ncols)`, where
        `ncols == len(self.info.columns)`.
    :type np.ndarray:
    """
    info: Orso
    data: np.ndarray

    def __post_init__(self):
        if self.data.shape[1] != len(self.info.columns):
            raise ValueError(
                "Data has to have the same number of columns as header"
            )

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
        comment: Optional[str] = None
) -> None:
    """
    Saves an ORSO file. Each of the datasets must have a unique
    `OrsoDataset.info.data_set` attribute. If that attribute is not
    set, it is given an integer value corresponding to it's position
    in the list.

    :param datasets: List of OrsoDataset to save into the Orso file
    :type datasests: List
    :param fname: The Orso file to save
    :type fname: file-like or str
    :param comment: Comment to write at the top of Orso file
    :type comment: str, Optional
    :raises ValueError: If the OrsoDataset.info.data_set values are not unique
    """
    for idx, dataset in enumerate(datasets):
        info = dataset.info
        data_set = info.data_set
        if (data_set is None or (
                isinstance(data_set, str) and len(data_set) == 0)):
            # it's not set, or is zero length string
            info.data_set = idx

    dsets = [dataset.info.data_set for dataset in datasets]
    if len(set(dsets)) != len(dsets):
        raise ValueError(
            "All `OrsoDataset.info.data_set` values must be unique"
        )

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
    :param fname: The Orso file to load
    :type fname: file-like or str

    :return: List of OrsoDataset corresponding to each dataset contained within the
        ORT file.
    :rtype: List
    """
    dct_list, datas, version = _read_header_data(fname)
    ods = []

    for dct, data in zip(dct_list, datas):
        o = Orso(**dct)
        od = OrsoDataset(o, data)
        ods.append(od)
    return ods
