"""
Implementation of the top level class for the ORSO header.
"""

# author: Andrew R. McCluskey (arm61)

from typing import List
from dataclasses import dataclass
from .base import Header, Column
from .data_source import DataSource
from .measurement import Measurement
from .reduction import Reduction


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
