"""
Implementation of the Orso class that defined the header.
"""

import sys

from .base import (Column, ComplexValue, ErrorColumn, File, Header, Person, Value, ValueRange, ValueVector,
                   _read_header_data, _validate_header_data, ORSO_DATACLASSES)
from .data_source import DataSource, Experiment, InstrumentSettings, Measurement, Polarization, Sample
from .orso import ORSO_VERSION, Orso, OrsoDataset, load_orso, save_orso, load_nexus, save_nexus
from .reduction import Reduction, Software

this_module = sys.modules[__name__]

for _o in dir(this_module):
    cls = getattr(this_module, _o)
    try:
        if issubclass(cls, Header):
            ORSO_DATACLASSES[_o] = cls
    except Exception:
        pass

__all__ = [s for s in dir() if not s.startswith("_")]
