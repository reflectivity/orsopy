"""
Implementation of the Orso class that defined the header.
"""

# author: Andrew R. McCluskey (arm61)

from dataclasses import dataclass
from typing import List
from orsopy.fileio.base import (ValueScalar, ValueRange, ValueVector, Comment,
                                Person, Column, File, Header)
from orsopy.fileio.reduction import Software, Reduction
from orsopy.fileio.measurement import InstrumentSettings, Measurement
from orsopy.fileio.data_source import Experiment, Sample, DataSource

OSRO_VERSION = 0.1


@dataclass
class Orso(Header):
    """
    The Orso object collects the necessary metadata.
    """
    data_source: DataSource
    measurement: Measurement
    reduction: Reduction
    column_description: List[Column]
