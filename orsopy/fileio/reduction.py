"""
The reduction elements for the ORSO header
"""

# author: Andrew R. McCluskey (arm61)

from typing import Optional, List, Union
from .dataclasses import field, dataclass
import datetime
from .base import Header, Person


@dataclass(repr=False)
class Software(Header):
    """Description of the reduction software."""
    name: str
    version: Optional[str] = None
    platform: Optional[str] = None


@dataclass(repr=False)
class Reduction(Header):
    """A description of the reduction that has been performed."""
    software: Union[Software, str]
    timestamp: Optional[datetime.datetime] = field(
        default=None,
        metadata={
            "description": "Timestamp string, formatted as ISO 8601 datetime"
        })
    creator: Optional[Person] = None
    corrections: Optional[List[str]] = None
    computer: Optional[str] = field(
        default=None, metadata={'description': 'Computer used for reduction'})
    call: Optional[str] = field(
        default=None, metadata={'description': 'The command line call used'})
    script: Optional[str] = field(
        default=None,
        metadata={'description': 'Path to reduction script or notebook'})
    binary: Optional[str] = field(
        default=None,
        metadata={'description': 'Path to full information file'})

    __repr__ = Header._staggered_repr
