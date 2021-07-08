"""
Implementation of the top level class for the ORSO header.
"""

# author: Andrew R. McCluskey (arm61)

from typing import List
from dataclasses import dataclass
from .base import Header, Column
from .data_source import DataSource, Experiment, Sample
from .measurement import InstrumentSettings, Measurement
from .reduction import Reduction, Software


@dataclass
class Orso(Header):
    """
    The Orso object collects the necessary metadata.
    """
    data_source: DataSource
    measurement: Measurement
    reduction: Reduction
    column_description: List[Column]
    data_set: int
    _orso_optionals = []


def make_empty():
    """
    Create a complete Orso class object, with :code:`None` in all values
    which should be filled with objects from :code:`orsopy.fileio.base`
    or some Python base object (:code:`int`, :code:`list`, etc.).

    :return: Uninformative object
    :rtype: orsopy.fileio.orso.Orso
    """
    _data_source = DataSource(None, Experiment(None, None, None, None),
                              Sample(None))
    _measurement = Measurement(InstrumentSettings(None, None), None)
    _reduction = Reduction(Software(None, None, None), None, None, None)
    return Orso(_data_source, _measurement, _reduction, None, None)
