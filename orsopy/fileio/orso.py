"""
Implementation of the top level class for the ORSO header.
"""

# author: Andrew R. McCluskey (arm61)

from typing import List, Union
from dataclasses import dataclass
import datetime
import yaml
import numpy as np

from .base import Header, Column, Person, Creator, _possibly_open_file
from .data_source import (DataSource, Experiment, Sample, InstrumentSettings,
                          Measurement)
from .reduction import Reduction, Software


ORSO_designate = ("# ORSO reflectivity data file | 0.1 standard | "
                  "YAML encoding | https://www.reflectometry.org/")


@dataclass
class Orso(Header):
    """
    The Orso object collects the necessary metadata.
    """
    creator: Creator
    data_source: Union[DataSource, List[DataSource]]
    reduction: Reduction
    columns: List[Column]
    data_set: Union[str, List[str]]
    _orso_optionals = []

    def __post_init__(self):
        if self.columns is None or self.data_source is None:
            return None

        ncols = len(self.columns)
        if self.data_source.data.shape[1] < ncols:
            raise ValueError(
                "The data must have at least as many columns as those defined"
                " in ORSO.columns."
            )

    def add_data_source(self, data_source, data_set):
        """
        Adding datasets to an ORSO file.
        """
        ncols = len(self.columns)
        if data_source.data.shape[1] < ncols:
            raise ValueError(
                "The data must have at least as many columns as those defined"
                " in ORSO.columns."
            )

        if self.n_datasets() > 1:
            self.data_source.append(data_source)
            self.data_set.append(data_set)
        elif self.n_datasets() == 1:
            ds = self.data_source
            self.data_source = [ds, data_source]
            ds = self.data_set
            self.data_set = [ds, data_set]
        else:
            raise RuntimeError(
                "Problem adding a data_source to the ORSO object")

    def n_datasets(self):
        if isinstance(self.data_source, list):
            return len(self.data_source)
        elif isinstance(self.data_source, DataSource):
            return 1

    def save(self, fname):
        """
        Save an ORSO file

        Parameters
        ----------
        fname: str
        """
        def to_yaml(entry, attr):
            return yaml.dump(
                {entry: attr.to_dict()}, sort_keys=False
            )

        # Here we assemble the file by converting individual parts to yaml
        # strings, rather than just calling self.to_yaml().
        # This is because the specification says that successive datasets are
        # separated by data_source yaml sections. Unfortunately self.to_yaml()
        # would place all the data_source attributes in a single list at the
        # top of the file.
        with open(fname, "wt+") as f:
            header = [f"{ORSO_designate}\n"]
            # write out the first dataset
            header.append(to_yaml("creator", self.creator))

            if self.n_datasets() > 1:
                dsource = self.data_source[0]
                dset = self.data_set[0]
            else:
                dsource = self.data_source
                dset = self.data_set

            header.append(to_yaml("data_source", dsource))
            header.append(to_yaml("reduction", self.reduction))

            cols = [col.to_dict() for col in self.columns]
            header.append(yaml.dump({"columns": cols}, sort_keys=False))

            header.append(f"data_set: {dset}")

            data = dsource.data
            np.savetxt(f, data, header="".join(header))

            # write out subsequent datasets
            for i in range(1, self.n_datasets()):
                dsource = self.data_source[i]
                dset = self.data_set[i]

                h = [to_yaml("data_source", dsource), f"data_set: {dset}"]
                np.savetxt(f, dsource.data, header="".join(h))

    @classmethod
    def from_file(cls, f):
        """
        Read an ORSO file
        """
        with _possibly_open_file(f, 'r'):
            # TODO IMPLEMENT
            pass


def make_empty():
    """
    Create a complete Orso class object, with :code:`None` in all values
    which should be filled with objects from :code:`orsopy.fileio.base`
    or some Python base object (:code:`int`, :code:`list`, etc.).

    :return: Uninformative object
    :rtype: orsopy.fileio.orso.Orso
    """
    _person = Person(None, None, None)
    _creator = Creator(None, None, None, None, None)
    _experiment = Experiment(None, None, None, None)
    _instrument_settings = InstrumentSettings(None, None)
    _measurement = Measurement(_instrument_settings, None)
    _data_source = DataSource(
        _person, _experiment, Sample(None), _measurement, np.array([])
    )

    _reduction = Reduction(Software(None, None, None), None, None, None)
    return Orso(_creator, _data_source, _reduction, None, None)
