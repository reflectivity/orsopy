"""
Implementation of the top level class for the ORSO header.
"""

from dataclasses import dataclass
from typing import Any, List, Optional, TextIO, Union

import numpy as np
import yaml

from .base import Column, Header, _dict_diff, _nested_update, _possibly_open_file, _read_header_data, orsodataclass
from .data_source import DataSource
from .reduction import Reduction

ORSO_VERSION = "0.1"
ORSO_DESIGNATE = (
    f"# ORSO reflectivity data file | {ORSO_VERSION} standard " "| YAML encoding | https://www.reflectometry.org/"
)


@orsodataclass
class Orso(Header):
    """
    The Orso object collects the necessary metadata.

    :param data_source: Information about the origin and ownership of
        the raw data.
    :param reduction: Details of the data reduction that has been
        performed the content of this section should contain enough
        information to rerun the reduction.
    :param columns: Information about the columns of data that will
        be contained in the file.
    :param data_set: An identified for the data set, i.e. if there is
        more than one data set in the object.
    """

    data_source: DataSource
    reduction: Reduction
    columns: List[Column]
    data_set: Optional[Union[int, str]] = None

    __repr__ = Header._staggered_repr

    def __init__(
        self,
        data_source: DataSource,
        reduction: Reduction,
        columns: List[Column],
        data_set: Optional[Union[int, str]] = None,
        **user_data,
    ):
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

        :return: Explanatory string.
        """
        out = "# "
        for ci in self.columns:
            if ci.unit is None:
                out += f"{ci.name:<23}"
            else:
                out += f"{f'{ci.name} ({ci.unit})':<23}"
            if ci is self.columns[0]:
                # strip two characters from first column to align
                out = out[:-4]
        return out[:-1]

    def from_difference(self, other_dict: dict) -> "Orso":
        """
        Constructs another :py:class:`Orso` instance from self, and a dict
        containing updated header information.

        :param other_dict: Contains updated header information.

        :return: A new :py:class:`Orso` object constructed from self, and the
            updated header information.
        """
        # recreate info from difference dictionary
        output = self.to_dict()
        output = _nested_update(output, other_dict)
        return Orso(**output)

    def to_difference(self, other: "Orso") -> dict:
        """
        A dictionary containing the difference in header information between
        two :py:class:`Orso` objects.

        :param other: Other header to diff with.

        :return: Dictionary of the header information difference.
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
        cols = out.pop("columns")
        out["columns"] = cols
        return out


@dataclass
class OrsoDataset:
    """
    :param info: The header information for the reflectivity measurement
    :param data: The numerical data associated with the reflectivity
        measurement. The data has shape :code:`(npnts, ncols)`.

    :raises ValueError: When :code:`ncols != len(self.info.columns)`.
    """

    info: Orso
    data: Any

    def __post_init__(self):
        if self.data.shape[1] != len(self.info.columns):
            raise ValueError("Data has to have the same number of columns as header")

    def header(self) -> str:
        """
        The header string for the ORSO file.

        :return: Header string.
        """
        out = self.info.to_yaml()
        out += self.info.column_header()
        return out

    def diff_header(self, other: "OrsoDataset") -> str:
        """
        Return a header string that only contains changes to other
        :py:class:`OrsoDataset` ensure that data_set is the first entry.

        :param other: Other :py:class:`OrsoDataset` to compare against.

        :return: Header string with only changes.
        """
        out_dict = {"data_set": None}

        _diff = self.info.to_difference(other.info)
        out_dict.update(_diff)
        out_dict["data_set"] = other.info.data_set

        out = yaml.dump(out_dict, sort_keys=False)
        out += self.info.column_header()
        return out

    def save(self, fname: Union[TextIO, str]):
        """
        Save the :py:class:`OrsoDataset`.

        :param fname: The file name to save to.
        """
        return save_orso([self], fname)

    def __eq__(self, other: "OrsoDataset"):
        return self.info == other.info and (self.data == other.data).all()


def save_orso(
    datasets: List[OrsoDataset], fname: Union[TextIO, str], comment: Optional[str] = None, data_separator: str = ""
) -> None:
    """
    Saves an ORSO file. Each of the datasets must have a unique
    :py:attr:`OrsoDataset.info.data_set` attribute. If that attribute is not
    set, it is given an integer value corresponding to it's position
    in the list.

    :param datasets: List of OrsoDataset to save into the Orso file.
    :param fname: The file name to save to.
    :param comment: Comment to write at the top of Orso file.
    :param data_separator: Optinal string of newline characters to separate multiple datasets.

    :raises ValueError: If the :py:attr:`OrsoDataset.info.data_set`
        values are not unique.
    """
    # check for valid seperator characters
    if data_separator != "" and not data_separator.isspace():
        raise ValueError("data_separator can only contain new lines and spaces")

    for idx, dataset in enumerate(datasets):
        info = dataset.info
        data_set = info.data_set
        if data_set is None or (isinstance(data_set, str) and len(data_set) == 0):
            # it's not set, or is zero length string
            info.data_set = idx

    dsets = [dataset.info.data_set for dataset in datasets]
    if len(set(dsets)) != len(dsets):
        raise ValueError("All `OrsoDataset.info.data_set` values must be unique")

    with _possibly_open_file(fname, "w") as f:
        header = f"{ORSO_DESIGNATE}\n"
        if comment is not None:
            header += f"# {comment}\n"

        ds1 = datasets[0]
        header += ds1.header()
        np.savetxt(f, ds1.data, header=header, fmt="%-22.16e")

        for dsi in datasets[1:]:
            # write an optional spacer string between dataset e.g. \n
            f.write(data_separator)
            hi = ds1.diff_header(dsi)
            np.savetxt(f, dsi.data, header=hi, fmt="%-22.16e")


def load_orso(fname: Union[TextIO, str]) -> List[OrsoDataset]:
    """
    :param fname: The Orso file to load.

    :return: :py:class:`OrsoDataset` objects for each dataset contained
        within the ORT file.
    """
    dct_list, datas, version = _read_header_data(fname)
    ods = []

    for dct, data in zip(dct_list, datas):
        o = Orso(**dct)
        od = OrsoDataset(o, data)
        ods.append(od)
    return ods
