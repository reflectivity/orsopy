"""
Implementation of the top level class for the ORSO header.
"""

# author: Andrew R. McCluskey (arm61)

from typing import List, Union
from dataclasses import dataclass, fields
import datetime
import yaml
import numpy as np

from .base import (Header, Column, Person, Creator, _possibly_open_file,
                   _read_header_data, ValueRange, Value, File)
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
        # TODO If we were using YAML tags then auto-object recreation would
        # be easy. However, we're not doing this so parse the yaml dictionary
        # by hand. There may be a better way of doing this.
        with _possibly_open_file(f, 'r') as fi:
            h, data = _read_header_data(fi)

        dct = yaml.load(h)

        # creator
        c = _make_kls(Creator, dct.get('creator', None))
        # columns
        columns = [Column(**c) for c in dct['columns']]

        # reduction
        _r = dct['reduction'].copy()
        _r['creator'] = _make_kls(Person, _r.get('creator', None))
        _s = _r.get("software", None)
        if isinstance(_s, str):
            _r['software'] = _s
        else:
            _r['software'] = _make_kls(Software, _s)

        r = _make_kls(Reduction, _r)

        # data_set
        data_set = dct.get('data_set')

        # data_source
        # if the number of data_source is 1, then data_source will be a dict
        # otherwise it'll be a list
        _ds_dct = dct['data_source'].copy()

        if hasattr(_ds_dct, "len"):
            ds = []
            for i, _dct in enumerate(_ds_dct):
                ds.append(_make_data_source(_dct, data[i]))
        else:
            ds = _make_data_source(_ds_dct, data[0])

        return Orso(c, ds, r, columns, data_set)


def _make_kls(kls, dct):
    """
    Factory for making the dataclass given an argument dictionary
    """
    if dct is None:
        return None
    else:
        lcl_dct = dct.copy()
        flds = fields(kls)
        names = [fld.name for fld in flds]
        # if the name isn't in the class field then remove from dct
        not_present = set(dct.keys()).difference(names)
        for k in not_present:
            lcl_dct.pop(k)

        return kls(**lcl_dct)


def _make_data_source(ds_dct, data):
    """Factory for creating a DataSource object"""
    e = _make_kls(Experiment, ds_dct['experiment'])
    o = _make_kls(Person, ds_dct['owner'])
    s = _make_kls(Sample, ds_dct['sample'])

    # constructing a Measurement is probably the hardest, since there
    # are lots of nested classes.
    meas = ds_dct['measurement']

    # deal with InstrumentSettings first
    inst = meas['instrument_settings']
    kls = _v_or_vr(inst['incident_angle'])
    inst['incident_angle'] = _make_kls(kls, inst['incident_angle'])
    kls = _v_or_vr(inst['wavelength'])
    inst['wavelength'] = _make_kls(kls, inst['wavelength'])
    meas['instrument_settings'] = _make_kls(InstrumentSettings, inst)

    def dfs_converter(df):
        if isinstance(df, dict):
            return _make_kls(File, df)
        return df

    if isinstance(meas['data_files'], list):
        meas['data_files'] = [dfs_converter(df) for df in meas['data_files']]
    else:
        meas['data_files'] = dfs_converter(meas['data_files'])

    dfr = meas.get("references", None)
    if dfr is not None:
        if isinstance(meas['references'], list):
            meas['references'] = [dfs_converter(df)
                                  for df in meas['references']]
        else:
            meas['references'] = dfs_converter(meas['references'])

    meas = _make_kls(Measurement, meas)

    return DataSource(o, e, s, meas, data)


def _v_or_vr(dct):
    # Choose whether the dictionary is consistent with a Value or ValueRange
    if "min" in dct and "max" in dct:
        return ValueRange
    elif "magnitude" in dct:
        return Value


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
